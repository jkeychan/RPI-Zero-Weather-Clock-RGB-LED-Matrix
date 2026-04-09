# Building rgb_display (C++)

## Requirements

All builds need the rpi-rgb-led-matrix submodule:

```bash
git submodule update --init matrix
```

The binary links against `libcurl`. On Pi:

```bash
sudo apt install libcurl4-openssl-dev
```

## Native Build (on Pi Zero W)

```bash
make
sudo ./rgb_display
```

`make` will build `matrix/lib/librgbmatrix.a` automatically on first run (takes ~2 min on Pi Zero W).

## Cross-Compile from macOS (recommended for development)

Cross-compilation lets you build the ARMv6 binary on your Mac and `scp` it to the Pi — much faster than building on the Pi itself.

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

### 3. Cross-compile and deploy

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

## CI / GitHub Releases

Precompiled ARMv6 binaries are built automatically on every version tag push (`v*.*.*`) via GitHub Actions. Download the latest binary from the [Releases page](../../releases).

**Quick install on Pi:**

```bash
wget https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/releases/latest/download/rgb_display
chmod +x rgb_display
sudo mv rgb_display /home/jeff/Documents/Code/RGB-Display/
sudo systemctl restart rgb_display.service
```

## Why Not Arduino IDE?

Arduino IDE targets microcontrollers (AVR, ARM Cortex-M) with no operating system. The Pi Zero W runs Linux; `librgbmatrix` uses `/dev/gpiomem` for direct GPIO memory access, requires POSIX threads (`pthread`), and drops root privileges after GPIO init — all Linux userspace features. Arduino IDE cannot produce compatible output. Use `make` or the precompiled binary from Releases.

## Prebuilt directory

`prebuilt/librgbmatrix_armv6.a` is not committed to git (it's in `.gitignore`). It must be copied from a Pi as described above. The `prebuilt/` directory itself is tracked via `prebuilt/.gitkeep`.
