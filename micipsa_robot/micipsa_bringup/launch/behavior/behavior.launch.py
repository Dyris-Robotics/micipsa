# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# ==============
# Micipsa Utils
# ==============
from utils.console.console_utils import subsection

# =========
# Constants
# =========
BEHAVIOR_PACKAGE_NAME = "micipsa_behavior"


def setup_launch(context, *args, **kwargs):
    behavior_pkg_share = FindPackageShare(BEHAVIOR_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context).strip()

    behavior_config_file = (
        LaunchConfiguration("behavior_config_file").perform(context).strip()
    )

    # =====================
    # Pointcloud Processing
    # =====================
    behavior = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🧭 STARTING MICIPSA BEHAVIOR TREE]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            behavior_pkg_share,
                            "launch",
                            "behavior_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "behavior_config_file": behavior_config_file,
                }.items(),
            ),
        ],
    )

    return [behavior]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "log_level",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "behavior_config_file",
                description="Name of the behavior XML config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
