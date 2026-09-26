# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
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
DEFAULT_TWIST_MUX_CONFIG_FILE = "twist_mux.yaml"
DEFAULT_CMD_VEL_OUTPUT_TOPIC = "/micipsa_base_controller/cmd_vel"


def setup_launch(context, *args, **kwargs):
    control_pkg_share = find_package_share(CONTROL_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    twist_mux_config_file = (
        LaunchConfiguration("twist_mux_config_file").perform(context).strip()
    )

    # ========================
    # Twist Mux Config Loading
    # ========================
    config_path = resolve_config_path(
        twist_mux_config_file,
        bringup_pkg_share,
        control_pkg_share,
        bringup_config_subdir="config/actuation",
        calling_config_subdir="config",
    )
    if config_path is None:
        if control_pkg_share:
            print(
                warn(
                    f"Given Config file not found, using default config: '{DEFAULT_TWIST_MUX_CONFIG_FILE}'"
                )
            )
            config_path = os.path.join(
                control_pkg_share, "config", DEFAULT_TWIST_MUX_CONFIG_FILE
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default config: '{CONTROL_PACKAGE_NAME}' package not found, skipping twist mux launch"
                )
            )
            return []

    # =========
    # Twist Mux
    # =========
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[config_path, {"use_sim_time": use_sim_time}],
        remappings=[("/cmd_vel_out", DEFAULT_CMD_VEL_OUTPUT_TOPIC)],
        arguments=[
            "--ros-args",
            "--log-level",
            log_level,
        ],
    )

    return [twist_mux]


def generate_launch_description():
    return LaunchDescription(
        [
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
                "twist_mux_config_file",
                default_value=DEFAULT_TWIST_MUX_CONFIG_FILE,
                description="Name of the twist mux config file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
