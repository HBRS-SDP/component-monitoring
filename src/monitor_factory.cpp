#include "monitor_factory.h"

namespace monitoring
{
    /**
     * Returns a pointer to a hardware monitor specified by the given name
     *
     * @param monitor_name monitor description name as specified in 'config_enums/HardwareMonitorNames'
     */
    std::shared_ptr<MonitorBase> MonitorFactory::getHardwareMonitor(config::MonitorModeConfig monitor_config_params)
    {
        if (monitor_config_params.name == HardwareMonitorNames::LASER_DEVICE_MONITOR)
        {
            std::shared_ptr<LaserDeviceMonitor> monitor(new LaserDeviceMonitor(monitor_config_params));
            return monitor;
        }
        // else if (monitor_name == HardwareMonitorNames::LASER_FUNCTIONAL_MONITOR)
        // {
        //     std::shared_ptr<LaserFunctionalMonitor> monitor(new LaserFunctionalMonitor());
        //     return monitor;
        // }
        // else if (monitor_name == HardwareMonitorNames::LASER_HEARTBEAT_MONITOR)
        // {
        //     std::shared_ptr<LaserHeartbeatMonitor> monitor(new LaserHeartbeatMonitor());
        //     return monitor;
        // }
    }

    /**
     * Returns a pointer to a software monitor specified by the given name
     *
     * @param monitor_name monitor description name as specified in 'config_enums/SoftwareMonitorNames'
     */
    std::shared_ptr<MonitorBase> MonitorFactory::getSoftwareMonitor(config::MonitorModeConfig monitor_config_params)
    {
        return NULL;
    }
}
