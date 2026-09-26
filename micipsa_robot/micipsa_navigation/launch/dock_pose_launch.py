# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# =========
# Constants
# =========
NAVIGATION_PACKAGE_NAME = "micipsa_navigation"


def setup_launch(context, *args, **kwargs):
    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level").perform(context).strip()

    # =========
    # Dock Pose
    # =========
    dock_pose = Node(
        package=NAVIGATION_PACKAGE_NAME,
        executable="dock_pose.py",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        arguments=["--ros-args", "--log-level", log_level],
    )

    return [dock_pose]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use simulation clock if true",
            ),
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
