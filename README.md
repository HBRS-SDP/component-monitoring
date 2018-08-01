# ROPOD component monitoring

## Component monitor specification

We see monitors as functions that get a certain input and produce a component status message as an output, such that we define these mappings in YAML-based configuration files.

Based on our abstraction, each component is associated with one or more monitors which may be redundant or may look at different aspects of the component; we refer to these monitors as component monitoring *modes*. The configuration file for a given component thus specifies a list of modes and has the following format:

```
name: string | required
modes: list<string> | required
dependencies: list<string> | optional
```

Here, `modes` is a list of path names to component monitor configuration files. Each of these files defines the input-output mapping mentioned above and has the format shown below:

```
name: string | required
mappings:
    - mapping:
        inputs: list[string] | required
        outputs: | required
            - output:
                name: string | required
                type: string | required
                expected: bool | string | int | double | optional
arguments: | optional
    - arg:
        name: bool | string | int | double | required
        value: bool | string | int | double | required
```

The output produced by each component monitor is a string in JSON format which has the general format shown below:

```
{
    "metamodel" : "ropod-component-monitor-schema.json",
    "robotId" : "",
    "monitorName": "",
    "healthStatus":
    {
        ...
    }
}
```

In this message, `healthStatus` is a list of key-value pairs of the output names specified in the monitor configuration file along with the output values corresponding to those.

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
