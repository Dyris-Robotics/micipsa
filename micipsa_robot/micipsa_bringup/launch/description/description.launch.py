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

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import subsection

# =========
# Constants
# =========
DESCRIPTION_PACKAGE_NAME = "micipsa_description"


def setup_launch(context, *args, **kwargs):
    description_pkg_share = FindPackageShare(DESCRIPTION_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    deploy_mode = LaunchConfiguration("deploy_mode").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context)
    devices_config_file = LaunchConfiguration("devices_config_file").perform(context)
    controllers_config_file = LaunchConfiguration("controllers_config_file").perform(
        context
    )

    micipsa_description = GroupAction(
        actions=[
            LogInfo(msg=subsection("[📖 STARTING MICIPSA DESCRIPTION]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            description_pkg_share,
                            "launch",
                            "micipsa_description_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "deploy_mode": deploy_mode,
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "devices_config_file": devices_config_file,
                    "controllers_config_file": controllers_config_file,
                }.items(),
            ),
        ],
    )

    return [micipsa_description]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "deploy_mode",
                description="Use real hardware if true, simulation if false",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "log_level",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "devices_config_file",
                description="Devices config file name or absolute path",
            ),
            DeclareLaunchArgument(
                "controllers_config_file",
                description="Controllers config file name or absolute path",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
