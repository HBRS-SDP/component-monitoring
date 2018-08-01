#ifndef CONFIG_PARAMS_H
#define CONFIG_PARAMS_H

#include <string>
#include <vector>

namespace config
{
    struct OutputConfig
    {
        std::string name;
        std::string obtained_value_type;
        std::string expected_value;
    };

    struct FunctionalMappingConfig
    {
        std::vector<std::string> inputs;
        std::vector<OutputConfig> outputs;
    };

    struct MonitorModeConfig
    {
        std::string name;
        std::vector<FunctionalMappingConfig> mappings;
    };

    struct ComponentMonitorConfig
    {
        std::string name;
        std::vector<MonitorModeConfig> modes;
        std::vector<ComponentMonitorConfig> component_dependencies;
    };
}

#endif
