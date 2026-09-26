# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch_ros.substitutions import FindPackageShare

# =============
# Micipsa Utils
# =============
from utils.filesystem.file_utils import get_file_path

# =================
# RealSense Imports
# =================
import os
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.absolute()))
sys.path.append(
    os.path.join(get_package_share_directory("realsense2_camera"), "launch")
)
import rs_launch  # pyright: ignore[reportMissingImports]

# =========
# Constants
# =========
PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CAMERA_CONFIG_FILE = "front_camera.yaml"


def set_configurable_parameters(local_params):
    return {param["name"]: LaunchConfiguration(param["name"]) for param in local_params}


def setup_launch(context, *args, **kwargs):
    pkg_share = FindPackageShare(PACKAGE_NAME).perform(context)

    # ================
    # Launch Arguments
    # ================
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    camera_config_file = (
        LaunchConfiguration("camera_config_file").perform(context).strip()
    )
    device_name = LaunchConfiguration("device_name").perform(context).strip()

    # =======================
    # Camera Node Config Path
    # =======================
    camera_config_path = get_file_path(
        pkg_share, camera_config_file, config_subdir="config/drivers"
    )

    local_parameters = [
        {
            "name": "camera_name",
            "default": device_name,
            "description": "camera unique name",
        },
        {"name": "camera_namespace", "default": "", "description": "camera namespace"},
        {
            "name": "config_file",
            "default": camera_config_path,
            "description": "yaml config file",
        },
        {"name": "log_level", "default": log_level, "description": "node log level"},
    ]
    params = rs_launch.configurable_parameters

    return [
        *rs_launch.declare_configurable_parameters(local_parameters),
        *rs_launch.declare_configurable_parameters(params),
        OpaqueFunction(
            function=rs_launch.launch_setup,
            kwargs={"params": set_configurable_parameters(params)},
        ),
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "camera_config_file",
                default_value=DEFAULT_CAMERA_CONFIG_FILE,
                description="Camera config file",
            ),
            DeclareLaunchArgument(
                "device_name",
                default_value="no_name_given_camera",
                description="Device name, must match device name defined in devices_config_file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
