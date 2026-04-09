# Makefile for rgb_display (C++ weather clock)
# Usage:
#   make               — native build (run on Pi Zero W)
#   make pi            — cross-compile for ARMv6 (run on macOS M5 Max)
#   make lint          — clang-tidy static analysis
#   make format        — clang-format (in-place)
#   make clean         — remove build outputs

CXX          := g++
CXX_CROSS    := arm-linux-gnueabihf-g++

TARGET       := rgb_display
TARGET_CROSS := rgb_display_armv6
SRC          := src/weather_clock.cc
HEADERS      := $(wildcard include/*.hh)
INCLUDES     := -I include -I matrix/include
MATRIX_LIB   := matrix/lib/librgbmatrix.a
PREBUILT     := prebuilt/librgbmatrix_armv6.a

CXXFLAGS     := -std=c++17 -Wall -Wextra -O2 $(INCLUDES)
LDFLAGS      := -lcurl -lpthread -lm

CROSS_ARCH   := -march=armv6 -marm -mfpu=vfp -mfloat-abi=hard

.PHONY: pi lint format clean

all: $(TARGET)

$(TARGET): $(SRC) $(MATRIX_LIB)
	$(CXX) $(CXXFLAGS) $(SRC) $(MATRIX_LIB) $(LDFLAGS) -o $(TARGET)

$(MATRIX_LIB):
	git submodule update --init matrix
	$(MAKE) -C matrix/lib

pi:
	@test -f $(PREBUILT) || { echo "ERROR: $(PREBUILT) not found. See BUILDING.md."; exit 1; }
	$(CXX_CROSS) $(CXXFLAGS) $(CROSS_ARCH) $(SRC) $(PREBUILT) $(LDFLAGS) -o $(TARGET_CROSS)

lint:
	clang-tidy $(SRC) -- $(CXXFLAGS)
	$(if $(HEADERS),clang-tidy $(HEADERS) -- $(CXXFLAGS))

format:
	clang-format -i $(SRC) $(HEADERS)

clean:
	rm -f $(TARGET) $(TARGET_CROSS)
