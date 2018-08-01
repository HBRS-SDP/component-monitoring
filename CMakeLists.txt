cmake_minimum_required(VERSION 2.8 FATAL_ERROR)

project(component_monitoring)

find_package(yaml-cpp REQUIRED)
find_package(roscpp REQUIRED)
find_package(topic_tools REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(ros_type_introspection REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(PkgConfig)
include(FindPkgConfig)

pkg_check_modules(JSONCPP jsoncpp)
link_libraries(${JSONCPP_LIBRARIES})

pkg_check_modules(LIBMONGOCXX REQUIRED libmongocxx)
pkg_check_modules(LIBBSONCXX REQUIRED libbsoncxx)

set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_RUNTIME OFF)
find_package(Boost)

set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
########################################################################
# LIBZMQ dependency
########################################################################
find_package(libzmq REQUIRED)
IF (LIBZMQ_FOUND)
    include_directories(${LIBZMQ_INCLUDE_DIRS})
    list(APPEND LIBS ${LIBZMQ_LIBRARIES})
ELSE (LIBZMQ_FOUND)
    message( FATAL_ERROR "libzmq not found." )
ENDIF (LIBZMQ_FOUND)

########################################################################
# CZMQ dependency
########################################################################
find_package(czmq REQUIRED)
IF (CZMQ_FOUND)
    include_directories(${CZMQ_INCLUDE_DIRS})
    list(APPEND LIBS ${CZMQ_LIBRARIES})
ELSE (CZMQ_FOUND)
    message( FATAL_ERROR "czmq not found." )
ENDIF (CZMQ_FOUND)

########################################################################
# Zyre dependency
########################################################################
find_package(zyre REQUIRED)
IF (ZYRE_FOUND)
    include_directories(${ZYRE_INCLUDE_DIRS})
    list(APPEND LIBS ${ZYRE_LIBRARIES})
ELSE (ZYRE_FOUND)
    message( FATAL_ERROR "zyre not found." )
ENDIF (ZYRE_FOUND)

include_directories(
    include/
    ${JSONCPP_INCLUDE_DIRS}
    ${LIBMONGOCXX_INCLUDE_DIRS}
    ${LIBBSONCXX_INCLUDE_DIRS}
    ${roscpp_INCLUDE_DIRS}
    ${topic_tools_INCLUDE_DIRS}
    ${std_msgs_INCLUDE_DIRS}
    ${geometry_msgs_INCLUDE_DIRS}
    ${nav_msgs_INCLUDE_DIRS}
    ${sensor_msgs_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
)

link_directories(
    ${LIBMONGOCXX_LIBRARY_DIRS}
    ${LIBBSONCXX_LIBRARY_DIRS}
)

add_library(component_monitoring
    src/config/config_enums.cpp
    src/config/config_file_reader.cpp
    src/monitor_base.cpp
    src/hardware_monitors/laser_monitors/laser_device_monitor.cpp
    # src/hardware_monitors/wheel_monitor.cpp
    src/monitor_factory.cpp
    src/monitor_manager.cpp
)

target_link_libraries(component_monitoring
    tins
    pthread
    zmq
    yaml-cpp
    jsoncpp
    ${LIBMONGOCXX_LIBRARIES}
    ${LIBBSONCXX_LIBRARIES}
    ${roscpp_LIBRARIES}
    ${topic_tools_LIBRARIES}
    ${std_msgs_LIBRARIES}
    ${geometry_msgs_LIBRARIES}
    ${nav_msgs_LIBRARIES}
    ${sensor_msgs_LIBRARIES}
    ${LIBS}
    ${Boost_LIBRARIES}
)

target_compile_features(component_monitoring PRIVATE cxx_range_for)

add_executable(component_monitors
    src/main.cpp
)

target_link_libraries(component_monitors
    component_monitoring
)

target_compile_features(component_monitors PRIVATE cxx_range_for)
