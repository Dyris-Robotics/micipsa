# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

from launch.actions import (
    DeclareLaunchArgument,
)

# =========
# Constants
# =========
DEFAULT_MADGWICK_FILTER_GAIN = "0.01"
DEFAULT_MADGWICK_FILTER_FIXED_FRAME = "base_footprint"
DEFAULT_MADGWICK_FILTER_WORLD_FRAME = "enu"


def generate_launch_description():
    # ================
    # Launch Arguments
    # ================
    log_level = LaunchConfiguration("log_level")
    madgwick_filter_use_mag = LaunchConfiguration("madgwick_filter_use_mag")
    madgwick_filter_gain = LaunchConfiguration("madgwick_filter_gain")
    madgwick_filter_fixed_frame = LaunchConfiguration("madgwick_filter_fixed_frame")
    madgwick_filter_world_frame = LaunchConfiguration("madgwick_filter_world_frame")
    madgwick_filter_publish_tf = LaunchConfiguration("madgwick_filter_publish_tf")

    # ====================
    # Madgwick Filter Node
    # ====================
    launch_robot_imu_filter_madgwick = Node(
        package="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        name="imu_filter_madgwick",
        parameters=[
            {"use_mag": madgwick_filter_use_mag},
            {"gain": madgwick_filter_gain},
            {"fixed_frame": madgwick_filter_fixed_frame},
            {"world_frame": madgwick_filter_world_frame},
            {"publish_tf": madgwick_filter_publish_tf},
        ],
        arguments=["--ros-args", "--log-level", log_level],
        remappings=[
            ("/imu/data_raw", "imu_sensor_broadcaster/imu"),
            ("/imu/data", "/micipsa_base/imu/data"),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "madgwick_filter_use_mag",
                default_value="false",
                description="Use magnetometer data in Madgwick filter",
            ),
            DeclareLaunchArgument(
                "madgwick_filter_gain",
                default_value=DEFAULT_MADGWICK_FILTER_GAIN,
                description="Madgwick filter gain parameter",
            ),
            DeclareLaunchArgument(
                "madgwick_filter_fixed_frame",
                default_value=DEFAULT_MADGWICK_FILTER_FIXED_FRAME,
                description="Fixed frame for the IMU filter",
            ),
            DeclareLaunchArgument(
                "madgwick_filter_world_frame",
                default_value=DEFAULT_MADGWICK_FILTER_WORLD_FRAME,
                description="World frame convention (enu, ned, nwu)",
            ),
            DeclareLaunchArgument(
                "madgwick_filter_publish_tf",
                default_value="false",
                description="Publish TF from Madgwick filter",
            ),
            launch_robot_imu_filter_madgwick,
        ]
    )
