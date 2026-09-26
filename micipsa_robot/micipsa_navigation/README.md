<div align="center">
  <p align="center">
    <img src="doc/images/package_banner.png" alt="micipsa_navigation banner" width="100%">
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

`micipsa_navigation` is a ROS 2 package that configures and launches the Nav2 stack to provide autonomous, collision-free navigation for Micipsa. It manages the full lifecycle of Nav2's stack.

In addition to standard navigation components, this package also launches a custom **dock pose detection node** (`dock_pose.py`) used to support docking behavior. This node uses poses of detected AprilTags in the robot’s environment, and filters these detections to identify a specific target frame defined by a `dock_frame` parameter, when the matching tag is detected, the node publishes its pose as a docking target.

<div align="center">
  <p align="center">
    <img src="doc/gif/nav2_test.gif" alt="Nav2 navigation" width="100%">
  </p>
</div>

---

## Architecture

`micipsa_navigation` sits at the top of the Micipsa autonomy stack. All underlying subsystems and layers must be running and healthy before this package can be activated. The only exception is the **SLAM layer**: Nav2 loads a previously saved map and localizes against it with AMCL, so SLAM must not run at the same time, both would publish the `map → odom` transform.

<div align="center">
  <p align="center">
    <img src="doc/images/micipsa_navigation_layer.png" alt="Micipsa Navigation Layer" width="85%">
  </p>
</div>

---

## ROS 2 Interface

### Published Topics

| Topic | Publisher | Type |
|-------|-----------|------|
| `/map` | `map_server` | `nav_msgs/msg/OccupancyGrid` |
| `/amcl_pose` | `amcl` | `geometry_msgs/msg/PoseWithCovarianceStamped` |
| `/plan` | `planner_server` | `nav_msgs/msg/Path` |
| `/global_costmap/costmap` | `global_costmap` | `nav_msgs/msg/OccupancyGrid` |
| `/local_costmap/costmap` | `local_costmap` | `nav_msgs/msg/OccupancyGrid` |
| `/cmd_vel` | Nav2 | `geometry_msgs/msg/TwistStamped` |
| `/detected_dock_pose` | `dock_pose_node` | `geometry_msgs/msg/PoseStamped` |

`/cmd_vel` is the navigation input of the `twist_mux` started by `micipsa_control`.

### TF Broadcast

| Transform | Broadcaster |
|-----------|-------------|
| `map → odom` | `amcl` |

### Subscribed Topics

| Topic | Subscriber | Type |
|-------|------------|------|
| `/scan` | `amcl`, costmaps, `collision_monitor` | `sensor_msgs/msg/LaserScan` |
| `/odometry/filtered` | `bt_navigator`, `controller_server`, `velocity_smoother` | `nav_msgs/msg/Odometry` |
| `/initialpose` | `amcl` | `geometry_msgs/msg/PoseWithCovarianceStamped` |
| `/goal_pose` | `bt_navigator` | `geometry_msgs/msg/PoseStamped` |
| `/detected_apriltags_poses` | `dock_pose_node` | `micipsa_msgs/msg/AprilTagPoseArray` |
| `/detected_dock_pose` | `docking_server` | `geometry_msgs/msg/PoseStamped` |

### Actions

| Action | Server |
|--------|--------|
| `/navigate_to_pose`, `/navigate_through_poses` | `bt_navigator` |
| `/spin`, `/backup`, `/drive_on_heading`, `/wait`, `/assisted_teleop` | `behavior_server` |
| `/dock_robot`, `/undock_robot` | `docking_server` |

### TF Subscriptions

| Transform | Provided by |
|-----------|-------------|
| `odom → base_footprint` | EKF from `micipsa_localization` |
| `base_footprint → base_link → laser_frame` | `robot_state_publisher` from `micipsa_description` |

### Parameters

#### `dock_pose_node`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dock_frame` | `string` | `home_dock` | AprilTag frame of the dock to target, can be changed at runtime (the `SelectDock` behavior tree node of `micipsa_behavior` sets it) |

### Launch Arguments

#### `nav2_launch.py`

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `use_sim_time` | `bool` | `true` | Use simulation clock if true |
| `log_level` | `string` | `info` | ROS 2 log level (`info`, `warn`, `error`) |
| `nav2_config_file` | `string` | `nav2_params.yaml` | Nav2 config file name or absolute path |
| `map_file` | `string` | `mappy.yaml` | Map file name, looked up in `micipsa_maps/maps` |
| `dock_database` | `string` | `dock_database.yaml` | Dock database file name or absolute path |
| `use_intra_process_comms` | `bool` | `True` | Enable zero copy intra process communication between the composed Nav2 nodes |

#### `dock_pose_launch.py`

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `use_sim_time` | `bool` | `true` | Use simulation clock if true |
| `log_level` | `string` | `info` | ROS 2 log level (`info`, `warn`, `error`) |

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
- [micipsa_msgs](../micipsa_msgs/README.md)
- [micipsa_description](../micipsa_description/README.md) (not required for building, needed in usage section)
- [micipsa_control](../micipsa_control/README.md) (not required for building, needed in usage section)
- [micipsa_localization](../micipsa_localization/README.md) (not required for building, needed in usage section)
- [micipsa_maps](../micipsa_maps/README.md) (not required for building, needed in usage section)

If **deploy** only:

- [micipsa_core](../micipsa_core/README.md) (not required for building, needed in usage section)
- [micipsa_hardware](../micipsa_hardware/README.md) (not required for building, needed in usage section)

If **simulation** only:

- [micipsa_simulation](../micipsa_simulation/README.md) (not required for building, needed in usage section)

### Native Install

Source the ROS 2 installation:

```bash
source /opt/ros/jazzy/setup.bash
```

Install ROS2 dependencies:

```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

Build the packages:

```bash
colcon build
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

To build and run `Micipsa Navigation` Docker image, follow Micipsa Dockerfile README [Build Section](https://micipsa.netlify.app/micipsa_docs/docs/docker/docker_file.html#build).

---

## Configuration

> [!INFO]
> For configuration files, you can specify either the filename or the absolute path. See [Package Standards](https://micipsa.netlify.app/micipsa_docs/docs/project_structure/package_standards.html#config-resolution) for understanding config loading workflow.

### Nav2 (`nav2_params.yaml`)

All Nav2 nodes run in a single `component_container_isolated` and share `nav2_params.yaml`:

| Component | Configuration |
|-----------|---------------|
| Localization | `amcl` with a likelihood field laser model and a differential motion model |
| Global planner | `NavfnPlanner` with A* |
| Controller | `RotationShimController` (rotates to the path heading first) wrapping the `MPPIController` with a `DiffDrive` motion model |
| Path smoother | `SimpleSmoother` |
| Collision monitor | `FootprintApproach` polygon on `/scan`, slows down and stops the robot before a collision |
| Docking | `docking_server` with three dock plugins: `charge_dock`, `check_dock` and `load_dock`, all using the external detection pose published on `/detected_dock_pose` |

### Map

The `map_file` argument is looked up in the `maps/` folder of `micipsa_maps`. When launched alone, `nav2_launch.py` loads `mappy.yaml`. The bringup config uses `dock_area.yaml`, the map of the default simulation world `dock_area.world`.

### Dock Database (`dock_database.yaml`)

Declares the docks known to the docking server, with their type and pose in the `map` frame:

| Dock | Type | Pose (x, y, yaw) |
|------|------|------------------|
| `home_dock` | `charge_dock` | `-4.5, 1.0, 3.14` |
| `fruit_dock` | `check_dock` | `4.5, 0.0, 0.0` |
| `store_dock` | `load_dock` | `-1.0, -4.5, -1.57` |

The dock names match the `tag.frames` configured in `micipsa_perception`'s `apriltags.yaml`, so `dock_pose_node` can forward the pose of the detected tag of the selected dock to the docking server.

---

## Usage

> [!IMPORTANT]
> If you want to enable docking capabilities in addition to autonomous navigation, start the `dock_pose_launch.py` launch file, along with the AprilTags detection pipeline of `micipsa_perception`. Make sure to adjust its parameters according to the deployment mode.

### Simulation

Launch the full Micipsa simulation stack in order, each in a separate terminal:

```bash
ros2 launch micipsa_description micipsa_description_launch.py
```

```bash
ros2 launch micipsa_simulation gazebo_launch.py
```

```bash
ros2 launch micipsa_control controllers_launch.py
```

```bash
ros2 launch micipsa_control twist_mux_launch.py
```

```bash
ros2 launch micipsa_localization rl_ekf_launch.py
```

```bash
ros2 launch micipsa_navigation nav2_launch.py map_file:=dock_area.yaml
```

The `dock_area.yaml` map matches the default simulation world. To use a custom Nav2 config file:

```bash
ros2 launch micipsa_navigation nav2_launch.py nav2_config_file:=my_custom_nav2.yaml
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
ros2 launch micipsa_navigation nav2_launch.py use_sim_time:=false
```

---

### Validation

#### Rviz

```bash
rviz2
```

In RViz Interface:

- Set **Fixed Frame** to `map`
- Add a **Map** display → topic `/map`
- Add a **Path** display → topic `/plan`
- Use the **2D Pose Estimate** tool to set the robot's initial pose on the map before sending a goal
- Use the **2D Goal Pose** tool to send a navigation goal and observe the planned path and robot motion

<div align="center">
  <p align="center">
    <img src="doc/gif/rviz_nav2.gif" alt="Nav2 navigation in RViz" width="100%">
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
| `micipsa_msgs` | Custom message/service definitions used at both build and run time |

#### Runtime Dependencies

These dependencies are not required to build the package but are required when running it.

| Package | Role |
|---|---|
| `nav2_map_server` | Serves the static occupancy grid map. |
| `nav2_amcl` | Performs localization using Adaptive Monte Carlo Localization (AMCL). |
| `nav2_planner` | Computes global paths to navigation goals. |
| `nav2_controller` | Computes local velocity commands to follow planned paths. |
| `nav2_bt_navigator` | Executes navigation behavior trees and coordinates navigation actions. |
| `nav2_smoother` | Smooths planned paths before execution. |
| `nav2_behaviors` | Provides recovery and utility behaviors (e.g., spin, backup, wait). |
| `nav2_velocity_smoother` | Filters and smooths outgoing velocity commands. |
| `nav2_collision_monitor` | Monitors sensor data and stops or slows the robot to avoid collisions. |
| `nav2_lifecycle_manager` | Manages the lifecycle state transitions of Nav2 nodes. |
| `nav2_navfn_planner` | Provides the NavFn global planner plugin used by `nav2_planner` to generate global paths. |
| `nav2_rotation_shim_controller` | Provides the rotation shim controller plugin that wraps the MPPI controller. |
| `nav2_mppi_controller` | Provides the MPPI local controller plugin used by `nav2_controller` for trajectory optimization and path following. |
| `nav2_costmap_2d` | Provides the 2D costmap framework and plugins used for obstacle representation and environment modeling. |
| `opennav_docking` | Provides autonomous docking and undocking services. |

#### Test Dependencies

Used only when running the package test suite.

| Package | Role |
|---|---|
| `ament_lint_auto` / `ament_lint_common` | Code style and copyright linting |
| `ament_cmake_pytest` | Python test runner for colcon |
| `launch_testing_ament_cmake` | Launch test integration for colcon |
| `launch_testing` | Framework for launch-based integration tests |
| `launch` / `launch_ros` | Launch description construction in tests |
| `ament_cmake_ros` | Provides `run_test_isolated.py` for isolated launch tests |

#### Micipsa Packages Dependencies

The launch file and integration test require the following packages to be built and available at runtime:

| Package | Role |
|---|---|
| `micipsa_description` | Must be running so that the static TF tree (`base_footprint → laser_frame`) is published |
| `micipsa_control` | Must be running so that the robot's actuators and state interfaces are active |
| `micipsa_localization` | Must be running so that `/odometry/filtered` and `odom → base_footprint` TF are published |
| `micipsa_simulation` or the LiDAR driver (deploy) | Must be running so that `/scan` is published |
| `micipsa_maps` | Must be available, the map loaded by `map_server` is read from it |
| `micipsa_common` | Provides `resolve_config_path()`, `find_file()`, `find_package_share()` and `utils.console.console_utils` launch utilities |
| `micipsa_msgs` | Micipsa custom messages |

---

### Testing

> [!NOTE]
> The integration test runs Gazebo in headless mode and does not require physical hardware. It requires the other Micipsa packages listed below to be built in the same workspace.

#### Launch Integration Tests

`test_navigation_integration_launch.py` validates the full Nav2 pipeline by launching:

- `micipsa_description` robot model and static TF
- `micipsa_simulation` Gazebo (headless)
- `micipsa_control` ros2_control controllers
- `micipsa_localization` robot_localization EKF
- `micipsa_slam` SLAM Toolbox
- `micipsa_navigation` Nav2 stack

**Success criteria:**

| # | Criterion |
|---|---|
| 1 | Nav2 action server `/navigate_to_pose` becomes available within 120 s |
| 2 | `/global_costmap/costmap` topic becomes available within 120 s |
| 3 | `/local_costmap/costmap` topic becomes available within 120 s |
| 4 | A valid `nav_msgs/OccupancyGrid` message is received on `/global_costmap/costmap` |
| 5 | A valid `nav_msgs/OccupancyGrid` message is received on `/local_costmap/costmap` |
| 6 | `global_costmap.header.frame_id == "map"` |
| 7 | `local_costmap.header.frame_id` is non-empty |
| 8 | Both costmap `width` and `height` metadata fields are non-negative |

A failure indicates one of: Nav2 lifecycle nodes failed to activate, a required TF transform is missing or delayed, SLAM or localization did not produce the expected outputs, a costmap plugin failed to initialize, or the action server was not created.

#### Running Tests

Run only the integration tests:

```bash
colcon build --packages-select micipsa_navigation
colcon test --packages-select micipsa_navigation --ctest-args -L launch -V
colcon test-result --verbose
```

Run all tests including linting:

```bash
colcon build --packages-select micipsa_navigation
colcon test --packages-select micipsa_navigation
colcon test-result --verbose
```

Clean test results between runs:

```bash
colcon test-result --delete-yes
```
