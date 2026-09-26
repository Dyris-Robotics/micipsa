# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# =============
# Micipsa Utils
# =============
from micipsa_common.device_utils import get_device_config
from utils.filesystem.file_utils import get_file_path

# =========
# Constants
# =========
PACKAGE_NAME = "micipsa_bringup"
DEFAULT_DEVICES_CONFIG_FILE = "devices.yaml"
DEFAULT_LIDAR_CONFIG_FILE = "base_lidar.yaml"
DEFAULT_LIDAR_DEVICE_NAME = "base_lidar"


def setup_launch(context, *args, **kwargs):
    pkg_share = FindPackageShare(PACKAGE_NAME).perform(context)

    # ================
    # Launch Arguments
    # ================
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    devices_config_file = (
        LaunchConfiguration("devices_config_file").perform(context).strip()
    )
    lidar_config_file = (
        LaunchConfiguration("lidar_config_file").perform(context).strip()
    )
    device_name = LaunchConfiguration("device_name").perform(context).strip()
    port_override = LaunchConfiguration("port").perform(context).strip()

    # ===========================
    # Lidar Device Config Loading
    # ===========================
    if port_override:
        lidar_port = port_override
    else:
        lidar_device_config = get_device_config(
            pkg_share, devices_config_file, "lidars", device_name
        )
        lidar_port = str(lidar_device_config.get("port"))

    # ======================
    # Lidar Node Config Path
    # ======================
    lidar_config_path = get_file_path(
        pkg_share, lidar_config_file, config_subdir="config/drivers"
    )

    # ============
    # YDLidar Node
    # ============
    lidar_node = Node(
        package="ydlidar_ros2_driver",
        executable="ydlidar_ros2_driver_node",
        name="ydlidar_ros2_driver_node",
        output="screen",
        emulate_tty=True,
        parameters=[
            lidar_config_path,
            {"port": lidar_port},
        ],
        arguments=["--ros-args", "--log-level", log_level],
    )

    on_start = RegisterEventHandler(
        OnProcessStart(
            target_action=lidar_node,
            on_start=[LogInfo(msg=f"[YDLIDAR] process started on port {lidar_port}")],
        )
    )

    on_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=lidar_node, on_exit=[LogInfo(msg="[YDLIDAR] process exited")]
        )
    )

    return [lidar_node, on_start, on_exit]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "devices_config_file",
                default_value=DEFAULT_DEVICES_CONFIG_FILE,
                description="Devices config file name or absolute path",
            ),
            DeclareLaunchArgument(
                "lidar_config_file",
                default_value=DEFAULT_LIDAR_CONFIG_FILE,
                description="Lidar config file",
            ),
            DeclareLaunchArgument(
                "device_name",
                default_value=DEFAULT_LIDAR_DEVICE_NAME,
                description="Device name, must match device name defined in devices_config_file",
            ),
            DeclareLaunchArgument(
                "port",
                default_value="",
                description="Lidar Device Port. If set, it overrides device_name.",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
