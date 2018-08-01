#ifndef COMPONENT_MONITOR_CONFIG_FILE_READER_H
#define COMPONENT_MONITOR_CONFIG_FILE_READER_H

#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>
#include <yaml-cpp/yaml.h>
#include <yaml-cpp/node/node.h>
#include "config/config_params.h"

namespace config
{
    /**
     * An interface for reading component monitor configuration files
     *
     * @author Alex Mitrevski, Santosh Thoduka
     * @contact aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de
     */
    class ComponentMonitorConfigFileReader
    {
    public:
        /**
         * Loads the configuration parameters of a component monitor from the given YAML file
         *
         * @param config_file_name absolute path of a config file
         */
        static ComponentMonitorConfig load(const std::string root_dir, const std::string config_file_name);

        /**
         * Loads the configuration parameters of a component monitor from the given YAML file
         *
         * @param config_file_name absolute path of a config file
         */
        static MonitorModeConfig loadModeConfig(const std::string root_dir, const std::string config_file_name);
    };

    class ComponentMonitorConfigException : public std::runtime_error
    {
    public:
        ComponentMonitorConfigException(std::string message)
            : std::runtime_error(message.c_str()), message_(message) {}

        virtual const char* what() const throw()
        {
            return message_.c_str();
        }

    private:
        std::string message_;
    };
}

#endif
