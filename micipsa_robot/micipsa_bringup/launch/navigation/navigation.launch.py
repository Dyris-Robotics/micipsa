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
NAVIGATION_PACKAGE_NAME = "micipsa_navigation"


def setup_launch(context, *args, **kwargs):
    navigation_pkg_share = FindPackageShare(NAVIGATION_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    nav2_config_file = LaunchConfiguration("nav2_config_file").perform(context).strip()
    map_file = LaunchConfiguration("map_file").perform(context).strip()
    dock_database = LaunchConfiguration("dock_database").perform(context).strip()

    # ====
    # Nav2
    # ====
    nav2 = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🧭 STARTING MICIPSA NAV2]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            navigation_pkg_share,
                            "launch",
                            "nav2_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "nav2_config_file": nav2_config_file,
                    "map_file": map_file,
                    "dock_database": dock_database,
                }.items(),
            ),
        ],
    )

    # =========
    # Dock Pose
    # =========
    dock_pose = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🧭 STARTING MICIPSA DOCK POSE PUBLISHER]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            navigation_pkg_share,
                            "launch",
                            "dock_pose_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                }.items(),
            ),
        ],
    )

    return [nav2, dock_pose]


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
                "nav2_config_file",
                description="Name of the nav2 config file",
            ),
            DeclareLaunchArgument(
                "map_file",
                description="Name of the map file",
            ),
            DeclareLaunchArgument(
                "dock_database",
                description="Name of the dock database file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
