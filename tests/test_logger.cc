#include "include/logger.hh"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>

int main()
{
    const std::string log_path = "/tmp/test_logger_rgb.log";
    // Clean up from any previous run
    std::filesystem::remove(log_path);

    Logger logger(log_path, Logger::Level::DEBUG);
    logger.Info("hello world");
    logger.Debug("debug line");
    logger.Warning("warn line");

    assert(std::filesystem::exists(log_path));
    std::ifstream f(log_path);
    std::string contents((std::istreambuf_iterator<char>(f)),
                          std::istreambuf_iterator<char>());
    assert(contents.find("hello world") != std::string::npos);
    assert(contents.find("debug line") != std::string::npos);
    assert(contents.find("warn line") != std::string::npos);
    std::filesystem::remove(log_path);

    // Test level filtering: INFO logger should not write DEBUG
    Logger logger2(log_path, Logger::Level::INFO);
    logger2.Debug("should not appear");
    logger2.Info("should appear");
    std::ifstream f2(log_path);
    std::string c2((std::istreambuf_iterator<char>(f2)),
                    std::istreambuf_iterator<char>());
    assert(c2.find("should not appear") == std::string::npos);
    assert(c2.find("should appear") != std::string::npos);
    std::filesystem::remove(log_path);

    // Test ParseLevel
    assert(Logger::ParseLevel("DEBUG") == Logger::Level::DEBUG);
    assert(Logger::ParseLevel("WARNING") == Logger::Level::WARNING);
    assert(Logger::ParseLevel("ERROR") == Logger::Level::ERROR);
    assert(Logger::ParseLevel("INFO") == Logger::Level::INFO);
    assert(Logger::ParseLevel("BOGUS") == Logger::Level::INFO);  // default

    // Test rotation: write enough data to trigger rotation
    {
        const std::string rot_path = "/tmp/test_logger_rotation.log";
        std::filesystem::remove(rot_path);
        std::filesystem::remove(rot_path + ".1");
        std::filesystem::remove(rot_path + ".2");

        // Use a small rotate threshold via a subclass/workaround:
        // Write 1MB + 1 byte by writing many lines
        Logger rot_logger(rot_path, Logger::Level::INFO);

        // Each line is ~40 bytes. 1MB / 40 = ~26,000 lines needed.
        // Write 30,000 lines to ensure we cross 1MB threshold.
        std::string filler(50, 'x');
        for (int i = 0; i < 30000; ++i) {
            rot_logger.Info(filler);
        }

        // After rotation: rot_path should exist (new log), rot_path.1 should exist
        assert(std::filesystem::exists(rot_path));
        assert(std::filesystem::exists(rot_path + ".1"));

        std::filesystem::remove(rot_path);
        std::filesystem::remove(rot_path + ".1");
        std::filesystem::remove(rot_path + ".2");
    }

    return 0;
}
