<div align="center">
  <p align="center">
    <img src="doc/images/package_banner.png" alt="Micipsa Slam Banner" width="100%">
  </p>
</div>

<div style="display: flex; justify-content: center; gap: 10px;">
  <p>
    <img src="https://img.shields.io/badge/ROS%202-Jazzy-blue?logo=ros" alt="ROS 2 Jazzy">
  </p>
  <p>
    <img src="https://img.shields.io/badge/NVIDIA-Jetson Xavier NX-blue?logo=nvidia" alt="Jetson Xavier NX">
  </p>
  <p>
    <img src="https://img.shields.io/badge/Ubuntu-24.04-blue?logo=ubuntu" alt="ubuntu 24.04">
  </p>
</div>

---

## Overview

`micipsa_slam` is a ROS 2 package that configures and launches `slam_toolbox` in online asynchronous mode to perform 2D SLAM. It subscribes to 2D LiDAR scans on `/scan` and consumes the `odom → base_footprint` transform provided by `micipsa_localization` to build a live occupancy grid map published on `/map` and continuously estimate the `map → odom` transform.

In addition to mapping, the package also includes a **map saving** feature based on `nav2_map_server`’s `map_saver_server`. This node is responsible for exporting the currently generated occupancy grid map to disk when triggered.

<div align="center">
  <p align="center">
    <img src="doc/images/slam_test.gif" alt="Slam Test" width="100%">
  </p>
</div>

---

## Architecture

`micipsa_slam` sits between the localization stack and the navigation stack.

`micipsa_slam` is a **pure configuration and launch package**, it contains no custom nodes or C++ source. Its single responsibility is to configure and launch the upstream `slam_toolbox` with the correct parameters and frame conventions for Micipsa as well as the `map_saver`.

<div align="center">
  <p align="center">
    <img src="doc/images/micipsa_slam_layer.png" alt="Micipsa Slam Layer" width="100%">
  </p>
</div>

<div align="center">
  <p align="center">
    <img src="doc/images/slam_workflow.png" alt="Slam Workflow" width="100%">
  </p>
</div>

---

## ROS 2 Interface

### Published Topics

| Topic | Publisher | Type | QoS |
|---|---|---|---|
| `/map` | `async_slam_toolbox_node` | `nav_msgs/OccupancyGrid` | `RELIABLE` / `TRANSIENT_LOCAL` |
| `/tf` | `async_slam_toolbox_node` | `tf2_msgs/msg/TFMessage` | `RELIABLE` / `VOLATILE` |

### TF Broadcast

| Transform | Broadcaster | Rate |
|---|---|---|
| `map → odom` | `async_slam_toolbox_node` | 50 Hz |

### Subscribed Topics

| Topic | Subscriber | Type | QoS |
|---|---|---|---|
| `/scan` | `async_slam_toolbox_node` | `sensor_msgs/LaserScan` | `BEST_EFFORT` / `VOLATILE` |
| `/tf` | `async_slam_toolbox_node` | `tf2_msgs/TFMessage` | `RELIABLE` / `VOLATILE` |
| `/tf_static` | `async_slam_toolbox_node` | `tf2_msgs/TFMessage` | `RELIABLE` / `TRANSIENT_LOCAL` |

### TF Subscriptions

| Transform | Consumer | Description |
|---|---|---|
| `odom → base_footprint` | `async_slam_toolbox_node` | Local odometry from `micipsa_localization` EKF required before map generation starts |
| `base_footprint → laser_frame` | `async_slam_toolbox_node` | Required to project scans into the robot frame |

---

## Installation

> [!IMPORTANT]
> Micipsa can be run in two ways: **natively** on a ROS 2 host, or via **Docker** using pre-built containerized images. Choose your approach before proceeding:
>
> - **Native** build the package directly in a ROS 2 workspace. Follow [requirements](#requirements) and the [Native Install](#native-install) steps below.
> - **Docker** use the Micipsa container stack, no manual workspace setup required. Skip requirements section and follow [Docker](#docker) section.

### Requirements

First, make sure that the following packages are available in your workspace:

- [micipsa_common](../micipsa_common/README.md)
- [micipsa_description](../micipsa_description/README.md) (not required for building, needed in usage section)
- [micipsa_control](../micipsa_control/README.md) (not required for building, needed in usage section)
- [micipsa_localization](../micipsa_localization/README.md) (not required for building, needed in usage section)

If **simulation**:

- [micipsa_simulation](../micipsa_simulation/README.md) (not required for building, needed in usage section)

### Native Install

Source the ROS 2 installation:

```bash
source /opt/ros/jazzy/setup.bash
```

Install ROS dependencies:

```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

Build the package:

```bash
colcon build --packages-select micipsa_common
colcon build --packages-select micipsa_slam
```

Source the workspace:

```bash
source install/setup.bash
```

> [!TIP]
> Add `source /opt/ros/jazzy/setup.bash` and `source ~/ros2_ws/install/setup.bash` to your `~/.bashrc` to avoid repeating these steps in every new terminal.

### Docker

> [!TIP]
> Reading Micipsa Docker documentation (architecture, dockerfile, docker compose,...) is **strongly recommended**, it covers how the Dockerfiles are structured, how images are built, how containers are orchestrated, and much more.

To build and run `Micipsa Slam` Docker image, follow Micipsa Dockerfile README [Build Section](https://micipsa.netlify.app/micipsa_docs/docs/docker/docker_file.html#build).

---

## Configuration

> [!INFO]
> For configuration files, you can specify either the filename or the absolute path. See [Package Standards](https://micipsa.netlify.app/micipsa_docs/docs/project_structure/package_standards.html#config-resolution) for understanding config loading workflow.

### SLAM Toolbox (`mapper_params_online_async.yaml`)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `mode` | `mapping` | Builds a new map |
| `map_frame` / `odom_frame` / `base_frame` | `map` / `odom` / `base_footprint` | Micipsa frames |
| `scan_topic` | `/scan` | LiDAR input |
| `resolution` | `0.05` | Map resolution in meters per cell |
| `max_laser_range` | `8.0` | Maximum range used to build the map, matching the LiDAR range |
| `map_update_interval` | `5.0` | Seconds between two map updates |
| `minimum_travel_distance` / `minimum_travel_heading` | `0.5` / `0.5` | Motion required before a new scan is processed |
| `transform_publish_period` | `0.02` | `map → odom` published at 50 Hz |
| `do_loop_closing` | `true` | Corrects the accumulated drift when a known place is revisited |

### Map Saver

The map saver configuration sets `save_map_timeout: 5.0`, `free_thresh_default: 0.25` and `occupied_thresh_default: 0.65`. The bringup copy is `micipsa_bringup/config/slam/map_saver.yaml`, the package copy is `config/map.saver.yaml`.

### Launch Arguments

#### `slam_toolbox_launch.py`

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `use_sim_time` | `bool` | `true` | Use simulation clock if true |
| `log_level` | `string` | `info` | ROS 2 log level, declared but not forwarded to SLAM Toolbox yet |
| `slam_toolbox_config_file` | `string` | `mapper_params_online_async.yaml` | SLAM Toolbox config file name or absolute path |

#### `map_server_launch.py`

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `use_sim_time` | `bool` | `true` | Use simulation clock if true |
| `log_level` | `string` | `info` | ROS 2 log level (`info`, `warn`, `error`) |
| `map_saver_config_file` | `string` | `map_saver.yaml` | Map saver config file name or absolute path |

---

## Usage

> [!CAUTION]
> Do not run AMCL simultaneously with SLAM Toolbox. Both nodes publish the `map → odom` transform, which causes TF conflicts and unpredictable localization behavior.

> [!IMPORTANT]
> SLAM Toolbox requires both `/scan` and a valid `odom → base_footprint` transform before it can produce a map.

### Simulation

Launch robot description:

```bash
ros2 launch micipsa_description micipsa_description_launch.py use_sim_time:=true deploy_mode:=false
```

Launch gazebo simulator:

```bash
ros2 launch micipsa_simulation gazebo_launch.py use_sim_time:=true
```

Launch controllers:

```bash
ros2 launch micipsa_control controllers_launch.py use_sim_time:=true deploy_mode:=false
```

Launch the twist multiplexer, to drive the robot while mapping:

```bash
ros2 launch micipsa_control twist_mux_launch.py use_sim_time:=true
```

Launch localization:

```bash
ros2 launch micipsa_localization rl_ekf_launch.py use_sim_time:=true
```

Launch slam:

```bash
ros2 launch micipsa_slam slam_toolbox_launch.py use_sim_time:=true
```

To use a custom configuration file:

```bash
ros2 launch micipsa_slam slam_toolbox_launch.py slam_toolbox_config_file:=my_custom_params.yaml
```

### Deploy

```bash
ros2 launch micipsa_description micipsa_description_launch.py use_sim_time:=false deploy_mode:=true
```

```bash
ros2 launch micipsa_control controllers_launch.py use_sim_time:=false deploy_mode:=true
```

```bash
ros2 launch micipsa_control twist_mux_launch.py use_sim_time:=false
```

```bash
ros2 launch micipsa_localization madgwick_filter_launch.py
```

```bash
ros2 launch micipsa_localization rl_ekf_launch.py use_sim_time:=false
```

```bash
ros2 launch micipsa_slam slam_toolbox_launch.py use_sim_time:=false
```

### Save a Map

Launch the map saver, along with SLAM Toolbox:

```bash
ros2 launch micipsa_slam map_server_launch.py use_sim_time:=true
```

Once the map covers the whole area, save it by calling the map saver service, `map_url` being the output path without extension:

```bash
ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap \
  "{map_topic: map, map_url: /path/to/micipsa/micipsa_robot/micipsa_maps/maps/my_map, image_format: pgm, map_mode: trinary, free_thresh: 0.25, occupied_thresh: 0.65}"
```

This writes `my_map.pgm` and `my_map.yaml`. Saving them in `micipsa_maps/maps` makes them available to `micipsa_navigation` through its `map_file` argument after rebuilding `micipsa_maps`. On the real robot, use `use_sim_time:=false`.

---

## Validation

### Rviz

```bash
rviz2
```

In RViz:
- Set **Fixed Frame** to `map`
- Add a **Map** display → topic `/map`
- Add a **LaserScan** display → topic `/scan`
- Add a **TF** display and verify the chain: `map → odom → base_footprint → laser_frame`

> [!IMPORTANT]
> As the robot moves, LaserScan points should align tightly with the black obstacle borders in the map. If the map blurs or smears, it typically indicates degraded wheel odometry or IMU data feeding the EKF.

<div align="center">
  <p align="center">
    <img src="doc/images/slam_test.gif" alt="Slam Test" width="100%">
  </p>
</div>

### CLI

Confirm the `odom → base_footprint` chain exists (SLAM input dependency):

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

Confirm the `map → odom` transform is being broadcast:

```bash
ros2 run tf2_ros tf2_echo map odom
```

Confirm the map topic is being published:

```bash
ros2 topic echo /map --once
```

<div align="center">
  <p align="center">
    <img src="doc/images/slam_topics_validation.gif" alt="Slam Topics Validation" width="100%">
  </p>
</div>

---

## Additional Information

### Dependencies

#### Build Dependencies

These dependencies are required when building the package.

| Package | Role |
|---------|------|
| `ament_cmake` | Build system |
| `ament_cmake_python` | Python package installation support within a CMake package |

#### Runtime Dependencies

These dependencies are not required to build the package but are required when running it.

| Package | Role |
|---|---|
| `slam_toolbox` | Provides the `async_slam_toolbox_node` executable |
| `nav2_map_server` | Provides the `map_saver_server` node used to save maps |
| `nav2_lifecycle_manager` | Manages the lifecycle (configure/activate) of the `map_saver` node |

#### Test Dependencies

Used only when running the package test suite.

| Package | Role |
|---|---|
| `ament_lint_auto` / `ament_lint_common` | Code style and copyright linting |
| `ament_cmake_pytest` | Python test runner for colcon |
| `launch_testing_ament_cmake` | Launch test integration for colcon |
| `launch_testing` | Framework for launch-based integration tests |
| `launch` | Launch API used by test descriptions |
| `launch_ros` | ROS-specific launch actions used by tests |
| `ament_cmake_ros` | Provides `run_test_isolated.py` for isolated launch tests |

#### Micipsa Packages Dependencies

The launch file and integration test require the following packages to be built and available at runtime:

| Package | Role |
|---|---|
| `micipsa_description` | Must be running so that the `base_footprint → laser_frame` static TF is published |
| `micipsa_control` | Must be running so that the robot's actuators and state interfaces are active |
| `micipsa_localization` | Must be running so that the `odom → base_footprint` transform is published |
| `micipsa_simulation` or the LiDAR driver (deploy) | Must be running so that `/scan` is published |
| `micipsa_common` | Provides `resolve_config_path()`, `find_package_share()` and `utils.console.console_utils` launch utilities |

---

### Testing

> [!NOTE]
> The integration test runs Gazebo in headless mode and does not require physical hardware. It requires the other Micipsa packages listed below to be built in the same workspace.

#### Launch Integration Tests

**`test_slam_integration_launch.py`** validates the full SLAM pipeline by launching:

- `micipsa_description` robot model and static TF
- `micipsa_simulation` Gazebo (headless)
- `micipsa_control` ros2_control controllers
- `micipsa_localization` robot_localization EKF
- `micipsa_slam` SLAM Toolbox

**Success criteria:**

| # | Criterion |
|---|---|
| 1 | `/scan` topic becomes available within 90 s |
| 2 | `/tf` topic becomes available within 90 s |
| 3 | `/map` topic becomes available within 120 s |
| 4 | TF `base_footprint ← laser_frame` resolves within 90 s |
| 5 | TF `odom ← base_footprint` resolves within 90 s |
| 6 | A `nav_msgs/OccupancyGrid` message is received on `/map` |
| 7 | `msg.header.frame_id == "map"` |

A failure indicates one of: missing scan publisher, broken TF chain, EKF not providing odometry, or SLAM Toolbox failing to initialise.

#### Running Tests

Run only the integration tests:

```bash
colcon build --packages-select micipsa_slam
colcon test --packages-select micipsa_slam --ctest-args -L launch -V
colcon test-result --verbose
```

Run all tests:

```bash
colcon build --packages-select micipsa_slam
colcon test --packages-select micipsa_slam
colcon test-result --verbose
```

Clean test results between runs:

```bash
colcon test-result --delete-yes
```
