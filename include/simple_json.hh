#pragma once
#include <string>
#include <optional>
#include <cctype>
#include <cstdlib>

// Minimal JSON helpers (no <regex>) for specific OpenWeatherMap fields
namespace tinyjson {
  inline size_t skip_ws(const std::string &s, size_t i) {
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    return i;
  }

  inline std::optional<std::string> extract_quoted(const std::string &s, size_t from) {
    size_t q = s.find('"', from);
    if (q == std::string::npos) return std::nullopt;
    std::string out; bool esc = false;
    for (size_t i = q + 1; i < s.size(); ++i) {
      char c = s[i];
      if (esc) { out.push_back(c); esc = false; continue; }
      if (c == '\\') { esc = true; continue; }
      if (c == '"') return out;
      out.push_back(c);
    }
    return std::nullopt;
  }

  inline std::optional<double> extract_number(const std::string &s, size_t from) {
    size_t i = skip_ws(s, from);
    while (i < s.size() && !(s[i]=='-' || s[i]=='+' || std::isdigit(static_cast<unsigned char>(s[i])))) ++i;
    if (i >= s.size()) return std::nullopt;
    char *endptr = nullptr;
    double v = std::strtod(&s[i], &endptr);
    if (&s[i] == endptr) return std::nullopt;
    return v;
  }
}

inline std::optional<std::string> json_string(const std::string &text, const std::string &key) {
  std::string needle = '"' + key + '"';
  size_t p = text.find(needle);
  if (p == std::string::npos) return std::nullopt;
  size_t colon = text.find(':', p + needle.size());
  if (colon == std::string::npos) return std::nullopt;
  return tinyjson::extract_quoted(text, colon + 1);
}

inline std::optional<double> json_number(const std::string &text, const std::string &key) {
  std::string needle = '"' + key + '"';
  size_t p = text.find(needle);
  if (p == std::string::npos) return std::nullopt;
  size_t colon = text.find(':', p + needle.size());
  if (colon == std::string::npos) return std::nullopt;
  return tinyjson::extract_number(text, colon + 1);
}

inline std::optional<std::string> json_array0_string(const std::string &text, const std::string &array, const std::string &key) {
  std::string a = '"' + array + '"';
  size_t p = text.find(a);
  if (p == std::string::npos) return std::nullopt;
  size_t lb = text.find('[', p);
  if (lb == std::string::npos) return std::nullopt;
  size_t br = text.find('{', lb);
  if (br == std::string::npos) return std::nullopt;
  // find end of first object
  size_t i = br + 1; int depth = 1; bool in_str = false; bool esc=false;
  for (; i < text.size(); ++i) {
    char c = text[i];
    if (in_str) {
      if (esc) { esc = false; continue; }
      if (c == '\\') { esc = true; continue; }
      if (c == '"') in_str = false;
      continue;
    }
    if (c == '"') { in_str = true; continue; }
    if (c == '{') depth++;
    else if (c == '}') { depth--; if (depth == 0) break; }
  }
  if (depth != 0) return std::nullopt;
  std::string obj = text.substr(br, i - br + 1);
  std::string needle = '"' + key + '"';
  size_t pk = obj.find(needle);
  if (pk == std::string::npos) return std::nullopt;
  size_t colon = obj.find(':', pk + needle.size());
  if (colon == std::string::npos) return std::nullopt;
  return tinyjson::extract_quoted(obj, colon + 1);
}

