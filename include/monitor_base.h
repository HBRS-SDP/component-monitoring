#ifndef MONITOR_BASE_H
#define MONITOR_BASE_H

#include <vector>
#include <string>
#include <json/json.h>
#include "config/config_params.h"

namespace monitoring
{
    class MonitorBase
    {
    public:
        MonitorBase(config::MonitorModeConfig config_params);
        virtual Json::Value getStatus() = 0;
    protected:
        Json::Value getStatusMessageTemplate();
        std::string jsonToString(Json::Value msg);

        config::MonitorModeConfig config_params_;
        Json::StreamWriterBuilder json_stream_builder_;
    };
}

#endif
