# ROPOD component monitoring


## Dependencies
* [Pyre](https://github.com/ropod-project/pyre)
* [Pyre base communicator](https://github.com/ropod-project/ropod_common)

## Run

Run by specifying the path to a configuration file:

`python3 main.py [config_file_path]`

Example: `python3 main.py config/component_monitoring_config.yaml`

Note that the default value of `[config_file_path]` is `config/component_monitoring_config.yaml`.

## Component monitor specification

We see monitors as functions that get a certain input and produce a component status message as an output, such that we define these mappings in YAML-based configuration files.

Based on our abstraction, each component is associated with one or more monitors which may be redundant or may look at different aspects of the component; we refer to these monitors as component monitoring *modes*. The configuration file for a given component thus specifies a list of modes and has the following format:

```
component_name: string          [required] -- Component name (snake case should be used if the name has multiple words)
description: string             [required] -- Monitored component
modes: list<string>             [required] -- A list of path names to component monitor configuration files
dependencies: list<string>      [optional] -- A list of components on which the component depends
```

In `modes`, each file defines the input-output mapping mentioned above and has the format shown below:

```
name: string                                            [required] -- Monitor mode name (snake case should be used if the name has multiple words)
description: string                                     [required] -- Monitor mode description
mappings:                                               [required] -- Specified a list of functional input-output mappings for the monitor mode
    - mapping:
        inputs: list<string>                            [required] -- A list of inputs to the monitor mode (e.g. data variable names)
        outputs:                                        [required] -- A list of monitor outputs
            - output:
                name: string                            [required] -- Output name
                type: string                            [required] -- Output type (allowed types: bool, string, int, double)
                expected: bool | string | int | double  [optional] -- Expected value of the output
        map_outputs: bool                               [optional] -- Specifies whether the mapping outputs should be returned in a map or not (returning them in a map is useful if there may be an unknown number of output copies - e.g. if the number of sensors changes dynamically)
arguments:                                              [optional] -- An optional list of arguments to the monitor mode (e.g. thresholds)
    - arg:
        name: bool | string | int | double              [required] -- Argument name
        value: bool | string | int | double             [required] -- Argument value
```

In this specification, the optional output parameter `map_outputs` allows controlling the overall type of the monitor output, such that if `map_outputs` is set to `true`, the outputs will be returned in a dictionary. This is useful if the number of output value copies is unknown at design time.

## Monitor Output

The output produced by each component monitor is a string in JSON format which has the general format shown below:

```
{
    "component": "",
    "component_id": "",
    "component_sm_state": "",
    "modes":
    [
        "monitorDescription": "",
        "healthStatus":
        {
            ...
        },
        ...
    ]
}
```

For the full message description, see [ropod-models](https://git.ropod.org/ropod/communication/ropod-models/tree/master/schemas)

In this message:
* if `map_outputs` is set to `false` or is not set at all, `healthStatus` is a list of key-value pairs of the output names specified in the monitor configuration file along with the output values corresponding to those
* on the other hand, if `map_outputs` is set to `true`, `healthStatus` is a dictionary in which each value is a list of key-value pairs of the output names

## Specification example

To illustrate the component monitoring configuration described above, we can consider an example in which a robot has two laser scanners whose status we want to monitor. Let us suppose that we have two monitoring modes for the scanners, namely we can monitor whether (i) the hardware devices as such are recognised by the host operating system and (ii) the scanners are operational. A configuration file for this scenario would look as follows:

```
name: laser_monitor
modes: [laser_monitors/device.yaml, laser_monitors/heartbeat.yaml]
dependencies: []
```

Referring to the two monitor modes as device and heartbeat monitors, we will have the two monitor configuration files shown below:

```
name: laser_device_monitor
mappings:
    - mapping:
        inputs: [/dev/front_laser]
        outputs:
            - output:
                name: front_laser_working
                type: bool
    - mapping:
        inputs: [/dev/rear_laser]
        outputs:
            - output:
                name: rear_laser_working
                type: bool
```

```
name: laser_heartbeat_monitor
mappings:
    - mapping:
        inputs: [/scan_front]
        outputs:
            - output:
                name: front_laser_working
                type: bool
    - mapping:
        inputs: [/scan_rear]
        outputs:
            - output:
                name: rear_laser_working
                type: bool
```

Laser scanner device monitor example:
```
{
    "metamodel" : "ropod-component-monitor-schema.json",
    "robotId" : "ropod_0",
    "healthStatus":
    {
        "hokuyo_front_working": true,
        "hokuyo_rear_working": true
    }
}
```

Battery example:
```
{
    "metamodel" : "ropod-component-monitor-schema.json",
    "robotId" : "ropod_0",
    "healthStatus":
    {
        "battery_working": true,
        "battery_voltage": 12
    }
}
```

## Procedure for adding new monitors

### Automatic procedure

This is the recommended way of adding new monitors since it creates all necessary file skeletons at once.

To add new monitors using this procedure, go to the repository's directory and run

```
python3 component_monitoring/utils/add_monitors.py [component_config_dir] \
[host_name] [monitor_type] [component_name] [mode_names]
```

where:
* `[component_config_dir]` is the path to the component config directory
* `[host_name]` is the name of the host on which the monitors are running (either `robot` or `black-box`)
* `[monitor_type]` is the type of monitor (either `hardware` or `software`)
* `[component_name]` is the name of the component to be monitored
* `[mode_names]` is a list of component monitor modes separated by space

The script will create:
1. A component configuration file `[component_config_dir]/[host_name]/[monitor_type]/[component_name].yaml`
2. A directory `[component_config_dir]/[host_name]/[monitor_type]/[component_name]` and monitor mode configuration files inside it
3. A directory `[monitor_type]/[component_name]` at the location of the package `component_monitoring.monitors` and individual Python scripts for the monitor modes inside it

Once the necessary files are created, one simply has to complete the mode configuration files, the Python scripts of the monitor modes, and, if necessary, list dependencies in the component monitor configuration file.

### Manual procedure

1. Create a monitor configuration file `component_monitoring/component_config/<host>/<type>/<component-name>.yaml`, where `<host>` is either `robot` or `black-box` and `<type>` is either `hardware` or `software` depending on the type of component, and describe the monitoring modes as explained above. Make sure that the `component_name` parameter in the monitor configuration file is set to `<component-name>`
2. Create a directory `component_monitoring/component_config/<host>/<type>/<component-name>` and add the mode configuration files there
3. Create a directory `component_monitoring/monitors/<type>/<component-name>` and implement the mode monitors in separate scripts; the monitors should inherit from the `MonitorBase` class defined in `monitor_base.py`. Make sure that the names of the scripts in which the modes are implemented match the names specified in the mode configuration files
