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
    OpaqueFunction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

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
DEFAULT_CONFIG_FILE_NAME = "map_saver.yaml"


def setup_launch(context, *args, **kwargs):
    slam_pkg_share = find_package_share(SLAM_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level")
    map_saver_config_file = (
        LaunchConfiguration("map_saver_config_file").perform(context).strip()
    )

    # ========================
    # Map Saver Config Loading
    # ========================
    config_path = resolve_config_path(
        map_saver_config_file,
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
                    f"Cannot fall back to default config: '{SLAM_PACKAGE_NAME}' package not found, skipping map saver launch"
                )
            )
            return []

    # ===============
    # Map Server Node
    # ===============
    map_server_launch = Node(
        package="nav2_map_server",
        executable="map_saver_server",
        name="map_saver",
        output="screen",
        parameters=[
            config_path,
            {"use_sim_time": use_sim_time},
        ],
        arguments=["--ros-args", "--log-level", log_level],
    )

    # =================
    # Lifecycle Manager
    # =================
    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_slam",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_saver"],
            }
        ],
        arguments=["--ros-args", "--log-level", log_level],
    )

    return [map_server_launch, lifecycle_manager]


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
                "map_saver_config_file",
                default_value=DEFAULT_CONFIG_FILE_NAME,
                description="Name of the map saver config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
