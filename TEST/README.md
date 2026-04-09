# TEST/

This directory contained the original C++ prototype. It has been superseded:

- `TEST/weather_clock.cc` → `src/weather_clock.cc`
- `TEST/simple_json.hh` → `include/simple_json.hh`

Build with the root `Makefile`. See `BUILDING.md` for instructions.

`TEST/Makefile` and `TEST/test-config.ini.sample` have been removed — the TEST/ directory no longer has a standalone build since source files now live under `src/` and `include/`.
