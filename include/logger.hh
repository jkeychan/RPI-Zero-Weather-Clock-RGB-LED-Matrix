#pragma once
#include <sys/wait.h>
#include <unistd.h>

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

    // Must be constructed before the process drops privileges (e.g. rgb_matrix's
    // drop_privileges): the file is opened here and the descriptor is kept open for the
    // process lifetime, so writes keep working under the post-drop UID even though that
    // UID may lack permission to open the file itself.
    Logger(const std::string& path, Level min_level = Level::INFO)
        : path_(path), min_level_(min_level)
    {
        std::filesystem::create_directories(std::filesystem::path(path).parent_path());
        stream_.open(path_, std::ios::app);
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
    std::ofstream stream_;

    // Compresses a just-rotated file in place (path -> path.gz) by shelling out to gzip.
    // Runs rarely (once per kRotateBytes of log growth), so the fork/exec cost is fine.
    static void GzipFile(const std::string& path)
    {
        pid_t pid = fork();
        if (pid == 0)
        {
            execlp("gzip", "gzip", "-f", path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        else if (pid > 0)
        {
            int status = 0;
            waitpid(pid, &status, 0);
        }
    }

    // Keeps kKeepFiles compressed generations (path.1.gz .. path.N.gz) plus the active
    // file. Closes/reopens stream_ around the rename since the active file's name
    // changes.
    void Rotate()
    {
        namespace fs = std::filesystem;
        std::error_code ec;

        auto oldest = path_ + "." + std::to_string(kKeepFiles) + ".gz";
        if (fs::exists(oldest, ec))
            fs::remove(oldest, ec);

        for (int i = kKeepFiles - 1; i >= 1; --i)
        {
            auto from = path_ + "." + std::to_string(i) + ".gz";
            auto to = path_ + "." + std::to_string(i + 1) + ".gz";
            if (fs::exists(from, ec))
                fs::rename(from, to, ec);
        }

        stream_.close();
        auto rotated = path_ + ".1";
        fs::rename(path_, rotated, ec);
        if (!ec)
            GzipFile(rotated);
        stream_.open(path_, std::ios::app);
    }

    void Write(Level level, const char* label, const std::string& msg)
    {
        if (level < min_level_)
            return;
        std::lock_guard<std::mutex> lock(mu_);
        if (!stream_)
            return;

        namespace fs = std::filesystem;
        std::error_code ec;
        auto fsize = fs::file_size(path_, ec);
        if (!ec && fsize >= kRotateBytes)
            Rotate();
        if (!stream_)
            return;

        std::time_t now = std::time(nullptr);
        struct tm tm_buf = {};
        localtime_r(&now, &tm_buf);
        char ts[32];
        if (std::strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", &tm_buf) == 0)
            ts[0] = '\0';
        stream_ << "[" << ts << "] [" << label << "] " << msg << "\n";
        stream_.flush();
    }
};
