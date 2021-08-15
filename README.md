# Component Monitoring
This project is concerned with providing a general, unified and robust approach to monitoring a distributed robotic application. To provide flexibility and extensibility, a general API is provided for controling a distributed monitoring system.

## Usage
Run by specifying the path to a configuration file:
```bash
python3 main.py [config_file_path]
```

Example: `python3 main.py config/component_monitoring_config.yaml`

> **NOTE** that the default value of `[config_file_path]` is `config/component_monitoring_config.yaml`.

## Functional Overview
On a system level, **four** components can be identified that together provide the monitoring functionality in a distributed manner.

## Control Message Format
The components of the component monitoring system communicate with each other via the *Apache Kafka Message Bus*. To start, stop and configure the different parts of the system, so called *control messages* are exchanged via the respective *control channel* on *Kafka*. These messages all follow a general message design of header and body. The gerneral structure of all messages looks as follows:
```json
{
    "from": "monitor_manager",
    "to": "rgbd_camera",
    "message":"response",
    "body": {
        ...
    }
}
```
The `from`, `to` and `message` parameters together form the *header* of the message, while the `body` argument contains an arbitrary message body that depends on the actual *type* of message being sent. The high level *type* of a message is determined by the `message` parameter, while the contents of the *body* determine the fully qualified *type*.
|Parameter|Required|Type                                |Description                                       
|---------|--------|------------------------------------|--------------------------------------------------
|`from`   |True    |string                              |Contains the address of the originating component.
|`to`     |True    |string                              |Contains the address of the receiving component.  
|`message`|True    |enum["response", "request", "info"] |Determines the *type* of the message.             
|`body`   |True    |object                              |The body of the message, its contents depend on the *message type*.

### Request
A **request** contains a `command` and the respective `monitors` that it should be applied for. While generally any component can send requests to any other component, currently this type of message is only transmitted by the *fault tolerant component* to request some particular action from one of the managing components in either the *monitor manager* or the *storage manager*.
```json
{
    "command": "activate",
    "monitors": [
        "pointcloud_monitor"
    ]
}
```
|Parameter |Required|Type                                |Description                                       
|----------|--------|------------------------------------|--------------------------------------------------
|`command` |True    |enum["activate", "shutdown", "start_store", "stop_store"]|The action that is requested by the sender.
|`monitors`|True    |array[string]                       |The IDs of the monitors the action should be applied to.

### Response
A **response** is only send as a reply to a previously received **request**. There is two types of responses, `SUCCESS` and `FAILURE`. Each of them can include additional parameters like `monitors` to return information about the results of a particular command. In the case of failure, the response can contain a `message` field to inform the component about the particular problem that occured on the receiver side.

```json
{
    "body": {
        "code": 200,
        "monitors": [
            {
                "name": "pointcloud_monitor",
                "topic": "pointcloud_monitor_eventbus"
            }
        ],
        "message": "Something happened"
}
```
|Parameter |Required|Type                                |Description                                       
|----------|--------|------------------------------------|--------------------------------------------------
|`code`    |True    |integer                             |The response code defining the success of a related request
|`monitors`|False   |array                               |Array of JSON objects containing tupley of `[name, topic]` to inform the receiver about the monitors and the topics which they are publish on
|`message` |False   |string                              |Any message that aids the status code in explaining the success or failure of a request
|

### Info


## Monitor Manager
The **monitor manager** is the central entry point of the monitoring application and controls the individual **monitors**, which are started as processes by the manager on request by the **Faul Tolerant Component** via a `START` message.

## Storage Manager

## Monitor
We see monitors as functions that get a certain input and produce a component status message as an output, such that we define these mappings in YAML-based configuration files.

Based on our abstraction, each component is associated with one or more monitors which may be redundant or may look at different aspects of the component; we refer to these monitors as component monitoring *modes*. We classify monitoring modes into different types, in particular:
* `Existence monitors`: Validate the existence of a component (e.g. whether a hardware device is recognised by the host operating system or whether a process is running)
* `Functional monitors`: Validate the operation of a component, namely whether the component satisfies a predefined functional specification

The configuration file for a given component specifies a list of modes and has the following format:

```
component_name: string          [required] -- Component name (snake case should be used
                                              if the name has multiple words)
description: string             [required] -- Monitored component
modes: list<string>             [required] -- A list of path names to component monitor
                                              configuration files
dependencies: list<string>      [optional] -- A list of components on which the component depends
dependency_monitors: dict       [optional] -- For each dependency in "dependencies", specifies
                                              the types and names of the monitors that are
                                              of interest to the component
```

In `modes`, each file defines the input-output mapping mentioned above and has the format shown below:

```yaml
name: string                                            [required] -- Monitor mode name (snake case
                                                                      should be used if the name has
                                                                      multiple words)
description: string                                     [required] -- Monitor mode description
mappings:                                               [required] -- Specifies a list of functional
                                                                      input-output mappings for the
                                                                      monitor mode
    - mapping:
        inputs: list<string>                            [required] -- A list of inputs to the monitor mode
                                                                      (e.g. data variable names)
        outputs:                                        [required] -- A list of monitor outputs
            - output:
                name: string                            [required] -- Output name
                type: string                            [required] -- Output type (allowed types: bool,
                                                                      string, int, double)
                expected: bool | string | int | double  [optional] -- Expected value of the output
        map_outputs: bool                               [optional] -- Specifies whether the mapping outputs
                                                                      should be returned in a map or not
                                                                      (returning them in a map is useful if there
                                                                      may be an unknown number of output copies -
                                                                      e.g. if the number of sensors changes
                                                                      dynamically)
arguments:                                              [optional] -- A dictionary of arguments to the monitor
                                                                      mode (e.g. thresholds). The arguments
                                                                      should be specified as name-value pairs
    name_n: value_n
```

In this specification, the optional output parameter `map_outputs` allows controlling the overall type of the monitor output, such that if `map_outputs` is set to `true`, the outputs will be returned in a dictionary. This is useful if the number of output value copies is unknown at design time.

### Monitor output

The output produced by each component monitor is a string in JSON format which has the general format shown below:

```json
{
    "monitorName": "",
    "monitorDescription": "",
    "healthStatus":
    {
        ...
    },
    ...
}
```

In this message:
* if `map_outputs` is set to `false` or is not set at all, `healthStatus` is a list of key-value pairs of the output names specified in the monitor configuration file along with the output values corresponding to those
* if `map_outputs` is set to `true`, `healthStatus` is a dictionary in which each value is a list of key-value pairs of the output names

## Specification example

To illustrate the component monitoring configuration described above, we can consider an example in which a robot has two laser scanners whose status we want to monitor. Let us suppose that we have two monitoring modes for the scanners. Namely, we can monitor whether the scanners are: (i) recognised by the host operating system, and (ii) operational. A configuration file for this scenario would look as follows:

```yaml
name: laser_monitor
modes: [laser_monitors/device.yaml, laser_monitors/heartbeat.yaml]
dependencies: []
```

Referring to the two monitor modes as device and heartbeat monitors, we will have the two monitor configuration files shown below:

```yaml
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

```yaml
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

Laser scanner device monitor result example:
```json
{
    "monitorName" : "laser_device_monitor",
    "monitorDescription" : "Monitor verifying that laser devices are recognised by the operating system",
    "healthStatus":
    {
        "hokuyo_front_working": true,
        "hokuyo_rear_working": true
    }
}
```

Battery monitor result example:
```json
{
    "monitorName" : "battery_functional_monitor",
    "monitorDescription" : "Battery level monitor",
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


# Storage Mechanism


## Introduction
* In our current project, we have a lot of Fault-tolerant components that produce many events related data.
* There may be use-cases where these produced signals, if stored, can be used for further analysis *(example - to figure at what point certain failures occur)* or other purposes. Thus the Storage of such events becomes essential.
* But storing all the produced events by every FTSM component could be very impractical as the data can blow up in size within a small amount of time.
* This has lead us to design a storage mechanism that can be switched on/off on demand and which is highly configurable.


## Technical Overview
* Since storage mechanism is required to function independent of the FTSM components and its monitor, The StorageManager runs as a separate process.
* The Storage mechanism is governed by the *'StorageManager'* class. And currently the StorageManager stores the event data by using the ***AbstractStorageComponent***. 
* ***AbstractStorageComponent*** is an abstract class that needs to be inherited by a concrete storage component - which has the ability to store event data to the required database.
* The configuration of which Storage component to be used is specified in the `config.yaml` before running the main program. Currently, the supported Storage components are: 
	1. *SQL-based Storage Component*
	2. *MongoDB-based Storage Component*
* Naturally, in the future - as per the storage requirement, ***AbstractStorageComponent*** can be extended to support other storage components *(such as file based storage, or Redis-based storage, etc.)* if required.


## Storage Components:
1. *SQL-based Storage Component*:
   * This component is implemented with help of the library *'SQLAlchemy'*.
   * There are few advantages when it comes to the use of this library:
     * Usually there is no need for writing raw SQL queries for basic CRUD operations.
     * Also, without the change in code, our system has the ability to communicate with all SQL-based databases supported by SQLAlchemy.
     * In case of switching between different SQL-based database, only changes to the respective configuration of the database needs to be performed. Additionally, it may be required to install the python driver to communicate with the new database.
2. *MongoDB-based Storage Component*:
   * Based on *'pymongo'* based implementation, we implement the basic functions for CRUD operations and listing the stored document in a MongoDB collection.
   * The MongoDB has been configured as the default storage component in the deliverable software package.
   * If the MongoDB is not running on default configuration, then the configuration file `config.yaml` needs to be updated to point to properly running instance of MongoDB.


## Storage Mechanism - Working
* When the main application is run for the Monitor Manager, Storage Manager starts as a sub-process of the main process.
* The Storage Manager initializes the required (configured) storage component but does not store anything immediately.
* Storage Manager keeps listening on the required Kafka control topic. And, as soon as a message,requesting to start storage, arrives on this topic, the Storage Manager updates its Kafka Consumer to listen on the required Kafka Topic where FTSM component is publishing event messages (signals). Whatever this Kafka Consumer listens, firstly it will try to validate if the received message is in a particular format. And then if validation is successful, it will store the message to the required storage component.
* Once Storage Manager receives the `'start_store'` signal, it will keep storing all the event messages. In order, to stop storage of unneccessary message, on the same control topic the FTSM component can send `'stop_store'` command signal. This command will detach the storage Kafka Consumer from the topic where FTSM component is publishing the message,thus in-turn it stops storing the event messages.
* Storage can be started again or stopped again as many times required just by sending the `'start_store'` or `'stop_store'` command signal respectively.
* A better understanding can be found the following flowchart diagram:
![Storage Mechanism Flowchart](docs/StorageManager_Flowchart.png)
