#include <iostream>
#include <vector>
#include <string>
#include "config/config_params.h"
#include "config/config_file_reader.h"
#include "monitor_manager.h"
#include <boost/filesystem.hpp>

std::vector<std::string> readFiles(std::string dir_name)
{
    std::vector<std::string> file_names;
    boost::filesystem::directory_iterator end;
    for (boost::filesystem::directory_iterator iter(dir_name); iter != end; ++iter)
    {
        if (!boost::filesystem::is_directory(*iter))
        {
            file_names.push_back(iter->path().leaf().string());
        }
    }
    return file_names;
}

int main()
{
    std::string hw_monitor_config_dir_name = "../monitor_config/hardware_monitors";
    std::string sw_monitor_config_dir_name = "../monitor_config/software_monitors";

    std::vector<std::string> hw_config_file_names = readFiles(hw_monitor_config_dir_name);
    std::vector<config::ComponentMonitorConfig> hw_monitor_config_params;
    for (auto config_file_name : hw_config_file_names)
    {
        std::cout << "Reading parameters of hardware monitor " <<  config_file_name << std::endl;
        config::ComponentMonitorConfig component_config_params = config::ComponentMonitorConfigFileReader::load(hw_monitor_config_dir_name, config_file_name);
        hw_monitor_config_params.push_back(component_config_params);
    }
    std::cout << std::endl;

    std::vector<std::string> sw_config_file_names = readFiles(sw_monitor_config_dir_name);
    std::vector<config::ComponentMonitorConfig> sw_monitor_config_params;
    for (auto config_file_name : sw_config_file_names)
    {
        std::cout << "Reading parameters of software monitor " <<  config_file_name << std::endl;
        config::ComponentMonitorConfig component_config_params = config::ComponentMonitorConfigFileReader::load(sw_monitor_config_dir_name, config_file_name);
        sw_monitor_config_params.push_back(component_config_params);
    }

    //hardware_monitor_config_params = config::ComponentMonitorConfigFileReader::load(monitor_config_dir_name, "laser_monitor.yaml");

    // std::cout << "Monitor name: " << monitor_config_params.name << std::endl;
    // for (auto mode_params : monitor_config_params.modes)
    // {
    //     std::cout << "    Mode name: " << mode_params.name << std::endl;
    //     for (auto fn_mapping_params : mode_params.mappings)
    //     {
    //         std::cout << "    Inputs:" << std::endl;
    //         for (auto input : fn_mapping_params.inputs)
    //         {
    //             std::cout << "        " << input << std::endl;
    //         }
    //
    //         std::cout << "    Outputs:" << std::endl;
    //         for (auto output : fn_mapping_params.outputs)
    //         {
    //             std::cout << "        Output name: " << output.name << std::endl;
    //             std::cout << "        Obtained value type: " << output.obtained_value_type << std::endl;
    //             std::cout << "        Expected value: " << output.expected_value << std::endl;
    //         }
    //     }
    //     std::cout << std::endl;
    // }

    monitoring::MonitorManager monitor_manager(hw_monitor_config_params, sw_monitor_config_params);
    monitor_manager.monitorComponents();
    return 0;
}
