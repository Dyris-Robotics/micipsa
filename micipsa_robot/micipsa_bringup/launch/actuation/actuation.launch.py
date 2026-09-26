# ==============
# Launch Imports
# ==============
from launch_ros.substitutions import FindPackageShare
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch.actions import (
    IncludeLaunchDescription,
    GroupAction,
    LogInfo,
    DeclareLaunchArgument,
)

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import (
    subsection,
)

# =========
# Constants
# =========
CONTROL_PACKAGE_NAME = "micipsa_control"


def generate_launch_description():
    pkg_share = FindPackageShare(CONTROL_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    deploy_mode = LaunchConfiguration("deploy_mode")
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level")
    ros2_control_controllers_config_file = LaunchConfiguration(
        "ros2_control_controllers_config_file"
    )
    twist_mux_config_file = LaunchConfiguration("twist_mux_config_file")

    # ============
    # ROS2_CONTROL
    # ============
    ros2_control_stack = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🔍 STARTING ROS2_CONTROL STACK]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([pkg_share, "launch", "controllers_launch.py"])
                ),
                launch_arguments={
                    "deploy_mode": deploy_mode,
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "ros2_control_controllers_config_file": ros2_control_controllers_config_file,
                }.items(),
            ),
        ],
    )

    # =========
    # Twist Mux
    # =========
    twist_mux = GroupAction(
        actions=[
            LogInfo(msg=subsection("[STARTING TWIST MUX]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([pkg_share, "launch", "twist_mux_launch.py"])
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "twist_mux_config_file": twist_mux_config_file,
                }.items(),
            ),
        ],
    )

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
                "ros2_control_controllers_config_file",
                description="Name of the ros2_control controllers config file",
            ),
            DeclareLaunchArgument(
                "twist_mux_config_file",
                description="Name of the twist mux config file",
            ),
            ros2_control_stack,
            twist_mux,
        ]
    )
