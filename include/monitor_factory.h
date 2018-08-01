#ifndef MONITOR_FACTORY_H
#define MONITOR_FACTORY_H

#include <string>
#include <memory>
#include "monitor_base.h"
#include "config/config_enums.h"

#include "hardware_monitors/laser_monitors/laser_device_monitor.h"

namespace monitoring
{
    /**
     * A factory for creating component monitors
     *
     * @author Alex Mitrevski, Santosh Thoduka
     * @contact aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de
     */
    class MonitorFactory
    {
    public:
        /**
         * Returns a pointer to a hardware monitor specified by the given name
         *
         * @param monitor_name monitor description name as specified in 'config_enums/HardwareMonitorNames'
         */
        static std::shared_ptr<MonitorBase> getHardwareMonitor(config::MonitorModeConfig monitor_config_params);

        /**
         * Returns a pointer to a software monitor specified by the given name
         *
         * @param monitor_name monitor description name as specified in 'config_enums/SoftwareMonitorNames'
         */
        static std::shared_ptr<MonitorBase> getSoftwareMonitor(config::MonitorModeConfig monitor_config_params);
    };
}

#endif
