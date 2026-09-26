# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
)

# =============
# Micipsa Utils
# =============
from micipsa_common.launch_utils import resolve_config_path, find_package_share
from utils.console.console_utils import warn

# =========
# Constants
# =========
BEHAVIOR_PACKAGE_NAME = "micipsa_behavior"
BRINGUP_PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CONFIG_FILE_NAME = "behavior.xml"


def setup_launch(context, *args, **kwargs):
    behavior_pkg_share = find_package_share(BEHAVIOR_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level").perform(context)
    config_file = LaunchConfiguration("behavior_config_file").perform(context).strip()

    # ===================
    # Config File Loading
    # ===================
    config_path = resolve_config_path(
        config_file,
        bringup_pkg_share,
        behavior_pkg_share,
        bringup_config_subdir="config/behavior",
        calling_config_subdir="config",
    )

    if config_path is None:
        if behavior_pkg_share:
            print(
                warn(
                    f"Given Config file not found, using default config: '{DEFAULT_CONFIG_FILE_NAME}'"
                )
            )
            config_path = os.path.join(
                behavior_pkg_share, "config", DEFAULT_CONFIG_FILE_NAME
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default config: '{BEHAVIOR_PACKAGE_NAME}' package not found, skipping behavior launch"
                )
            )
            return []

    # =============
    # Behavior Node
    # =============
    behavior_node = Node(
        package=BEHAVIOR_PACKAGE_NAME,
        executable="behavior_node",
        name="behavior_node",
        parameters=[{"behavior_tree_xml": config_path}, {"use_sim_time": use_sim_time}],
        arguments=["--ros-args", "--log-level", log_level],
    )

    return [behavior_node]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
            ),
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "behavior_config_file",
                default_value=DEFAULT_CONFIG_FILE_NAME,
                description="Name of the behavior XML config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
