#pragma once
#include <ctime>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <string>

class Logger
{
   public:
    enum class Level
    {
        DEBUG = 0,
        INFO = 1,
        WARNING = 2,
        ERROR = 3
    };

    static Level ParseLevel(const std::string& s)
    {
        if (s == "DEBUG")
            return Level::DEBUG;
        if (s == "WARNING")
            return Level::WARNING;
        if (s == "ERROR")
            return Level::ERROR;
        return Level::INFO;
    }

    Logger(const std::string& path, Level min_level = Level::INFO)
        : path_(path), min_level_(min_level)
    {
        std::filesystem::create_directories(std::filesystem::path(path).parent_path());
    }

    void Debug(const std::string& msg)
    {
        Write(Level::DEBUG, "DEBUG", msg);
    }
    void Info(const std::string& msg)
    {
        Write(Level::INFO, "INFO", msg);
    }
    void Warning(const std::string& msg)
    {
        Write(Level::WARNING, "WARNING", msg);
    }
    void Error(const std::string& msg)
    {
        Write(Level::ERROR, "ERROR", msg);
    }

   private:
    static constexpr std::uintmax_t kRotateBytes = 1024 * 1024;  // 1 MB
    static constexpr int kKeepFiles = 3;

    std::string path_;
    Level min_level_;
    std::mutex mu_;

    void Rotate()
    {
        namespace fs = std::filesystem;
        for (int i = kKeepFiles - 1; i > 0; --i)
        {
            auto older = path_ + "." + std::to_string(i);
            auto newer = (i == 1) ? path_ : path_ + "." + std::to_string(i - 1);
            std::error_code ec;
            if (fs::exists(older, ec))
                fs::remove(older, ec);
            if (fs::exists(newer, ec))
                fs::rename(newer, older, ec);
        }
    }

    void Write(Level level, const char* label, const std::string& msg)
    {
        if (level < min_level_)
            return;
        std::lock_guard<std::mutex> lock(mu_);

        namespace fs = std::filesystem;
        std::error_code ec;
        if (fs::exists(path_, ec))
        {
            auto fsize = fs::file_size(path_, ec);
            if (!ec && fsize >= kRotateBytes)
                Rotate();
        }

        std::ofstream f(path_, std::ios::app);
        if (!f)
            return;

        std::time_t now = std::time(nullptr);
        struct tm tm_buf {};
        localtime_r(&now, &tm_buf);
        char ts[32];
        if (std::strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", &tm_buf) == 0)
            ts[0] = '\0';
        f << "[" << ts << "] [" << label << "] " << msg << "\n";
    }
};
