#ifndef MONITORING_CONFIG_ENUMS_H
#define MONITORING_CONFIG_ENUMS_H

#include <string>

namespace monitoring
{
    struct HardwareMonitorNames
    {
        static std::string LASER_DEVICE_MONITOR;
        static std::string LASER_FUNCTIONAL_MONITOR;
        static std::string LASER_HEARTBEAT_MONITOR;
    };

    struct SoftwareMonitorNames
    {
    };
}

#endif
