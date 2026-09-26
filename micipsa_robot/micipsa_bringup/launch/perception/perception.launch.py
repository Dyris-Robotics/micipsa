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
PERCEPTION_PACKAGE_NAME = "micipsa_perception"


def setup_launch(context, *args, **kwargs):
    perception_pkg_share = FindPackageShare(PERCEPTION_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context).strip()

    pointcloud_config_file = (
        LaunchConfiguration("pointcloud_config_file").perform(context).strip()
    )

    apriltags_config_file = (
        LaunchConfiguration("apriltags_config_file").perform(context).strip()
    )

    # =====================
    # Pointcloud Processing
    # =====================
    pointcloud_processing = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🧭 STARTING MICIPSA POINTCLOUD PROCESSING]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            perception_pkg_share,
                            "launch",
                            "pointcloud_process_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "pointcloud_config_file": pointcloud_config_file,
                }.items(),
            ),
        ],
    )

    # ===================
    # Apriltags Detection
    # ===================
    apriltags_detection = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🧭 STARTING MICIPSA APRILTAGS DETECTION]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            perception_pkg_share,
                            "launch",
                            "apriltags_detection_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "apriltags_config_file": apriltags_config_file,
                }.items(),
            ),
        ],
    )

    return [pointcloud_processing, apriltags_detection]


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
                "pointcloud_config_file",
                description="Name of the pointcloud YAML config file",
            ),
            DeclareLaunchArgument(
                "apriltags_config_file",
                description="Name of the apriltags YAML config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
