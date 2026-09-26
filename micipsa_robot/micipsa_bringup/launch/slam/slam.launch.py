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
SLAM_PACKAGE_NAME = "micipsa_slam"


def setup_launch(context, *args, **kwargs):
    slam_pkg_share = FindPackageShare(SLAM_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    slam_toolbox_config_file = (
        LaunchConfiguration("slam_toolbox_config_file").perform(context).strip()
    )
    map_saver_config_file = (
        LaunchConfiguration("map_saver_config_file").perform(context).strip()
    )

    # ============
    # SLAM ToolBox
    # ============
    slam_toolbox = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🗺️ STARTING MICIPSA SLAM TOOLBOX]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            slam_pkg_share,
                            "launch",
                            "slam_toolbox_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "slam_toolbox_config_file": slam_toolbox_config_file,
                }.items(),
            ),
        ],
    )

    # ==========
    # Map Server
    # ==========
    map_server = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🗺️ STARTING MICIPSA MAP SERVER]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            slam_pkg_share,
                            "launch",
                            "map_server_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "map_saver_config_file": map_saver_config_file,
                }.items(),
            ),
        ],
    )

    return [slam_toolbox, map_server]


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
                "slam_toolbox_config_file",
                description="Name of the slam_toolbox config file",
            ),
            DeclareLaunchArgument(
                "map_saver_config_file",
                description="Name of the map saver config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
