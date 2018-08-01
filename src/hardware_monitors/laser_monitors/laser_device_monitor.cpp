#include "hardware_monitors/laser_monitors/laser_device_monitor.h"

namespace monitoring
{
    LaserDeviceMonitor::LaserDeviceMonitor(config::MonitorModeConfig config_params)
        : MonitorBase(config_params)
    {
        for (auto mapping : config_params.mappings)
        {
            // each input mapping has a single device name, so we just take the first element
            device_names_.push_back(mapping.inputs[0]);
            device_status_names_.push_back(mapping.outputs[0].name);
        }
    }

    Json::Value LaserDeviceMonitor::getStatus()
    {
        Json::Value status_msg = getStatusMessageTemplate();
        status_msg["monitorName"] = config_params_.name;
        for (size_t i=0; i<device_names_.size(); i++)
        {
            status_msg["healthStatus"][device_status_names_[i]] = boost::filesystem::exists(device_names_[i]);
        }
        return status_msg;
    }
}
