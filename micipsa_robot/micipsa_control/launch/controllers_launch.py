# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# =============
# Micipsa Utils
# =============
from micipsa_common.launch_utils import resolve_config_path, find_package_share
from utils.console.console_utils import warn

# =========
# Constants
# =========
CONTROL_PACKAGE_NAME = "micipsa_control"
BRINGUP_PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CONFIG_FILE_NAME = "controllers.yaml"


def setup_launch(context, *args, **kwargs):
    control_pkg_share = find_package_share(CONTROL_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    deploy_mode = LaunchConfiguration("deploy_mode").perform(context).strip()
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    controllers_config_file = (
        LaunchConfiguration("ros2_control_controllers_config_file")
        .perform(context)
        .strip()
    )

    # ==========================
    # Controllers Config Loading
    # ==========================
    config_path = resolve_config_path(
        controllers_config_file,
        bringup_pkg_share,
        control_pkg_share,
        bringup_config_subdir="config/actuation",
        calling_config_subdir="config",
    )
    if config_path is None:
        if control_pkg_share:
            print(
                warn(
                    f"Given Config file not found, using default config: '{DEFAULT_CONFIG_FILE_NAME}'"
                )
            )
            config_path = os.path.join(
                control_pkg_share, "config", DEFAULT_CONFIG_FILE_NAME
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default config: '{CONTROL_PACKAGE_NAME}' package not found, skipping controllers launch"
                )
            )
            return []

    # ==================
    # Controller Manager
    # ==================
    # In SIM controller manager is launched from gazebo/urdf
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[config_path, {"use_sim_time": use_sim_time}],
        condition=IfCondition(deploy_mode),
        output="both",
        arguments=[
            "--ros-args",
            "--log-level",
            log_level,
        ],
    )

    # ==================
    # IMU Broadcaster
    # ==================
    # In SIM, Gazebo internal IMU plugin generates data
    imu_sensor_broadcaster_node = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "imu_sensor_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--ros-args",
            "--log-level",
            log_level,
        ],
        condition=IfCondition(deploy_mode),
    )

    # =======================
    # Joint State Broadcaster
    # =======================
    joint_state_broadcaster_node = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--ros-args",
            "--log-level",
            log_level,
        ],
    )

    # =====================
    # Diff Drive Controller
    # =====================
    robot_controllers_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "micipsa_base_controller",
            "--controller-manager",
            "/controller_manager",
            "--ros-args",
            "--log-level",
            log_level,
        ],
    )

    return [
        controller_manager,
        imu_sensor_broadcaster_node,
        joint_state_broadcaster_node,
        robot_controllers_spawner,
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "deploy_mode",
                default_value="false",
                description="Set to deploy mode if running on real robot",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "ros2_control_controllers_config_file",
                default_value=DEFAULT_CONFIG_FILE_NAME,
                description="Full path to ros2_control controllers YAML file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
