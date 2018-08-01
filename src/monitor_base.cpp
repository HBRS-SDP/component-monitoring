#include "monitor_base.h"

namespace monitoring
{
    MonitorBase::MonitorBase(config::MonitorModeConfig config_params)
    {
        config_params_ = config_params;
    }

    Json::Value MonitorBase::getStatusMessageTemplate()
    {
        Json::Value msg;
        msg["metamodel"] = "ropod-component-monitor-schema.json";
        msg["robotId"] = "";
        return msg;
    }

    std::string MonitorBase::jsonToString(Json::Value msg)
    {
        std::string str = Json::writeString(json_stream_builder_, msg);
        return str;
    }
}
