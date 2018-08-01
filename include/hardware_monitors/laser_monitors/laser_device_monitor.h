#ifndef LASER_MONITOR_H
#define LASER_MONITOR_H

#include <boost/filesystem.hpp>
#include "monitor_base.h"

namespace monitoring
{
    class LaserDeviceMonitor : public MonitorBase
    {
    public:
        LaserDeviceMonitor(config::MonitorModeConfig config_params);
        virtual Json::Value getStatus();
    private:
        std::vector<std::string> device_names_;
        std::vector<std::string> device_status_names_;
    };
}

#endif
