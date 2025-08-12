#include "led-matrix.h"
#include "graphics.h"
#include <curl/curl.h>
#include <unistd.h>
#include <getopt.h>
#include <thread>
#include <atomic>
#include <mutex>
#include <chrono>
#include <csignal>
#include <fstream>
#include <sstream>
#include <map>
#include "simple_json.hh"
#include <cmath>

using rgb_matrix::RGBMatrix;
using rgb_matrix::FrameCanvas;
using rgb_matrix::Canvas;
using rgb_matrix::Color;
using rgb_matrix::Font;

struct AppConfig {
  std::string api_key;
  std::string zip_code;
  int time_format = 24;
  char temp_unit = 'F';
  int text_cycle_interval = 10;
  bool auto_brightness = true;
  int manual_brightness = 50;
  int min_brightness = 20;
  int max_brightness = 60;
  int frame_interval_ms = 60;
  int brightness_update_seconds = 10;
  int dynamic_color_interval_seconds = 1;
  bool langtons_ant = true;
};

struct WeatherState {
  std::atomic<int> temperature{0};
  std::atomic<int> feels_like{0};
  std::atomic<int> humidity{0};
  std::string main_weather;
  std::string description;
  std::atomic<long> sunrise{0};
  std::atomic<long> sunset{0};
  std::mutex mu;
};

static volatile bool interrupt_received = false;
static void InterruptHandler(int signo) { interrupt_received = true; }

static size_t CurlWrite(void *contents, size_t size, size_t nmemb, void *userp) {
  size_t total = size * nmemb;
  std::string *s = static_cast<std::string*>(userp);
  s->append(static_cast<char*>(contents), total);
  return total;
}

bool LoadConfig(const std::string &path, AppConfig &cfg) {
  std::ifstream in(path);
  if (!in) return false;
  std::string line; std::string section;
  auto trim = [](std::string s){
    size_t a = s.find_first_not_of(" \t\r\n");
    size_t b = s.find_last_not_of(" \t\r\n");
    if (a==std::string::npos) return std::string();
    return s.substr(a, b-a+1);
  };
  while (std::getline(in, line)) {
    line = trim(line);
    if (line.empty() || line[0]=='#' || line[0]==';') continue;
    if (line.front()=='[' && line.back()==']') { section = line.substr(1, line.size()-2); continue; }
    auto pos = line.find('='); if (pos==std::string::npos) continue;
    std::string key = trim(line.substr(0,pos));
    std::string val = trim(line.substr(pos+1));
    if (section=="Weather") {
      if (key=="api_key") cfg.api_key = val;
      else if (key=="zip_code") cfg.zip_code = val;
    } else if (section=="Display") {
      if (key=="time_format") cfg.time_format = std::stoi(val);
      else if (key=="temp_unit") cfg.temp_unit = val.empty()? 'F' : (char)toupper(val[0]);
      else if (key=="text_cycle_interval") cfg.text_cycle_interval = std::stoi(val);
      else if (key=="AUTO_BRIGHTNESS_ADJUST") cfg.auto_brightness = (val=="true"||val=="True"||val=="1");
      else if (key=="MANUAL_BRIGHTNESS") cfg.manual_brightness = std::stoi(val);
      else if (key=="MIN_BRIGHTNESS") cfg.min_brightness = std::stoi(val);
      else if (key=="MAX_BRIGHTNESS") cfg.max_brightness = std::stoi(val);
      else if (key=="FRAME_INTERVAL_MS") cfg.frame_interval_ms = std::stoi(val);
      else if (key=="BRIGHTNESS_UPDATE_SECONDS") cfg.brightness_update_seconds = std::stoi(val);
      else if (key=="DYNAMIC_COLOR_INTERVAL_SECONDS") cfg.dynamic_color_interval_seconds = std::stoi(val);
      else if (key=="LANGTONS_ANT_ENABLED") cfg.langtons_ant = (val=="true"||val=="True"||val=="1");
    }
  }
  return true;
}

void WeatherThread(const AppConfig &cfg, WeatherState &state) {
  CURL *curl = curl_easy_init();
  if (!curl) return;
  std::string endpoint = "https://api.openweathermap.org/data/2.5/weather";
  std::string url = endpoint + "?zip=" + cfg.zip_code + "&appid=" + cfg.api_key + "&units=metric";
  std::string buffer;
  long backoff = 5; long max_backoff = 300; int interval = 600;
  while (!interrupt_received) {
    buffer.clear();
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, CurlWrite);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);
    CURLcode res = curl_easy_perform(curl);
    if (res == CURLE_OK) {
      auto temp = json_number(buffer, "temp");
      auto feels = json_number(buffer, "feels_like");
      auto hum = json_number(buffer, "humidity");
      auto sr = json_number(buffer, "sunrise");
      auto ss = json_number(buffer, "sunset");
      auto mainw = json_array0_string(buffer, "weather", "main");
      auto desc = json_array0_string(buffer, "weather", "description");
      if (temp && feels && hum && sr && ss && mainw && desc) {
        int t = (int)std::lround(*temp);
        int f = (int)std::lround(*feels);
        int h = (int)std::lround(*hum);
        if (cfg.temp_unit=='F') {
          t = (int)std::lround((t*9.0/5.0)+32);
          f = (int)std::lround((f*9.0/5.0)+32);
        }
        std::lock_guard<std::mutex> lk(state.mu);
        state.temperature = t; state.feels_like = f; state.humidity = h;
        state.sunrise = (long)*sr; state.sunset = (long)*ss;
        state.main_weather = *mainw; state.description = *desc;
        backoff = 5; // reset
      }
      std::this_thread::sleep_for(std::chrono::seconds(interval));
    } else {
      std::this_thread::sleep_for(std::chrono::seconds(backoff));
      backoff = std::min(max_backoff, backoff*2);
    }
  }
  curl_easy_cleanup(curl);
}

static Color TempColor(int tempF) {
  if (tempF <= 0) return Color(0,0,255);
  if (tempF >= 100) return Color(255,0,0);
  // simple gradient blue->cyan->yellow->red
  if (tempF <= 50) {
    double f = (tempF - 0)/50.0; // 0..1
    int r=0, g=(int)(255*f), b=255;
    return Color(r,g,b);
  } else if (tempF <= 75) {
    double f = (tempF - 50)/25.0;
    int r=(int)(255*f), g=255, b=(int)(255*(1.0-f));
    return Color(r,g,b);
  } else {
    double f = (tempF - 75)/25.0;
    int r=255, g=(int)(255*(1.0-f)), b=0;
    return Color(r,g,b);
  }
}

static Color HumidityColor(int humidity) {
  if (humidity < 30) return Color(0,0,255);
  if (humidity < 60) return Color(0,255,0);
  return Color(255,69,0);
}

static Color DynamicRainbowColor(int seconds_period) {
  using namespace std::chrono;
  auto now = steady_clock::now().time_since_epoch();
  double t = std::fmod(duration_cast<milliseconds>(now).count()/1000.0, (double)seconds_period) / seconds_period;
  double h = t; double s=1.0, v=1.0;
  double r,g,b;
  int i = int(h*6);
  double f = h*6 - i;
  double p = v*(1-s); double q=v*(1-f*s); double u=v*(1-(1-f)*s);
  switch(i%6){
    case 0: r=v; g=u; b=p; break;
    case 1: r=q; g=v; b=p; break;
    case 2: r=p; g=v; b=u; break;
    case 3: r=p; g=q; b=v; break;
    case 4: r=u; g=p; b=v; break;
    default: r=v; g=p; b=q; break;
  }
  return Color((int)(r*255),(int)(g*255),(int)(b*255));
}

static void DrawSun(Canvas *c, int x, int y) {
  // minimal icon
  rgb_matrix::DrawCircle(c, x+7, y+7, 3, Color(255,255,0));
}
static void DrawCloud(Canvas *c, int x, int y) {
  rgb_matrix::DrawCircle(c, x+4, y+8, 3, Color(255,255,255));
  rgb_matrix::DrawCircle(c, x+8, y+8, 4, Color(255,255,255));
}
static void DrawRain(Canvas *c, int x, int y) {
  DrawCloud(c, x, y);
  rgb_matrix::DrawLine(c, x+4, y+12, x+3, y+14, Color(100,170,255));
  rgb_matrix::DrawLine(c, x+9, y+12, x+8, y+14, Color(100,170,255));
}
static void DrawSnow(Canvas *c, int x, int y) {
  DrawCloud(c, x, y);
  rgb_matrix::DrawLine(c, x+6, y+12, x+6, y+14, Color(173,216,230));
  rgb_matrix::DrawLine(c, x+5, y+13, x+7, y+13, Color(173,216,230));
}
static void DrawThunder(Canvas *c, int x, int y) {
  DrawCloud(c, x, y);
  rgb_matrix::DrawLine(c, x+8, y+10, x+7, y+12, Color(255,255,0));
  rgb_matrix::DrawLine(c, x+7, y+12, x+9, y+14, Color(255,255,0));
}
static void DrawFog(Canvas *c, int x, int y) {
  rgb_matrix::DrawLine(c, x, y+8, x+14, y+8, Color(220,220,220));
  rgb_matrix::DrawLine(c, x, y+10, x+14, y+10, Color(220,220,220));
}

static void DrawWeatherIcon(Canvas *c, const std::string &w, int x, int y){
  if (w=="Clear") DrawSun(c,x,y);
  else if (w=="Clouds") DrawCloud(c,x,y);
  else if (w=="Rain") DrawRain(c,x,y);
  else if (w=="Snow") DrawSnow(c,x,y);
  else if (w=="Thunderstorm") DrawThunder(c,x,y);
  else if (w=="Fog"||w=="Mist"||w=="Haze") DrawFog(c,x,y);
}

int main(int argc, char **argv) {
  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  // Parse standard LED matrix flags so hardware mapping like --led-gpio-mapping works.
  rgb_matrix::RGBMatrix::Options options;
  rgb_matrix::RuntimeOptions runtime;
  if (!rgb_matrix::ParseOptionsFromFlags(&argc, &argv, &options, &runtime)) {
    fprintf(stderr, "Invalid LED options.\n");
    return 1;
  }
  // Sensible defaults for Pi Zero W if not provided via flags
  if (options.gpio_slowdown == 0) options.gpio_slowdown = 4;

  AppConfig cfg;
  LoadConfig("TEST/test-config.ini", cfg);

  RGBMatrix *matrix = rgb_matrix::CreateMatrixFromOptions(options, runtime);
  if (matrix == nullptr) return 1;
  FrameCanvas *offscreen = matrix->CreateFrameCanvas();

  // Diagnostic: print resolved options
  fprintf(stderr, "Matrix initialized: %dx%d chain=%d parallel=%d slowdown=%d mapping=%s\n",
          options.cols, options.rows, options.chain_length, options.parallel,
          options.gpio_slowdown, options.hardware_mapping ? options.hardware_mapping : "(default)");

  // Quick test pattern for 2 seconds to confirm panel output
  {
    auto t_end = std::chrono::steady_clock::now() + std::chrono::seconds(2);
    int w = offscreen->width();
    int h = offscreen->height();
    while (std::chrono::steady_clock::now() < t_end) {
      offscreen->Fill(0, 0, 0);
      // Color bars
      for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
          if (x < w/3) offscreen->SetPixel(x, y, 255, 0, 0);
          else if (x < 2*w/3) offscreen->SetPixel(x, y, 0, 255, 0);
          else offscreen->SetPixel(x, y, 0, 0, 255);
        }
      }
      offscreen = matrix->SwapOnVSync(offscreen);
      usleep(20000);
    }
  }

  Font font;
  if (!font.LoadFont("../fonts/5x7.bdf")) {
    // Fallback if running from repo root
    font.LoadFont("fonts/5x7.bdf");
  }

  WeatherState weather;
  std::thread t(WeatherThread, std::ref(cfg), std::ref(weather));
  t.detach();

  matrix->SetBrightness(cfg.manual_brightness);

  bool show_main_weather = true; double last_switch = 0;
  int scroll_x = offscreen->width();

  auto start = std::chrono::steady_clock::now();
  auto to_seconds = [](auto tp){return std::chrono::duration_cast<std::chrono::seconds>(tp).count();};
  long last_brightness = 0; long last_color = 0;
  Color dynamic = DynamicRainbowColor(cfg.dynamic_color_interval_seconds);

  while (!interrupt_received) {
    offscreen->Clear();

    auto now_tp = std::chrono::steady_clock::now();
    long now_s = to_seconds(now_tp - start);

    // brightness throttle
    if (cfg.auto_brightness && (now_s - last_brightness >= cfg.brightness_update_seconds)) {
      long sr = weather.sunrise.load();
      long ss = weather.sunset.load();
      auto now_local = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
      // simple step: min before sunrise/after sunset; ramp linearly otherwise
      int b = cfg.min_brightness;
      if (sr>0 && ss>0) {
        if (now_local < sr || now_local > ss) b = cfg.min_brightness; else b = cfg.max_brightness;
      }
      matrix->SetBrightness(b);
      last_brightness = now_s;
    }

    // text colors
    if (now_s - last_color >= cfg.dynamic_color_interval_seconds) {
      dynamic = DynamicRainbowColor(cfg.dynamic_color_interval_seconds);
      last_color = now_s;
    }

    // copy state under lock
    int tF=0,fF=0,hum=0; std::string mainw="", desc="";
    {
      std::lock_guard<std::mutex> lk(weather.mu);
      tF = weather.temperature.load();
      fF = weather.feels_like.load();
      hum = weather.humidity.load();
      mainw = weather.main_weather; desc = weather.description;
    }

    time_t now = time(nullptr);
    struct tm *tm = localtime(&now);
    char timebuf[8];
    if (cfg.time_format==12) strftime(timebuf, sizeof(timebuf), "%I:%M", tm); else strftime(timebuf, sizeof(timebuf), "%H:%M", tm);
    if (timebuf[0]=='0') timebuf[0] = ' ';

    char daybuf[4];
    strftime(daybuf, sizeof(daybuf), "%a", tm);

    std::string temp = std::to_string(tF) + (cfg.temp_unit=='F'?"F":"C");
    std::string feels = std::to_string(fF) + "|";
    std::string humidity = std::to_string(hum) + "%";

    rgb_matrix::DrawText(offscreen, font, 2, 8, dynamic, daybuf);
    rgb_matrix::DrawText(offscreen, font, 34, 8, dynamic, timebuf);
    rgb_matrix::DrawText(offscreen, font, 2, 16, TempColor(tF), temp.c_str());
    rgb_matrix::DrawText(offscreen, font, 33, 16, TempColor(fF), feels.c_str());
    rgb_matrix::DrawText(offscreen, font, 49, 16, HumidityColor(hum), humidity.c_str());

    const std::string &weather_text = show_main_weather ? mainw : desc;
    int est = (int)weather_text.size()*6;
    if (!show_main_weather && est > offscreen->width()) {
      rgb_matrix::DrawText(offscreen, font, scroll_x, 24, Color(255,255,255), weather_text.c_str());
      if (scroll_x + est < 0) scroll_x = offscreen->width();
      else scroll_x -= 1;
    } else {
      rgb_matrix::DrawText(offscreen, font, 2, 24, Color(255,255,255), weather_text.c_str());
      scroll_x = offscreen->width();
    }

    // icon
    DrawWeatherIcon(offscreen, mainw, 50, 12);

    offscreen = matrix->SwapOnVSync(offscreen);

    // toggle text
    if (difftime(time(nullptr), last_switch) >= cfg.text_cycle_interval) {
      show_main_weather = !show_main_weather; last_switch = time(nullptr); scroll_x = offscreen->width();
    }

    usleep(std::max(20, cfg.frame_interval_ms) * 1000);
  }

  delete matrix;
  return 0;
}


