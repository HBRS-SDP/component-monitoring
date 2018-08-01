#include "monitor_manager.h"
#include <iostream>

namespace monitoring
{
    MonitorManager::MonitorManager(std::vector<config::ComponentMonitorConfig> hw_monitor_config_params,
                                   std::vector<config::ComponentMonitorConfig> sw_monitor_config_params)
    {
        for (auto monitor_config : hw_monitor_config_params)
        {
            hardware_monitors_[monitor_config.name] = std::vector<std::shared_ptr<MonitorBase>>();
            for (auto monitor_mode_config : monitor_config.modes)
            {
                hardware_monitors_[monitor_config.name].push_back(MonitorFactory::getHardwareMonitor(monitor_mode_config));
            }
        }

        for (auto monitor_config : sw_monitor_config_params)
        {
            hardware_monitors_[monitor_config.name] = std::vector<std::shared_ptr<MonitorBase>>();
            for (auto monitor_mode_config : monitor_config.modes)
            {
                hardware_monitors_[monitor_config.name].push_back(MonitorFactory::getSoftwareMonitor(monitor_mode_config));
            }
        }
    }

    void MonitorManager::monitorComponents()
    {
        Json::StreamWriterBuilder json_stream_builder_;

        Json::Value component_status_msg;
        for (auto component_monitors : hardware_monitors_)
        {
            std::string component_monitor_name = component_monitors.first;
            Json::Value &mode_status_msgs = component_status_msg[component_monitor_name];
            for (auto monitor : component_monitors.second)
            {
                Json::Value monitor_status = monitor->getStatus();
                mode_status_msgs.append(monitor_status);
                std::cout << Json::writeString(json_stream_builder_, monitor_status) << std::endl;
            }
        }
        std::cout << std::endl;
        std::cout << Json::writeString(json_stream_builder_, component_status_msg) << std::endl;
    }
}
