CXX := g++
CXXFLAGS := -O2 -std=c++17 -Wall -Wextra

# Allow overriding matrix include/lib via environment variables
# Usage: make MAT_INC=/path/to/include MAT_LIB=/path/to/lib
MAT_INC ?=
MAT_LIB ?=

# Auto-detect submodule path; fallback to system install (/usr/local)
ifneq (,$(wildcard ../matrix/include/led-matrix.h))
  DETECTED_INC := ../matrix/include
  DETECTED_LIB := ../matrix/lib
else
  DETECTED_INC := /usr/local/include
  DETECTED_LIB := /usr/local/lib
endif

INCLUDES := -I$(if $(MAT_INC),$(MAT_INC),$(DETECTED_INC))
LIBDIRS  := -L$(if $(MAT_LIB),$(MAT_LIB),$(DETECTED_LIB))
LDLIBS   := -lrgbmatrix -lrt -lm -lpthread -lcurl

SRC := weather_clock.cc simple_json.hh
BIN := weather_clock

all: $(BIN)

$(BIN): weather_clock.cc simple_json.hh
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ weather_clock.cc $(LIBDIRS) $(LDLIBS)

clean:
	rm -f $(BIN)

.PHONY: all clean

