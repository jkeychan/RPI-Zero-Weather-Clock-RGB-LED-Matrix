#include <curl/curl.h>
#include <getopt.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <csignal>
#include <fstream>
#include <mutex>
#include <sstream>
#include <thread>

#include "graphics.h"
#include "led-matrix.h"
#include "logger.hh"
#include "simple_json.hh"

using rgb_matrix::Canvas;
using rgb_matrix::Color;
using rgb_matrix::Font;
using rgb_matrix::FrameCanvas;
using rgb_matrix::RGBMatrix;

struct AppConfig
{
    std::string api_key;
    std::string zip_code;
    int time_format = 24;
    char temp_unit = 'F';
    int text_cycle_interval = 10;
    bool auto_brightness = true;
    int brightness = 20;
    int manual_brightness = 50;
    int min_brightness = 20;
    int max_brightness = 60;
    int frame_interval_ms = 60;
    int brightness_update_seconds = 10;
    int dynamic_color_interval_seconds = 1;
    bool langtons_ant = false;
    std::string font_path = "fonts/5x7.bdf";
    std::string log_level = "INFO";
    std::string ntp_server = "pool.ntp.org";  // handled by systemd-timesyncd
};

struct WeatherState
{
    std::atomic<int> temperature{0};
    std::atomic<int> temperature_c{0};
    std::atomic<int> feels_like{0};
    std::atomic<int> feels_like_c{0};
    std::atomic<int> humidity{0};
    std::string main_weather;
    std::string description;
    std::atomic<long> sunrise{0};
    std::atomic<long> sunset{0};
    std::mutex mu;
};

static volatile bool interrupt_received = false;
static void InterruptHandler(int signo)
{
    interrupt_received = true;
    (void)signo;
}

static std::mutex weather_ready_mutex;
static std::condition_variable weather_ready_cv;
static bool weather_fetched = false;

static int SafeInt(const std::string& v, int fallback) noexcept
{
    try
    {
        return std::stoi(v);
    }
    catch (...)
    {
        return fallback;
    }
}

static size_t CurlWrite(void* contents, size_t size, size_t nmemb, void* userp)
{
    if (nmemb != 0 && size > SIZE_MAX / nmemb)
        return 0;  // overflow would occur — signal error to libcurl
    size_t total = size * nmemb;
    std::string* s = static_cast<std::string*>(userp);
    s->append(static_cast<char*>(contents), total);
    return total;
}

bool LoadConfig(const std::string& path, AppConfig& cfg)
{
    std::ifstream in(path);
    if (!in)
        return false;
    std::string line;
    std::string section;
    auto trim = [](std::string s)
    {
        size_t a = s.find_first_not_of(" \t\r\n");
        size_t b = s.find_last_not_of(" \t\r\n");
        if (a == std::string::npos)
            return std::string();
        return s.substr(a, b - a + 1);
    };
    while (std::getline(in, line))
    {
        line = trim(line);
        if (line.empty() || line[0] == '#' || line[0] == ';')
            continue;
        if (line.front() == '[' && line.back() == ']')
        {
            section = line.substr(1, line.size() - 2);
            continue;
        }
        auto pos = line.find('=');
        if (pos == std::string::npos)
            continue;
        std::string key = trim(line.substr(0, pos));
        std::string val = trim(line.substr(pos + 1));
        if (section == "Weather")
        {
            if (key == "api_key")
                cfg.api_key = val;
            else if (key == "zip_code")
                cfg.zip_code = val;
        }
        else if (section == "Display")
        {
            if (key == "time_format")
                cfg.time_format = SafeInt(val, 24);
            else if (key == "temp_unit")
                cfg.temp_unit = val.empty() ? 'F' : static_cast<char>(toupper(val[0]));
            else if (key == "text_cycle_interval")
                cfg.text_cycle_interval = SafeInt(val, 10);
            else if (key == "AUTO_BRIGHTNESS_ADJUST")
                cfg.auto_brightness = (val == "true" || val == "True" || val == "1");
            else if (key == "BRIGHTNESS")
                cfg.brightness = SafeInt(val, 20);
            else if (key == "MANUAL_BRIGHTNESS")
                cfg.manual_brightness = SafeInt(val, 50);
            else if (key == "MIN_BRIGHTNESS")
                cfg.min_brightness = SafeInt(val, 20);
            else if (key == "MAX_BRIGHTNESS")
                cfg.max_brightness = SafeInt(val, 60);
            else if (key == "FRAME_INTERVAL_MS")
                cfg.frame_interval_ms = SafeInt(val, 60);
            else if (key == "BRIGHTNESS_UPDATE_SECONDS")
                cfg.brightness_update_seconds = SafeInt(val, 10);
            else if (key == "DYNAMIC_COLOR_INTERVAL_SECONDS")
                cfg.dynamic_color_interval_seconds = SafeInt(val, 1);
            else if (key == "LANGTONS_ANT_ENABLED")
                cfg.langtons_ant = (val == "true" || val == "True" || val == "1");
            else if (key == "FONT_PATH")
                cfg.font_path = val;
            else if (key == "LOG_LEVEL")
                cfg.log_level = val;
        }
        else if (section == "NTP")
        {
            if (key == "preferred_server")
                cfg.ntp_server = val;
        }
    }
    return true;
}

void WeatherThread(const AppConfig& cfg, WeatherState& state)
{
    CURL* curl = curl_easy_init();
    if (!curl)
        return;
    std::string url = "https://api.openweathermap.org/data/2.5/weather?zip=" + cfg.zip_code +
                      "&appid=" + cfg.api_key + "&units=metric";
    std::string buffer;
    long backoff = 5;
    const long max_backoff = 300;
    const int interval = 600;
    while (!interrupt_received)
    {
        buffer.clear();
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, CurlWrite);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);
        CURLcode res = curl_easy_perform(curl);
        if (res == CURLE_OK)
        {
            auto temp = json_number(buffer, "temp");
            auto feels = json_number(buffer, "feels_like");
            auto hum = json_number(buffer, "humidity");
            auto sr = json_number(buffer, "sunrise");
            auto ss = json_number(buffer, "sunset");
            auto mainw = json_array0_string(buffer, "weather", "main");
            auto desc = json_array0_string(buffer, "weather", "description");
            if (temp && feels && hum && sr && ss && mainw && desc)
            {
                int t_c = static_cast<int>(std::lround(*temp));
                int f_c = static_cast<int>(std::lround(*feels));
                int t = t_c;
                int f = f_c;
                if (cfg.temp_unit == 'F')
                {
                    t = static_cast<int>(std::lround((t * 9.0 / 5.0) + 32));
                    f = static_cast<int>(std::lround((f * 9.0 / 5.0) + 32));
                }
                std::lock_guard<std::mutex> lk(state.mu);
                state.temperature = t;
                state.temperature_c = t_c;
                state.feels_like = f;
                state.feels_like_c = f_c;
                state.humidity = static_cast<int>(std::lround(*hum));
                state.sunrise = static_cast<long>(*sr);
                state.sunset = static_cast<long>(*ss);
                state.main_weather = *mainw;
                state.description = *desc;
                backoff = 5;

                // Signal first-fetch wait in main()
                {
                    std::lock_guard<std::mutex> lk(weather_ready_mutex);
                    weather_fetched = true;
                }
                weather_ready_cv.notify_one();
            }
            // Sleep in 1s chunks so SIGTERM wakes us within 1 second
            for (int i = 0; i < interval && !interrupt_received; ++i)
                std::this_thread::sleep_for(std::chrono::seconds(1));
        }
        else
        {
            for (long i = 0; i < backoff && !interrupt_received; ++i)
                std::this_thread::sleep_for(std::chrono::seconds(1));
            backoff = std::min(max_backoff, backoff * 2);
        }
    }
    curl_easy_cleanup(curl);
}

// Maps Celsius [-40, 50] to a smooth HSV color: blue=cold, red=hot.
static Color TempColor(int tempCelsius)
{
    const double t_min = -40.0;
    const double t_max = 50.0;
    double t = std::max(t_min, std::min(t_max, static_cast<double>(tempCelsius)));
    double frac = (t - t_min) / (t_max - t_min);  // 0..1
    double hue = 240.0 * (1.0 - frac);            // 240° (blue) → 0° (red)

    // HSV → RGB with S=1, V=1
    double h = hue / 60.0;
    int i = static_cast<int>(h) % 6;
    double f = h - static_cast<double>(static_cast<int>(h));
    double q = 1.0 - f;
    double u = f;

    double r, g, b;
    switch (i)
    {
        case 0:
            r = 1;
            g = u;
            b = 0;
            break;
        case 1:
            r = q;
            g = 1;
            b = 0;
            break;
        case 2:
            r = 0;
            g = 1;
            b = u;
            break;
        case 3:
            r = 0;
            g = q;
            b = 1;
            break;
        case 4:
            r = u;
            g = 0;
            b = 1;
            break;
        default:
            r = 1;
            g = 0;
            b = q;
            break;
    }
    return Color(static_cast<int>(r * 255), static_cast<int>(g * 255), static_cast<int>(b * 255));
}

static Color HumidityColor(int humidity)
{
    if (humidity < 30)
        return Color(0, 0, 255);
    if (humidity < 60)
        return Color(0, 255, 0);
    return Color(255, 69, 0);
}

static Color DynamicRainbowColor(int seconds_period)
{
    using namespace std::chrono;
    auto now = steady_clock::now().time_since_epoch();
    double t = std::fmod(duration_cast<milliseconds>(now).count() / 1000.0,
                         static_cast<double>(seconds_period)) /
               seconds_period;
    int i = static_cast<int>(t * 6);
    double f = t * 6 - i;
    double q = 1.0 - f;
    double u = f;
    double r, g, b;
    switch (i % 6)
    {
        case 0:
            r = 1;
            g = u;
            b = 0;
            break;
        case 1:
            r = q;
            g = 1;
            b = 0;
            break;
        case 2:
            r = 0;
            g = 1;
            b = u;
            break;
        case 3:
            r = 0;
            g = q;
            b = 1;
            break;
        case 4:
            r = u;
            g = 0;
            b = 1;
            break;
        default:
            r = 1;
            g = 0;
            b = q;
            break;
    }
    return Color(static_cast<int>(r * 255), static_cast<int>(g * 255), static_cast<int>(b * 255));
}

// Sun: filled disc + 8 cardinal/diagonal rays
static void DrawSun(Canvas* c, int x, int y)
{
    const Color kYellow(255, 200, 0);
    const int cx = x + 7;
    const int cy = y + 7;
    rgb_matrix::DrawCircle(c, cx, cy, 3, kYellow);
    // fill interior pixels that DrawCircle leaves empty
    for (int dy = -2; dy <= 2; ++dy)
    {
        for (int dx = -2; dx <= 2; ++dx)
        {
            c->SetPixel(cx + dx, cy + dy, kYellow.r, kYellow.g, kYellow.b);
        }
    }
    // 8 rays: cardinal + diagonal
    rgb_matrix::DrawLine(c, cx, cy - 4, cx, cy - 6, kYellow);          // N
    rgb_matrix::DrawLine(c, cx, cy + 4, cx, cy + 6, kYellow);          // S
    rgb_matrix::DrawLine(c, cx - 4, cy, cx - 6, cy, kYellow);          // W
    rgb_matrix::DrawLine(c, cx + 4, cy, cx + 6, cy, kYellow);          // E
    rgb_matrix::DrawLine(c, cx - 3, cy - 3, cx - 5, cy - 5, kYellow);  // NW
    rgb_matrix::DrawLine(c, cx + 3, cy - 3, cx + 5, cy - 5, kYellow);  // NE
    rgb_matrix::DrawLine(c, cx - 3, cy + 3, cx - 5, cy + 5, kYellow);  // SW
    rgb_matrix::DrawLine(c, cx + 3, cy + 3, cx + 5, cy + 5, kYellow);  // SE
}

// Cloud: two overlapping circles with bottom line to fill the base
static void DrawCloud(Canvas* c, int x, int y)
{
    const Color kWhite(200, 200, 200);
    rgb_matrix::DrawCircle(c, x + 5, y + 7, 3, kWhite);
    rgb_matrix::DrawCircle(c, x + 9, y + 6, 4, kWhite);
    // fill interiors
    for (int dy = -2; dy <= 2; ++dy)
    {
        for (int dx = -2; dx <= 2; ++dx)
        {
            c->SetPixel(x + 5 + dx, y + 7 + dy, kWhite.r, kWhite.g, kWhite.b);
        }
    }
    for (int dy = -3; dy <= 3; ++dy)
    {
        for (int dx = -3; dx <= 3; ++dx)
        {
            c->SetPixel(x + 9 + dx, y + 6 + dy, kWhite.r, kWhite.g, kWhite.b);
        }
    }
    // flat base (x+13 max = 63 at call site x=50, stays on-screen)
    rgb_matrix::DrawLine(c, x + 2, y + 10, x + 12, y + 10, kWhite);
    rgb_matrix::DrawLine(c, x + 2, y + 11, x + 12, y + 11, kWhite);
}

static void DrawRain(Canvas* c, int x, int y)
{
    DrawCloud(c, x, y);
    const Color kBlue(80, 140, 255);
    rgb_matrix::DrawLine(c, x + 3, y + 13, x + 2, y + 15, kBlue);
    rgb_matrix::DrawLine(c, x + 7, y + 13, x + 6, y + 15, kBlue);
    rgb_matrix::DrawLine(c, x + 11, y + 13, x + 10, y + 15, kBlue);
}

static void DrawSnow(Canvas* c, int x, int y)
{
    DrawCloud(c, x, y);
    const Color kIce(173, 216, 230);
    const int cx = x + 7;
    const int cy = y + 14;
    rgb_matrix::DrawLine(c, cx, cy - 2, cx, cy + 2, kIce);          // vertical
    rgb_matrix::DrawLine(c, cx - 2, cy, cx + 2, cy, kIce);          // horizontal
    rgb_matrix::DrawLine(c, cx - 1, cy - 1, cx + 1, cy + 1, kIce);  // diagonal NW-SE
    rgb_matrix::DrawLine(c, cx - 1, cy + 1, cx + 1, cy - 1, kIce);  // diagonal SW-NE
}

static void DrawThunder(Canvas* c, int x, int y)
{
    DrawCloud(c, x, y);
    const Color kYellow(255, 220, 0);
    // forked lightning bolt — stays within y+15 to match other icons
    rgb_matrix::DrawLine(c, x + 9, y + 12, x + 7, y + 15, kYellow);
    rgb_matrix::DrawLine(c, x + 7, y + 14, x + 10, y + 14, kYellow);
    rgb_matrix::DrawLine(c, x + 10, y + 13, x + 8, y + 15, kYellow);
}

static void DrawFog(Canvas* c, int x, int y)
{
    const Color kGray(160, 160, 160);
    for (int row : {5, 8, 11, 14})
    {
        rgb_matrix::DrawLine(c, x + 1, y + row, x + 13, y + row, kGray);
    }
}

static void DrawWeatherIcon(Canvas* c, const std::string& w, int x, int y)
{
    if (w == "Clear")
        DrawSun(c, x, y);
    else if (w == "Clouds")
        DrawCloud(c, x, y);
    else if (w == "Rain" || w == "Drizzle")
        DrawRain(c, x, y);
    else if (w == "Snow")
        DrawSnow(c, x, y);
    else if (w == "Thunderstorm")
        DrawThunder(c, x, y);
    else
        DrawFog(c, x, y);  // Fog, Mist, Haze, Smoke, Dust, Sand, Ash, Squall, Tornado
}

int main(int argc, char** argv)
{
    signal(SIGTERM, InterruptHandler);
    signal(SIGINT, InterruptHandler);

    // Parse standard LED matrix flags (--led-* args from command line)
    rgb_matrix::RGBMatrix::Options options;
    rgb_matrix::RuntimeOptions runtime;
    if (!rgb_matrix::ParseOptionsFromFlags(&argc, &argv, &options, &runtime))
    {
        fprintf(stderr, "Invalid LED options.\n");
        return 1;
    }

    // Matrix settings for Pi Zero W + Adafruit Bonnet — hardcoded, not flag-overridable
    options.hardware_mapping = "adafruit-hat";
    options.rows = 32;
    options.cols = 64;
    options.pwm_bits = 6;   // ≤5 causes blank display on Pi Zero W adafruit-hat; 6 reduces shimmer
    options.led_rgb_sequence = "RGB";
    options.disable_hardware_pulsing = true;  // required for Adafruit HAT/Bonnet
    options.limit_refresh_rate_hz = 100;      // cap refresh to reduce shimmer
    runtime.gpio_slowdown = 3;                // Pi Zero W timing margin without excess CPU
    runtime.drop_privileges = 1;

    AppConfig cfg;
    LoadConfig("config.ini", cfg);

    Logger logger("/var/log/rgb/weather_clock.log", Logger::ParseLevel(cfg.log_level));
    logger.Info("rgb_display starting");

    RGBMatrix* matrix = rgb_matrix::CreateMatrixFromOptions(options, runtime);
    if (matrix == nullptr)
    {
        logger.Error("Failed to create RGB matrix");
        return 1;
    }
    FrameCanvas* offscreen = matrix->CreateFrameCanvas();

    logger.Info("Matrix initialized: " + std::to_string(options.cols) + "x" +
                std::to_string(options.rows) +
                " slowdown=" + std::to_string(runtime.gpio_slowdown));

    Font font;
    if (!font.LoadFont(cfg.font_path.c_str()))
    {
        logger.Warning("Failed to load font: " + cfg.font_path);
    }

    WeatherState weather;
    std::thread wt(WeatherThread, std::ref(cfg), std::ref(weather));

    // Wait up to 15s for the first weather fetch before starting the display loop
    {
        std::unique_lock<std::mutex> lk(weather_ready_mutex);
        bool ok =
            weather_ready_cv.wait_for(lk, std::chrono::seconds(15), [] { return weather_fetched; });
        if (!ok)
            logger.Warning("Weather fetch timed out — starting with defaults");
    }

    matrix->SetBrightness(cfg.auto_brightness ? cfg.brightness : cfg.manual_brightness);

    bool show_main_weather = true;
    time_t last_switch = time(nullptr);
    int scroll_x = offscreen->width();

    auto start_tp = std::chrono::steady_clock::now();
    auto to_seconds = [](auto tp)
    { return std::chrono::duration_cast<std::chrono::seconds>(tp).count(); };
    long last_brightness = 0;

    while (!interrupt_received)
    {
        offscreen->Clear();

        auto now_tp = std::chrono::steady_clock::now();
        long now_s = to_seconds(now_tp - start_tp);

        // Auto brightness: smooth solar interpolation between min and max
        if (cfg.auto_brightness && (now_s - last_brightness >= cfg.brightness_update_seconds))
        {
            long sr = weather.sunrise.load();
            long ss = weather.sunset.load();
            auto now_local = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
            int b = cfg.min_brightness;
            if (sr > 0 && ss > 0 && now_local >= sr && now_local <= ss)
            {
                double solar_noon = (static_cast<double>(sr) + static_cast<double>(ss)) / 2.0;
                double frac = (static_cast<double>(now_local) <= solar_noon)
                                  ? (static_cast<double>(now_local - sr)) /
                                        (solar_noon - static_cast<double>(sr))
                                  : (static_cast<double>(ss - now_local)) /
                                        (static_cast<double>(ss) - solar_noon);
                frac = std::max(0.0, std::min(1.0, frac));
                b = cfg.min_brightness +
                    static_cast<int>(frac * (cfg.max_brightness - cfg.min_brightness));
            }
            matrix->SetBrightness(b);
            last_brightness = now_s;
        }

        // Dynamic rainbow: full cycle in 30 s, updated every frame
        Color dynamic = DynamicRainbowColor(30);

        // Copy weather state under lock
        int tF = 0, fF = 0, hum = 0, tC = 0;
        std::string mainw, desc;
        {
            std::lock_guard<std::mutex> lk(weather.mu);
            tF = weather.temperature.load();
            tC = weather.temperature_c.load();
            fF = weather.feels_like.load();
            hum = weather.humidity.load();
            mainw = weather.main_weather;
            desc = weather.description;
        }

        // Time display (thread-safe localtime_r)
        time_t now = time(nullptr);
        struct tm tm_buf = {};
        localtime_r(&now, &tm_buf);
        char timebuf[16];
        if (strftime(timebuf, sizeof(timebuf), cfg.time_format == 12 ? "%I:%M" : "%H:%M", &tm_buf) >
            0)
            if (timebuf[0] == '0')
                timebuf[0] = ' ';

        char daybuf[16];
        strftime(daybuf, sizeof(daybuf), "%a", &tm_buf);

        std::string temp_str = std::to_string(tF) + (cfg.temp_unit == 'F' ? "F" : "C");
        std::string feels_str = std::to_string(fF) + "|";
        std::string humid_str = std::to_string(hum) + "%";

        rgb_matrix::DrawText(offscreen, font, 2, 10, dynamic, daybuf);
        rgb_matrix::DrawText(offscreen, font, 34, 10, dynamic, timebuf);
        rgb_matrix::DrawText(offscreen, font, 2, 20, TempColor(tC), temp_str.c_str());
        rgb_matrix::DrawText(offscreen, font, 33, 20, TempColor(tC), feels_str.c_str());
        rgb_matrix::DrawText(offscreen, font, 49, 20, HumidityColor(hum), humid_str.c_str());

        const std::string& weather_text = show_main_weather ? mainw : desc;
        int est = static_cast<int>(weather_text.size()) * 6;
        if (!show_main_weather && !weather_text.empty() && est > offscreen->width())
        {
            rgb_matrix::DrawText(offscreen, font, scroll_x, 30, Color(255, 255, 255),
                                 weather_text.c_str());
            // scroll_x + est: est > 0 guaranteed by the empty check above, so no
            // signed overflow — scroll_x resets before it can reach INT_MIN
            if (scroll_x + est < 0)
                scroll_x = offscreen->width();
            else
                --scroll_x;
        }
        else
        {
            rgb_matrix::DrawText(offscreen, font, 2, 30, Color(255, 255, 255),
                                 weather_text.c_str());
            scroll_x = offscreen->width();
        }

        DrawWeatherIcon(offscreen, mainw, 50, 20);  // matches Python ICON_POSITION_X/Y

        offscreen = matrix->SwapOnVSync(offscreen);

        if (difftime(time(nullptr), last_switch) >= cfg.text_cycle_interval)
        {
            show_main_weather = !show_main_weather;
            last_switch = time(nullptr);
            scroll_x = offscreen->width();
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(std::max(20, cfg.frame_interval_ms)));
    }

    delete matrix;
    wt.join();
    return 0;
}
