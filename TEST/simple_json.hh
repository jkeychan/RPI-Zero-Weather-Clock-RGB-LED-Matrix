#pragma once
#include <string>
#include <optional>
#include <regex>

// Minimal helpers to extract simple values from OpenWeatherMap JSON responses

inline std::optional<std::string> json_string(const std::string &text, const std::string &key) {
  std::regex re("\"" + key + "\"\s*:\s*\"([^\"]*)\"");
  std::smatch m; if (std::regex_search(text, m, re)) return m[1];
  return std::nullopt;
}

inline std::optional<double> json_number(const std::string &text, const std::string &key) {
  std::regex re("\"" + key + "\"\s*:\s*([-+]?[0-9]*\.?[0-9]+)");
  std::smatch m; if (std::regex_search(text, m, re)) return std::stod(m[1]);
  return std::nullopt;
}

// Extract the first object's field in an array, e.g. weather[0].main
inline std::optional<std::string> json_array0_string(const std::string &text, const std::string &array, const std::string &key) {
  std::regex re("\"" + array + "\"\s*:\s*\[\s*\{[^}]*\"" + key + "\"\s*:\s*\"([^\"]*)\"");
  std::smatch m; if (std::regex_search(text, m, re)) return m[1];
  return std::nullopt;
}

