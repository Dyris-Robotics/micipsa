# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import subsection

# =========
# Constants
# =========
PACKAGE_NAME = "micipsa_bringup"


def generate_launch_description():
    pkg_share = FindPackageShare(PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    log_level = LaunchConfiguration("log_level")
    devices_config_file = LaunchConfiguration("devices_config_file")
    front_camera_config_file = LaunchConfiguration("front_camera_config_file")
    front_camera_device_name = LaunchConfiguration("front_camera_device_name")
    base_lidar_config_file = LaunchConfiguration("base_lidar_config_file")
    base_lidar_device_name = LaunchConfiguration("base_lidar_device_name")

    # ======
    # Lidars
    # ======
    base_lidar = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🔍 STARTING YDLIDAR BASE LIDAR DRIVER]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "drivers", "lidar.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "devices_config_file": devices_config_file,
                    "lidar_config_file": base_lidar_config_file,
                    "device_name": base_lidar_device_name,
                }.items(),
            ),
        ],
    )

    # =======
    # Cameras
    # =======
    front_camera = GroupAction(
        actions=[
            LogInfo(msg=subsection("[📷 STARTING REALSENSE FRONT CAMERA DRIVER]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "drivers", "camera.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "camera_config_file": front_camera_config_file,
                    "device_name": front_camera_device_name,
                }.items(),
            ),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "log_level",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "devices_config_file",
                description="Devices config file name or absolute path",
            ),
            DeclareLaunchArgument(
                "front_camera_config_file",
                description="Config file name for the front camera driver",
            ),
            DeclareLaunchArgument(
                "front_camera_device_name",
                description="Device name for the front camera",
            ),
            DeclareLaunchArgument(
                "base_lidar_config_file",
                description="Config file name for the base lidar driver",
            ),
            DeclareLaunchArgument(
                "base_lidar_device_name",
                description="Device name for the base lidar",
            ),
            base_lidar,
            front_camera,
        ]
    )
