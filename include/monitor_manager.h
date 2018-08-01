#ifndef MONITOR_MANAGER_H
#define MONITOR_MANAGER_H

#include <map>
#include <vector>
#include <string>
#include <memory>
#include "config/config_params.h"
#include "monitor_base.h"
#include "monitor_factory.h"

namespace monitoring
{
    class MonitorManager
    {
    public:
        MonitorManager(std::vector<config::ComponentMonitorConfig> hw_monitor_config_params,
                       std::vector<config::ComponentMonitorConfig> sw_monitor_config_params);
        void monitorComponents();
    private:
        std::map<std::string, std::vector<std::shared_ptr<MonitorBase>>> hardware_monitors_;
        std::map<std::string, std::vector<std::shared_ptr<MonitorBase>>> software_monitors_;
    };
}

#endif
