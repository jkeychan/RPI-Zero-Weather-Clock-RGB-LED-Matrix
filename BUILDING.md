# Building rgb_display (C++)

## Requirements

All builds need the rpi-rgb-led-matrix submodule:

```bash
git submodule update --init matrix
```

The binary links against `libcurl` and `libmosquitto`. On Pi:

```bash
sudo apt install libcurl4-openssl-dev libmosquitto-dev
```

`libmosquitto-dev` provides both the headers and the runtime library. If you only need the runtime (no build):

```bash
sudo apt install libmosquitto1
```

## Native Build (on Pi Zero W)

```bash
make
sudo ./rgb_display
```

`make` builds `matrix/lib/librgbmatrix.a` automatically on the first run (~2 min on Pi Zero W). Subsequent builds are fast.

**Recommended** for most use cases — no cross-compile toolchain or ARM library setup needed.

## Cross-Compile from macOS

Cross-compilation lets you build the ARMv6 binary on your Mac and `scp` it to the Pi, which is faster than building on the Pi for development iteration. The extra step vs. the native build is sourcing ARM versions of both `librgbmatrix` and `libmosquitto`.

### 1. Install the ARMv6 toolchain (once)

```bash
brew tap messense/macos-cross-toolchains
brew install arm-unknown-linux-gnueabihf
arm-linux-gnueabihf-g++ --version  # verify
```

### 2. Build librgbmatrix on the Pi and copy it back (once, or after matrix/ updates)

The matrix library must be compiled for ARMv6 — it cannot be cross-compiled directly because it uses platform-specific GPIO headers.

```bash
# On Pi Zero W:
cd ~/Documents/Code/RGB-Display/matrix/lib
make
# Takes ~2 min

# On macOS (from repo root):
scp jeff@pi-zero-w-rgb-screen.local:~/Documents/Code/RGB-Display/matrix/lib/librgbmatrix.a \
    prebuilt/librgbmatrix_armv6.a
file prebuilt/librgbmatrix_armv6.a
# Expected: ELF 32-bit LSB, ARM, EABI5 version 1
```

### 3. Copy libmosquitto from the Pi (once, or after mosquitto updates)

```bash
# On Pi Zero W (install if not already present):
sudo apt install libmosquitto-dev -y

# On macOS (from repo root):
scp jeff@pi-zero-w-rgb-screen.local:/usr/lib/arm-linux-gnueabihf/libmosquitto.a \
    prebuilt/libmosquitto_armv6.a
file prebuilt/libmosquitto_armv6.a
# Expected: ELF 32-bit LSB, ARM, EABI5 version 1
```

Then update the `pi` target in `Makefile` to link the prebuilt static library instead of `-lmosquitto`:

```makefile
$(TARGET_CROSS): $(SRC) $(PREBUILT)
    $(CXX_CROSS) $(CXXFLAGS) $(CROSS_ARCH) $(SRC) $(PREBUILT) prebuilt/libmosquitto_armv6.a \
        -lcurl -lpthread -lm -o $(TARGET_CROSS)
```

### 4. Cross-compile and deploy

```bash
make pi
scp rgb_display_armv6 jeff@pi-zero-w-rgb-screen.local:~/Documents/Code/RGB-Display/rgb_display
ssh jeff@pi-zero-w-rgb-screen.local "sudo systemctl restart rgb_display.service"
```

## Linting and Formatting

```bash
make lint     # clang-tidy static analysis
make format   # clang-format -i (in-place)
```

Requires `clang-format` and `clang-tidy`. On macOS:

```bash
brew install llvm
```

The `make lint` target runs `clang-tidy` which parses `#include <mosquitto.h>`. Install mosquitto headers locally so the analysis completes:

```bash
brew install mosquitto
```

## CI / GitHub Releases

Precompiled ARMv6 binaries are built automatically on every version tag push (`v*.*.*`) via GitHub Actions. Download the latest binary from the [Releases page](../../releases).

The release workflow and CodeQL analysis both install `libmosquitto-dev` on the Ubuntu runner.

**Quick install on Pi (first time):**

```bash
git clone https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix.git
cd RPI-Zero-Weather-Clock-RGB-LED-Matrix
cp sample-config.ini config.ini && vi config.ini   # add API key + zip
bash deploy/install.sh                             # service files, log dir, system tuning
wget https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/releases/latest/download/rgb_display
chmod +x rgb_display
sudo apt install libmosquitto1 -y                  # runtime library for MQTT support
sudo systemctl enable --now rgb_display.service
```

**Update binary only (already installed):**

```bash
cd RPI-Zero-Weather-Clock-RGB-LED-Matrix
wget -O rgb_display https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/releases/latest/download/rgb_display
chmod +x rgb_display
sudo systemctl restart rgb_display.service
```

## Why Not Arduino IDE?

Arduino IDE targets microcontrollers (AVR, ARM Cortex-M) with no operating system. The Pi Zero W runs Linux; `librgbmatrix` uses `/dev/gpiomem` for direct GPIO memory access, requires POSIX threads (`pthread`), and drops root privileges after GPIO init — all Linux userspace features. Arduino IDE cannot produce compatible output. Use `make` or the precompiled binary from Releases.

## Prebuilt directory

`prebuilt/librgbmatrix_armv6.a` and `prebuilt/libmosquitto_armv6.a` are not committed to git (listed in `.gitignore`). They must be copied from a Pi as described above. The `prebuilt/` directory itself is tracked via `prebuilt/.gitkeep`.
