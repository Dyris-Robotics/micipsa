<div align="center">
  <p align="center">
    <img src="doc/images/package_banner.png" alt="micipsa_msgs banner" width="100%">
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

`micipsa_msgs` is a ROS 2 interface package that defines the custom message types used to exchange custom data across the Micipsa stack. It contains no nodes, no launch files, and no source code beyond the message, service, and action definitions themselves, its only responsibility is to provide a shared, versioned interface contract between the packages that produce and consume custom Micipsa data.

---

## Message Definitions

### `AprilTagPose.msg`

Describes a single AprilTag detection.

| Field | Type | Description |
|-------|------|--------------|
| `header` | `std_msgs/Header` | Timestamp and frame ID the pose is expressed in |
| `tag_id` | `int32` | Numeric ID encoded in the detected AprilTag |
| `frame` | `string` | Semantic name associated with this tag (e.g. a dock or waypoint identifier) |
| `pose` | `geometry_msgs/Pose` | Position and orientation of the detected tag relative to `header.frame_id` |

### `AprilTagPoseArray.msg`

Bundles all tags detected in a single perception cycle.

| Field | Type | Description |
|-------|------|--------------|
| `header` | `std_msgs/Header` | Timestamp and frame ID common to the detection batch |
| `tag_poses` | `AprilTagPose[]` | List of individual tag detections for this cycle |

---

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
colcon build --packages-select micipsa_msgs
```

Source the workspace:

```bash
source install/setup.bash
```

> [!TIP]
> Add `source /opt/ros/jazzy/setup.bash` and `source ~/ros2_ws/install/setup.bash` to your `~/.bashrc` to avoid repeating these steps in every new terminal.

---

## Additional Information

### Dependencies

#### Build Dependencies

These dependencies are required when building the package.

| Package | Role |
|---------|------|
| `ament_cmake` | Build system |
| `rosidl_default_generators` | Generates language-specific bindings (C++, Python) from the `.msg` definitions |
| `std_msgs` | Provides `Header`, used in both message definitions |
| `geometry_msgs` | Provides `Pose`, used in `AprilTagPose` |

#### Runtime Dependencies

These dependencies are not required to build the package but are required when running it.

| Package | Role |
|---------|------|
| `rosidl_default_runtime` | Runtime support for the generated message bindings |

#### Test Dependencies

Used only when running the package test suite.

| Package | Role |
|---------|------|
| `ament_lint_auto` | Runs the standard suite of linters configured for the workspace |
| `ament_lint_common` | Provides the common lint configurations used by `ament_lint_auto` |
