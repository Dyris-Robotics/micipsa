<div align="center">
  <p align="center">
    <img src="doc/images/package_banner.png" alt="Micipsa Core Banner" width="100%">
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

`micipsa_core` is a ROS-agnostic C++ library that implements the hardware abstraction layer for Micipsa. It provides all the logic needed to communicate with the microcontroller over serial, process wheel encoder counts and ingest raw IMU data without depending on any ROS 2 API. The library is designed to be linked into a `ros2_control` hardware component plugin (`micipsa_hardware`).

---

## Architecture

> [!IMPORTANT]
> The implementation of RobotBase and its components particularly the STM32 serial protocol framing in StmController, the absolute encoder count handling in DriveWheel, and the raw IMU data scaling in Imu **is tightly coupled to the behavior of the Yahboom ROS development board firmware**. The packet structure, function codes, checksum scheme, and data layout are all defined by how that board sends and receives data over serial. **If the firmware or the underlying board changes, these classes must be reviewed and updated accordingly.**

`micipsa_core` sits between the physical hardware and ROS 2 control.
The `ros2_control` hardware component plugin (from `micipsa_hardware` package) owns a `RobotBase` instance and is the only place where ROS 2 state/command interfaces are mapped onto the data structures defined here.

<div align="center">
  <p align="center">
    <img src="doc/images/data_flow.png" alt="Data Flow" width="100%">
  </p>
</div>

### Update Cycle

<div align="center">
  <p align="center">
    <img src="doc/images/update_cycle.png" alt="Update Cycle" width="100%">
  </p>
</div>

At every control loop, `Micipsa Hardware Component` calls the following sequence:

#### Read

A background reader thread of `StmController`, started when the hardware component is activated, continuously reads the serial port. It resynchronizes on the `0xFF 0xFB` frame header, checks the frame length and checksum, and keeps the latest valid frame.

`readCurrentState()` → `RobotBase` fetches that latest frame, only if a new one arrived since the previous cycle. The frame type determines which component is updated:

- `FUNC_REPORT_ENCODER` carries the four cumulative encoder counts as `int32` (front left, back right, front right, back left) and routes them to the four `DriveWheel::update()` calls.
- `FUNC_REPORT_ICM_RAW` carries the raw gyroscope and accelerometer values as six `int16` and routes them to `Imu::update()`.

#### Write

`sendCommands()` → `RobotBase::prepareWheelCommands()` calls `DriveWheel::adjustCommand()` on each wheel, which clamps the command (rad/s) to the maximum wheel velocity, mirrors it if the wheel velocity is inverted, and converts it to a wheel speed in mm/s. Then `StmController::formatDriveWheelsSpeedData()` rounds each speed to an `int16`, packs it little endian into a `FUNC_MOTOR_SPEED` frame in the board motor order (M1 front left, M2 back right, M3 front right, M4 back left), and writes the frame to the serial port. The STM32 firmware runs the closed loop speed control.

### Design Constraints

This library enforces a strict no-ROS rule. Every class must be free of ROS headers and ROS-specific types. Any new hardware component added to this library must follow the same pattern: a self-contained class with an `init()` function, an `update()` function, and no ROS dependency.

> [!IMPORTANT]
> It is highly recommended to read `micipsa_hardware` [README](../micipsa_hardware/README.md) to understand better how the `micipsa_core` and `micipsa_hardware` packages relate to each other and how data flows to and from the robot.

---

## ROS 2 Interface

`micipsa_core` is a C++ library, it has no nodes, topics, services, or actions of its own.

---

## Installation

> [!IMPORTANT]
> Micipsa can be run in two ways: **natively** on a ROS 2 host, or via **Docker** using pre-built containerized images. Choose your approach before proceeding:
>
> - **Native** build the package directly in a ROS 2 workspace. Follow [requirements](#requirements) and the [Native Install](#native-install) steps below.
> - **Docker** use the Micipsa container stack, no manual workspace setup required. skip requirements section and follow [Docker](#docker) section.

### Requirements

Make sure that the following packages are available in your workspace:

- [micipsa_common](../micipsa_common/README.md)
- `serial`, the [Dyris-Robotics fork](https://github.com/Dyris-Robotics/serial) of `wjwwood/serial`, already patched to build with colcon

> [!NOTE]
> The original `wjwwood/serial` repository is catkin based (ROS 1) and does not build with colcon. If you use it instead of the fork, follow [Patching the Serial Library](serial_ros2_patch.md) first.

### Native Install

Source the ROS 2 environment:

```bash
source /opt/ros/jazzy/setup.bash
```

Install ROS dependencies from the workspace root:

```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

Build the packages:

```bash
colcon build --packages-select micipsa_common
colcon build --packages-select serial
colcon build --packages-select micipsa_core
```

Source the install overlay:

```bash
source install/setup.bash
```

> [!TIP]
> Add `source /opt/ros/jazzy/setup.bash` and `source ~/ros2_ws/install/setup.bash` to your `~/.bashrc` to avoid repeating these steps in every new terminal.

### Docker

`micipsa_core` package is part of Micipsa Actuation Docker image.

> [!TIP]
> Reading Micipsa Docker documentation (architecture, dockerfile, docker compose,...) is **strongly recommended**, it covers how the Dockerfiles are structured, how images are built, how containers are orchestrated, and much more.

To build and run `Micipsa Actuation` Docker image, follow Micipsa Dockerfile README [Build Section](https://micipsa.netlify.app/micipsa_docs/docs/docker/docker_file.html#build).

---

## Configuration

`micipsa_core` has no configuration files. All parameters are passed programmatically through the `init()` function of each class and ultimately sourced from the `micipsa_hardware` plugin, which reads them from the URDF `ros2_control` hardware component block defined in `micipsa_description`.

<div align="center">
  <p align="center">
    <img src="doc/images/param_flow.png" alt="Param Flow" width="100%">
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
| `serial` | Serial port library used by `StmController` |

#### Test Dependencies

Used only when running the package test suite.

| Package | Role |
|---|---|
| `ament_lint_auto` / `ament_lint_common` | Code style and copyright linting |

#### Micipsa Packages Dependencies

The package requires the following Micipsa packages:

| Package | Role |
|---------|------|
| `micipsa_common` | Utils files used across the Micipsa stack |

#### Third Party Dependencies

| Library | Role | Source |
|---------|------|--------|
| `serial` | Low-level serial communication with the STM32 MCU | [Dyris-Robotics/serial](https://github.com/Dyris-Robotics/serial), fork of [wjwwood/serial](https://github.com/wjwwood/serial) patched for colcon |
---

### Testing

> [!NOTE]
> All tests are hardware-independent. They validate protocol formatting, mathematical conversions, and state management without requiring a physical serial device or microcontroller connection. They run reliably in CI.

### Unit Tests

Each test file targets a single class. Test cases are documented directly in the source files with a description and explicit success criteria.

`test_drive_wheel.cpp` covers initialization to a known zero state, encoder-count-to-angle conversion, full kinematics update (position, angular velocity, linear velocity), inverted command mirroring, and command velocity clamping.

`test_imu.cpp` covers default state initialization (identity quaternion, zero vectors, correct covariance arrays), gyroscope and accelerometer ratio scaling via `applyRatios()`, Z-axis sign correction via `correctAxisSigns()`, orientation pass-through, and header field preservation.

`test_stm_controller.cpp` covers initialization and configuration storage, `clearOutputData()` frame structure and checksum, `clearInputData()` buffer reset, and `formatDriveWheelsSpeedData()` motor frame encoding with correct headers, M1 to M4 wheel mapping, little endian `int16` packing, length, and checksum.

`test_robot_base.cpp` covers `unpackInt16()` signed 16-bit reconstruction from byte pairs, encoder report routing to all four wheels with correct kinematics, and IMU report routing with timestamp forwarding and value propagation.

### Running Tests

Build and run all unit tests:

```bash
colcon build --packages-select micipsa_core
colcon test --packages-select micipsa_core
colcon test-result --verbose
```

Clean test results between runs:

```bash
colcon test-result --delete-yes
```

> [!TIP]
> When adding a new class, register its test executable in `CMakeLists.txt` using `ament_add_gtest` and link it against `${PROJECT_NAME}` and any class-specific dependencies, following the pattern used for `test_drive_wheel` and `test_imu`.
