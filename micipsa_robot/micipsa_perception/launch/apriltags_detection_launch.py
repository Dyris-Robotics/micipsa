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
PERCEPTION_PACKAGE_NAME = "micipsa_perception"
BRINGUP_PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CONFIG_FILE_NAME = "apriltags.yaml"
DEFAULT_APRILTAGS_POSE_TARGET_FRAME = "odom"


def setup_launch(context, *args, **kwargs):
    perception_pkg_share = find_package_share(PERCEPTION_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level").perform(context)
    config_file = LaunchConfiguration("apriltags_config_file").perform(context).strip()
    apriltags_pose_target_frame = LaunchConfiguration(
        "apriltags_pose_target_frame"
    ).perform(context)

    # ===================
    # Config File Loading
    # ===================
    config_path = resolve_config_path(
        config_file,
        bringup_pkg_share,
        perception_pkg_share,
        bringup_config_subdir="config/perception",
        calling_config_subdir="config",
    )

    if config_path is None:
        if perception_pkg_share:
            print(
                warn(
                    f"Given Config file not found, using default config: '{DEFAULT_CONFIG_FILE_NAME}'"
                )
            )
            config_path = os.path.join(
                perception_pkg_share, "config", DEFAULT_CONFIG_FILE_NAME
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default config: '{PERCEPTION_PACKAGE_NAME}' package not found, skipping apriltags detection launch"
                )
            )
            return []

    # ===================
    # Apriltags Detection
    # ===================
    apriltag_detection_node = Node(
        package="apriltag_ros",
        executable="apriltag_node",
        output="screen",
        parameters=[config_path, {"use_sim_time": use_sim_time}],
        arguments=["--ros-args", "--log-level", log_level],
        remappings=[
            ("/image_rect", "/front_camera/color/image_raw"),
            ("/camera_info", "/front_camera/color/camera_info"),
        ],
    )

    # ==============
    # Apriltag Poses
    # ==============
    apriltag_poses = Node(
        package="micipsa_perception",
        executable="apriltag_poses.py",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "config_file": config_path,
                "target_frame": apriltags_pose_target_frame,
            }
        ],
        arguments=["--ros-args", "--log-level", log_level],
    )

    return [apriltag_detection_node, apriltag_poses]


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
                "apriltags_config_file",
                default_value=DEFAULT_CONFIG_FILE_NAME,
                description="Name of the apriltags YAML config file",
            ),
            DeclareLaunchArgument(
                "apriltags_pose_target_frame",
                default_value=DEFAULT_APRILTAGS_POSE_TARGET_FRAME,
                description="Name of the frame the apriltags will be transformed to",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
