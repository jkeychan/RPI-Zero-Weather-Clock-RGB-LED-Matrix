// Standalone icon-design preview: cycles candidate danger-bulb icons on the real
// matrix next to sample "feels like" text, so designs can be compared live without
// rebuilding/redeploying weather_clock.cc for every tweak. Not part of the main binary.
#include <unistd.h>

#include <chrono>
#include <csignal>
#include <string>
#include <thread>
#include <vector>

#include "graphics.h"
#include "led-matrix.h"

using rgb_matrix::Canvas;
using rgb_matrix::Color;
using rgb_matrix::Font;

static volatile bool interrupt_received = false;
static void InterruptHandler(int) { interrupt_received = true; }

// Candidate 1: 3x5 flat-yellow bulb — rounded glass, tapered neck, base.
static void DrawBulb1(Canvas* c, int x, int y)
{
    const Color k(255, 200, 0);
    c->SetPixel(x + 1, y, k.r, k.g, k.b);
    for (int dx = 0; dx <= 2; ++dx) c->SetPixel(x + dx, y + 1, k.r, k.g, k.b);
    for (int dx = 0; dx <= 2; ++dx) c->SetPixel(x + dx, y + 2, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 3, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 4, k.r, k.g, k.b);
}

// Candidate 2: 4x6 rounder bulb with distinct screw-base line.
static void DrawBulb2(Canvas* c, int x, int y)
{
    const Color k(255, 200, 0);
    c->SetPixel(x + 1, y, k.r, k.g, k.b);
    c->SetPixel(x + 2, y, k.r, k.g, k.b);
    for (int dx = 0; dx <= 3; ++dx) c->SetPixel(x + dx, y + 1, k.r, k.g, k.b);
    for (int dx = 0; dx <= 3; ++dx) c->SetPixel(x + dx, y + 2, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 3, k.r, k.g, k.b);
    c->SetPixel(x + 2, y + 3, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 4, k.r, k.g, k.b);
    c->SetPixel(x + 2, y + 4, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 5, k.r, k.g, k.b);
    c->SetPixel(x + 2, y + 5, k.r, k.g, k.b);
}

// Candidate 3: 3x5 with a bright-core/dim-halo "glow" instead of flat fill.
static void DrawBulb3(Canvas* c, int x, int y)
{
    const Color kDim(160, 110, 0);
    const Color kBright(255, 220, 40);
    c->SetPixel(x + 1, y, kDim.r, kDim.g, kDim.b);
    c->SetPixel(x, y + 1, kDim.r, kDim.g, kDim.b);
    c->SetPixel(x + 1, y + 1, kBright.r, kBright.g, kBright.b);
    c->SetPixel(x + 2, y + 1, kDim.r, kDim.g, kDim.b);
    c->SetPixel(x, y + 2, kDim.r, kDim.g, kDim.b);
    c->SetPixel(x + 1, y + 2, kBright.r, kBright.g, kBright.b);
    c->SetPixel(x + 2, y + 2, kDim.r, kDim.g, kDim.b);
    c->SetPixel(x + 1, y + 3, kDim.r, kDim.g, kDim.b);
    c->SetPixel(x + 1, y + 4, kDim.r, kDim.g, kDim.b);
}

// Candidate 4: 4x6 bulb with a tiny filament "X" for readability at a distance.
static void DrawBulb4(Canvas* c, int x, int y)
{
    const Color k(255, 200, 0);
    const Color kFil(120, 60, 0);
    c->SetPixel(x + 1, y, k.r, k.g, k.b);
    c->SetPixel(x + 2, y, k.r, k.g, k.b);
    for (int dx = 0; dx <= 3; ++dx) c->SetPixel(x + dx, y + 1, k.r, k.g, k.b);
    c->SetPixel(x, y + 2, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 2, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 2, y + 2, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 3, y + 2, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 3, k.r, k.g, k.b);
    c->SetPixel(x + 2, y + 3, k.r, k.g, k.b);
    c->SetPixel(x + 1, y + 4, k.r, k.g, k.b);
    c->SetPixel(x + 2, y + 4, k.r, k.g, k.b);
}

// Candidate 5: rounded yellow glass + dark screw-thread base (classic "idea bulb"
// silhouette) with a small highlight pixel for the glass shine.
static void DrawBulb5(Canvas* c, int x, int y)
{
    const Color kGlass(255, 200, 0);
    const Color kShine(255, 240, 140);
    const Color kBase(70, 70, 70);
    c->SetPixel(x + 1, y, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x, y + 1, kShine.r, kShine.g, kShine.b);
    for (int dx = 1; dx <= 3; ++dx) c->SetPixel(x + dx, y + 1, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 0; dx <= 3; ++dx) c->SetPixel(x + dx, y + 2, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 1, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 1, y + 4, kBase.r, kBase.g, kBase.b);
    c->SetPixel(x + 2, y + 4, kBase.r, kBase.g, kBase.b);
    c->SetPixel(x + 1, y + 5, kBase.r, kBase.g, kBase.b);
    c->SetPixel(x + 2, y + 5, kBase.r, kBase.g, kBase.b);
}

// Candidate 6: compact bulb with a visible "V" filament (like the reference photos),
// no outline — stays small so it doesn't crowd the humidity column. 5x7.
static void DrawBulb6(Canvas* c, int x, int y)
{
    const Color kGlass(255, 200, 0);
    const Color kFil(90, 50, 0);
    const Color kBase(70, 70, 70);
    for (int dx = 1; dx <= 3; ++dx) c->SetPixel(x + dx, y, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 0; dx <= 4; ++dx) c->SetPixel(x + dx, y + 1, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x, y + 2, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 1, y + 2, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 2, y + 2, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 3, y + 2, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 4, y + 2, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 1, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y + 3, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 3, y + 3, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 1; dx <= 3; ++dx) c->SetPixel(x + dx, y + 4, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 1; dx <= 3; ++dx) c->SetPixel(x + dx, y + 5, kBase.r, kBase.g, kBase.b);
    for (int dx = 1; dx <= 3; ++dx) c->SetPixel(x + dx, y + 6, kBase.r, kBase.g, kBase.b);
}

// Candidate 7: bigger, with a black outline + V filament, matching the reference
// images closely. Needs more room (7x9) so it will crowd the humidity column
// unless the layout reserves extra width for it.
static void DrawBulb7(Canvas* c, int x, int y)
{
    const Color kOutline(0, 0, 0);
    const Color kGlass(255, 200, 0);
    const Color kFil(90, 50, 0);
    const Color kBase(70, 70, 70);
    // Outline ring (rounded top, tapered sides) — drawn first, glass overwrites interior.
    int outline[][2] = {{2, 0}, {3, 0}, {4, 0}, {1, 1}, {5, 1}, {0, 2}, {6, 2},
                        {0, 3}, {6, 3}, {1, 4}, {5, 4}, {2, 5}, {4, 5}, {2, 6},
                        {4, 6}, {2, 7}, {4, 7}, {2, 8}, {4, 8}};
    for (auto& p : outline) c->SetPixel(x + p[0], y + p[1], kOutline.r, kOutline.g, kOutline.b);
    for (int dx = 2; dx <= 4; ++dx) c->SetPixel(x + dx, y, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 1; dx <= 5; ++dx) c->SetPixel(x + dx, y + 1, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 1; dx <= 5; ++dx) c->SetPixel(x + dx, y + 2, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 1, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y + 3, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 4, y + 3, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 5, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 1, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 3, y + 4, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 4, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 5, y + 4, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 3; dx <= 3; ++dx) c->SetPixel(x + dx, y + 5, kBase.r, kBase.g, kBase.b);
    for (int dx = 3; dx <= 3; ++dx) c->SetPixel(x + dx, y + 6, kBase.r, kBase.g, kBase.b);
    for (int dx = 3; dx <= 3; ++dx) c->SetPixel(x + dx, y + 7, kBase.r, kBase.g, kBase.b);
    c->SetPixel(x + 3, y + 8, kBase.r, kBase.g, kBase.b);
}

// Candidate 8: compact filament bulb (like 6) plus 5 short rays. Needs a 9x9
// bounding box — noticeably bigger than the ray-less candidates.
static void DrawBulb8(Canvas* c, int x, int y)
{
    const Color kGlass(255, 200, 0);
    const Color kFil(90, 50, 0);
    const Color kBase(70, 70, 70);
    c->SetPixel(x + 4, y + 0, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y + 1, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 6, y + 1, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 0, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 8, y + 3, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 3; dx <= 5; ++dx) c->SetPixel(x + dx, y + 2, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 2; dx <= 6; ++dx) c->SetPixel(x + dx, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 2, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 3, y + 4, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 4, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 5, y + 4, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 6, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 3, y + 5, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 4, y + 5, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 5, y + 5, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 3; dx <= 5; ++dx) c->SetPixel(x + dx, y + 6, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 3; dx <= 5; ++dx) c->SetPixel(x + dx, y + 7, kBase.r, kBase.g, kBase.b);
    for (int dx = 3; dx <= 5; ++dx) c->SetPixel(x + dx, y + 8, kBase.r, kBase.g, kBase.b);
}

// Candidate 9: candidate 8 shrunk — same 5 rays + V filament + base, tighter
// spacing. 7x8 bounding box (vs 8's 9x9).
static void DrawBulb9(Canvas* c, int x, int y)
{
    const Color kGlass(255, 200, 0);
    const Color kFil(90, 50, 0);
    const Color kBase(70, 70, 70);
    c->SetPixel(x + 3, y + 0, kGlass.r, kGlass.g, kGlass.b);  // N ray
    c->SetPixel(x + 1, y + 1, kGlass.r, kGlass.g, kGlass.b);  // NW ray
    c->SetPixel(x + 5, y + 1, kGlass.r, kGlass.g, kGlass.b);  // NE ray
    for (int dx = 2; dx <= 4; ++dx) c->SetPixel(x + dx, y + 2, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 0, y + 3, kGlass.r, kGlass.g, kGlass.b);  // W ray
    for (int dx = 2; dx <= 4; ++dx) c->SetPixel(x + dx, y + 3, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 6, y + 3, kGlass.r, kGlass.g, kGlass.b);  // E ray
    c->SetPixel(x + 2, y + 4, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 3, y + 4, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 4, y + 4, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 2, y + 5, kGlass.r, kGlass.g, kGlass.b);
    c->SetPixel(x + 3, y + 5, kFil.r, kFil.g, kFil.b);
    c->SetPixel(x + 4, y + 5, kGlass.r, kGlass.g, kGlass.b);
    for (int dx = 2; dx <= 4; ++dx) c->SetPixel(x + dx, y + 6, kBase.r, kBase.g, kBase.b);
    for (int dx = 2; dx <= 4; ++dx) c->SetPixel(x + dx, y + 7, kBase.r, kBase.g, kBase.b);
}

int main(int argc, char** argv)
{
    signal(SIGTERM, InterruptHandler);
    signal(SIGINT, InterruptHandler);

    rgb_matrix::RGBMatrix::Options options;
    rgb_matrix::RuntimeOptions runtime;
    if (!rgb_matrix::ParseOptionsFromFlags(&argc, &argv, &options, &runtime))
    {
        fprintf(stderr, "Invalid LED options.\n");
        return 1;
    }
    options.hardware_mapping = "adafruit-hat";
    options.rows = 32;
    options.cols = 64;
    options.pwm_bits = 6;
    options.led_rgb_sequence = "RGB";
    options.disable_hardware_pulsing = true;
    runtime.gpio_slowdown = 3;

    rgb_matrix::RGBMatrix* matrix = rgb_matrix::RGBMatrix::CreateFromOptions(options, runtime);
    if (!matrix)
    {
        fprintf(stderr, "Could not create matrix.\n");
        return 1;
    }
    matrix->SetBrightness(50);

    Font font;
    if (!font.LoadFont("fonts/5x7.bdf"))
    {
        fprintf(stderr, "Could not load font.\n");
        return 1;
    }

    struct Candidate
    {
        const char* label;
        void (*draw)(Canvas*, int, int);
        int width;  // reserved footprint, so humidity shifts right to avoid crowding
    };
    std::vector<Candidate> candidates = {
        {"1", DrawBulb1, 3}, {"2", DrawBulb2, 4}, {"3", DrawBulb3, 3},
        {"4", DrawBulb4, 4}, {"5", DrawBulb5, 4}, {"6", DrawBulb6, 5},
        {"7", DrawBulb7, 7}, {"8", DrawBulb8, 9}, {"9", DrawBulb9, 7},
    };

    rgb_matrix::FrameCanvas* offscreen = matrix->CreateFrameCanvas();
    size_t idx = 0;
    while (!interrupt_received)
    {
        offscreen->Clear();
        const Candidate& cand = candidates[idx];
        // Sample "feels like" row context: temp | feels-icon | humidity, same
        // baseline (y=20) as the real render loop. Humidity shifts right by the
        // candidate's width so bigger icons don't fake-overlap in this preview.
        constexpr int kIconX = 44;
        rgb_matrix::DrawText(offscreen, font, 2, 20, Color(255, 255, 255), "80F");
        rgb_matrix::DrawText(offscreen, font, 31, 20, Color(255, 255, 255), "83");
        cand.draw(offscreen, kIconX, 15);
        rgb_matrix::DrawText(offscreen, font, kIconX + cand.width + 1, 20, Color(0, 150, 255),
                             "81%");
        rgb_matrix::DrawText(offscreen, font, 2, 30, Color(0, 200, 0), cand.label);
        printf("Showing candidate %s\n", cand.label);
        fflush(stdout);

        offscreen = matrix->SwapOnVSync(offscreen);
        std::this_thread::sleep_for(std::chrono::seconds(5));
        idx = (idx + 1) % candidates.size();
    }

    delete matrix;
    return 0;
}
