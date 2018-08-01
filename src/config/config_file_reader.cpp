#include "config/config_file_reader.h"

namespace config
{
    /**
     * Loads the configuration parameters of a black box from the given YAML file
     *
     * @param config_file_name absolute path of a config file
     */
    ComponentMonitorConfig ComponentMonitorConfigFileReader::load(const std::string root_dir, const std::string config_file_name)
    {
        ComponentMonitorConfig params;
        YAML::Node root;
        try
        {
            root = YAML::LoadFile(root_dir + "/" + config_file_name);
        }
        catch (const std::exception& e)
        {
            std::cout << e.what() << "\n";
            return params;
        }

        if (root["name"])
        {
            params.name = root["name"].as<std::string>();
        }
        else
        {
            throw ComponentMonitorConfigException("name not specified");
        }

        if (root["modes"])
        {
            for (auto monitor_config : root["modes"])
            {
                std::string monitor_config_file = monitor_config.as<std::string>();
                MonitorModeConfig mode_config = ComponentMonitorConfigFileReader::loadModeConfig(root_dir, monitor_config_file);
                params.modes.push_back(mode_config);
            }
        }
        else
        {
            throw ComponentMonitorConfigException("modes not specified");
        }

        // if (root["dependencies"])
        // {
        //     for (auto monitor_config : root["dependencies"])
        //     {
        //
        //     }
        // }

        return params;
    }

    MonitorModeConfig ComponentMonitorConfigFileReader::loadModeConfig(const std::string root_dir, const std::string config_file_name)
    {
        MonitorModeConfig params;
        YAML::Node root;
        try
        {
            root = YAML::LoadFile(root_dir + "/" + config_file_name);
        }
        catch (const std::exception& e)
        {
            std::cout << e.what() << "\n";
            return params;
        }

        if (root["name"])
        {
            params.name = root["name"].as<std::string>();
        }
        else
        {
            throw ComponentMonitorConfigException("mode_config: name not specified");
        }

        if (root["mappings"])
        {
            for (auto mapping_it=root["mappings"].begin(); mapping_it != root["mappings"].end(); ++mapping_it)
            {
                YAML::Node params_node = mapping_it->begin()->second;
                FunctionalMappingConfig fn_mapping_params;

                fn_mapping_params.inputs = params_node["inputs"].as<std::vector<std::string>>();
                for (auto output_it=params_node["outputs"].begin(); output_it != params_node["outputs"].end(); ++output_it)
                {
                    YAML::Node output_params_node = output_it->begin()->second;
                    OutputConfig output_params;
                    output_params.name = output_params_node["name"].as<std::string>();
                    output_params.obtained_value_type = output_params_node["type"].as<std::string>();
                    if (output_params_node["expected"])
                    {
                        output_params.expected_value = output_params_node["expected"].as<std::string>();
                    }
                    fn_mapping_params.outputs.push_back(output_params);
                }

                params.mappings.push_back(fn_mapping_params);
            }
        }
        else
        {
            throw ComponentMonitorConfigException("mode_config: mappings not specified");
        }

        return params;
    }
}
