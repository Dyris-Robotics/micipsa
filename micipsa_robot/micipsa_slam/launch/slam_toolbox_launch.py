# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

# =======================
# ROS 2 Package Utilities
# =======================
from ament_index_python.packages import get_package_share_directory

# ==============
# Micipsa Utils
# ==============
from micipsa_common.launch_utils import resolve_config_path, find_package_share
from utils.console.console_utils import warn

# =========
# Constants
# =========
SLAM_PACKAGE_NAME = "micipsa_slam"
BRINGUP_PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CONFIG_FILE_NAME = "mapper_params_online_async.yaml"


def setup_launch(context, *args, **kwargs):
    slam_pkg_share = find_package_share(SLAM_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    slam_toolbox_config_file = (
        LaunchConfiguration("slam_toolbox_config_file").perform(context).strip()
    )

    # ==================
    # SLAM Config Loading
    # ==================
    config_path = resolve_config_path(
        slam_toolbox_config_file,
        bringup_pkg_share,
        slam_pkg_share,
        bringup_config_subdir="config/slam",
        calling_config_subdir="config",
    )
    if config_path is None:
        if slam_pkg_share:
            print(
                warn(
                    f"Given Config file not found, using default config: '{DEFAULT_CONFIG_FILE_NAME}'"
                )
            )
            config_path = os.path.join(
                slam_pkg_share, "config", DEFAULT_CONFIG_FILE_NAME
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default config: '{SLAM_PACKAGE_NAME}' package not found, skipping slam launch"
                )
            )
            return []

    # ========================
    # Slam Toolbox Launch file
    # ========================
    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("slam_toolbox"),
                    "launch",
                    "online_async_launch.py",
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "slam_params_file": config_path,
        }.items(),
    )

    return [slam_toolbox_launch]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "slam_toolbox_config_file",
                default_value=DEFAULT_CONFIG_FILE_NAME,
                description="Name of the slam_toolbox config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
