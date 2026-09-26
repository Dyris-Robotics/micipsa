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
SIMULATION_PACKAGE_NAME = "micipsa_simulation"


def setup_launch(context, *args, **kwargs):
    simulation_pkg_share = FindPackageShare(SIMULATION_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    headless = LaunchConfiguration("headless").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context)

    # ======
    # Gazebo
    # ======
    gazebo = GroupAction(
        actions=[
            LogInfo(msg=subsection("[💻 STARTING MICIPSA SIMULATION]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            simulation_pkg_share,
                            "launch",
                            "gazebo_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "headless": headless,
                }.items(),
            ),
        ],
    )

    return [gazebo]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "log_level",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "headless",
                description='Set to "true" to run Gazebo headlessly',
            ),
            DeclareLaunchArgument(
                "simulation_world_file",
                description="Name of the simulation world",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
