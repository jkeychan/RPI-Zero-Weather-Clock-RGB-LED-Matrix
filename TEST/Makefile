CXX := g++
CXXFLAGS := -O2 -std=c++17 -Wall -Wextra -I../matrix/include
LDFLAGS := -L../matrix/lib -lrgbmatrix -lrt -lm -lpthread -lcurl

SRC := weather_clock.cc simple_json.hh
BIN := weather_clock

all: $(BIN)

$(BIN): weather_clock.cc simple_json.hh
	$(CXX) $(CXXFLAGS) -o $@ weather_clock.cc $(LDFLAGS)

clean:
	rm -f $(BIN)

.PHONY: all clean

