<div align="center">
  <p align="center">
    <img src="doc/images/package_banner.png" alt="micipsa_common banner" width="100%">
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

`micipsa_common` is a shared support package for the Micipsa stack. It holds the small pieces of code, repeated across many packages, that don't belong to any single subsystem on their own. 
It contains no nodes, no launch files, and nothing that runs on its own, packages depend on it at build and/or run time to reuse this logic rather than duplicating it.

---

## Provided Utilities

### `launch_utils.py`

Helpers for resolving file paths inside ROS 2 launch files.

| Function | Description |
|----------|--------------|
| `find_file(pkg_share, file, file_subdir)` | Returns the absolute path to `file` under `pkg_share/file_subdir` if it exists, or `None` if it doesn't. Does not raise, intended for optional existence checks. |
| `resolve_config_path(config_file, bringup_pkg_share, calling_pkg_share, bringup_config_subdir, calling_config_subdir)` | Resolves a config file by searching the bringup package share first, then the calling package's own share. Returns the first match, or `None` if not found in either location. Logs which package the file was found in (or missing from) via `utils.console_utils`. |

This is the function referenced as the standard two-step config resolution pattern (`micipsa_bringup` first, package default second) used across the Micipsa workspace's launch files.

### `device_utils.py`

Helpers for reading hardware device configuration from the `devices.<category>.<name>` hierarchy in a hardware config YAML file.

| Function | Description |
|----------|--------------|
| `get_device_config(pkg_share, device_config_file, device_category, device_name)` | Retrieves and validates the configuration block for one specific device. Raises `ValueError` if the category, device, or its configuration is missing or malformed. |
| `get_all_devices_ports(pkg_share, device_config_file)` | Iterates every category and device under `devices` in the config file and returns a flat list of `{name, port}` entries for all configured ports. Raises `ValueError` if no ports are found. |

Internally, `get_all_devices_ports` relies on a private helper, `_extract_device_ports`, which handles two device shapes: a single `port` key, or a `ports` mapping covering multiple named or indexed ports (e.g. multiple cameras or sensors of the same type).

Both functions read the underlying YAML via `utils.file_utils.get_yaml_config_data` and resolve the file's path via `utils.file_utils.get_file_path`, scoped to a fixed default subdirectory:

```python
DEVICE_CONFIG_DEFAULT_SUBDIR = "config/hardware"
```

### `time.h`

A minimal, dependency-free C++ timestamp type for use in ROS-agnostic libraries (such as `micipsa_core`) that need to represent time without depending on ROS 2 message types.

```cpp
namespace micipsa_common {
struct TimeStamp {
    int64_t sec{0};
    uint32_t nsec{0};
};
}
```

---

## Dependencies

### Build Dependencies

These dependencies are required when building the package.

| Package | Role |
|---------|------|
| `ament_cmake` | Build system |
| `ament_cmake_python` | Installs the two Python packages (`micipsa_common`, `utils`) within a CMake package |

### Runtime Dependencies

This package has no `exec_depend` entries. The Python and C++ utilities it provides have no third-party runtime dependencies of their own beyond the standard library and whatever ROS 2 packages the *consuming* package already depends on.

### Test Dependencies

Used only when running the package test suite.

| Package | Role |
|---|---|
| `ament_lint_auto` / `ament_lint_common` | Code style and copyright linting |

---

## Installation

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
```

Source the workspace:

```bash
source install/setup.bash
```

> [!TIP]
> Add `source /opt/ros/jazzy/setup.bash` and `source ~/ros2_ws/install/setup.bash` to your `~/.bashrc` to avoid repeating these steps in every new terminal. **Adjust the path and ROS distribution name as needed.**

> [!WARNING]
> `micipsa_common`'s `CMakeLists.txt` expects the `utils` Python package to exist at `../../common/utils` relative to its own source directory. Building this package outside the full Micipsa workspace layout (i.e. without that sibling `common/utils` directory present) will fail.

---

## Usage

This package provides importable utilities only and is not launched directly. To use it from another package's launch file:

```python
from micipsa_common.launch_utils import resolve_config_path, find_file
from micipsa_common.device_utils import get_device_config, get_all_devices_ports
from utils.console_utils import ok, warn, error, info
```

Declare the dependency in the consuming package's `package.xml`:

```xml
<exec_depend>micipsa_common</exec_depend>
```

or `<depend>micipsa_common</depend>` if the dependency is also needed at build time.

To use the C++ timestamp type from another package:

```cpp
#include "micipsa_common/time.h"

micipsa_common::TimeStamp stamp;
stamp.sec = 12345;
stamp.nsec = 6789;
```

with the corresponding `package.xml` dependency and a CMake `find_package(micipsa_common REQUIRED)` plus a link/include against its exported include directory.
