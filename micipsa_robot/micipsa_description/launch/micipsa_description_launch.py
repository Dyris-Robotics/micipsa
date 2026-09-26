# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.substitutions import (
    Command,
    LaunchConfiguration,
)

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# =======================
# ROS 2 Package Utilities
# =======================
from ament_index_python.packages import (
    get_package_share_directory,
)

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import warn

from micipsa_common.device_utils import (
    get_device_config,
)
from micipsa_common.launch_utils import resolve_config_path, find_package_share


# =========
# Constants
# =========
DEFAULT_CONTROLLERS_CONFIG = "controllers.yaml"
DEFAULT_DEVICES_CONFIG = "devices.yaml"
MCU_BOARD_DEVICE_NAME = "stm_board"
M1_DEVICE_NAME = "m1"
M2_DEVICE_NAME = "m2"
M3_DEVICE_NAME = "m3"
M4_DEVICE_NAME = "m4"

BRINGUP_PACKAGE_NAME = "micipsa_bringup"
DESCRIPTION_PACKAGE_NAME = "micipsa_description"
CONTROL_PACKAGE_NAME = "micipsa_control"


# =========================================================================
#                       Device Configuration Loaders
# =========================================================================
def load_mcu_config(pkg_share: str, config_file: str) -> dict:
    stm_board = get_device_config(
        pkg_share,
        config_file,
        "mcu",
        MCU_BOARD_DEVICE_NAME,
    )

    return {
        "mcu_serial_device_arg": str(stm_board["port"]),
        "mcu_baudrate_arg": str(stm_board.get("baudrate", 115200)),
        "mcu_timeout_arg": str(stm_board.get("timeout", 2000)),
    }


def load_motors_config(pkg_share: str, config_file: str) -> dict:
    m1 = get_device_config(
        pkg_share,
        config_file,
        "motors",
        M1_DEVICE_NAME,
    )

    m2 = get_device_config(
        pkg_share,
        config_file,
        "motors",
        M2_DEVICE_NAME,
    )

    m3 = get_device_config(
        pkg_share,
        config_file,
        "motors",
        M3_DEVICE_NAME,
    )

    m4 = get_device_config(
        pkg_share,
        config_file,
        "motors",
        M4_DEVICE_NAME,
    )

    return {
        "m1_encoder_cpr_arg": str(m1["encoder_cpr"]),
        "m2_encoder_cpr_arg": str(m2["encoder_cpr"]),
        "m3_encoder_cpr_arg": str(m3["encoder_cpr"]),
        "m4_encoder_cpr_arg": str(m4["encoder_cpr"]),
        "m1_inverted_arg": str(m1["invert_sign"]).lower(),
        "m2_inverted_arg": str(m2["invert_sign"]).lower(),
        "m3_inverted_arg": str(m3["invert_sign"]).lower(),
        "m4_inverted_arg": str(m4["invert_sign"]).lower(),
    }


def load_devices_xacro_args(devices_config_file: str, context) -> dict:
    hardware_args = {}
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

    if bringup_pkg_share:
        hardware_args.update(
            load_mcu_config(
                bringup_pkg_share,
                devices_config_file,
            )
        )

        hardware_args.update(
            load_motors_config(
                bringup_pkg_share,
                devices_config_file,
            )
        )
    else:
        print(
            warn(
                f"Package '{BRINGUP_PACKAGE_NAME}' not found. "
                "Using Xacro default devices values from properties.xacro."
            )
        )

    return hardware_args


# =========================================================================
#                    Controllers Configuration Loader
# =========================================================================
def load_controller_config(controllers_config_file: str, context) -> dict:
    control_pkg_share = find_package_share(CONTROL_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)

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
                    f"Given Controllers Config file not found, using default config: '{DEFAULT_CONTROLLERS_CONFIG}'"
                )
            )
            config_path = os.path.join(
                control_pkg_share, "config", DEFAULT_CONTROLLERS_CONFIG
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default controllers config: '{CONTROL_PACKAGE_NAME}' package not found, skipping controllers launch"
                )
            )

    return {
        "controllers_config_file_arg": config_path,
    }


# =========================================================================
#                             Xacro Helpers
# =========================================================================
def build_xacro_command(xacro_file: str, arguments: dict):
    command = ["xacro ", xacro_file]

    for key, value in arguments.items():
        command.extend(
            [
                f" {key}:=",
                value,
            ]
        )

    return Command(command)


# =========================================================================
#                             Launch Setup
# =========================================================================
def setup_launch(context, *args, **kwargs):
    # ================
    # Launch Arguments
    # ================
    deploy_mode = LaunchConfiguration("deploy_mode").perform(context).lower() == "true"
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level")
    devices_config_file = LaunchConfiguration("devices_config_file").perform(context)
    controllers_config_file = LaunchConfiguration("controllers_config_file").perform(
        context
    )

    # ============
    # Xacro File
    # ============
    pkg_path = os.path.join(get_package_share_directory(DESCRIPTION_PACKAGE_NAME))

    xacro_file = os.path.join(
        pkg_path,
        "urdf",
        "micipsa_urdf.xacro",
    )

    # =====================
    # Devices Xacro Args
    # =====================
    devices_args = {}

    if deploy_mode:
        devices_args = load_devices_xacro_args(devices_config_file, context)

    # =====================
    # Controllers Args
    # =====================
    controllers_args = {}

    if not deploy_mode:
        controllers_args = load_controller_config(controllers_config_file, context)

    # ==========
    # Xacro Args
    # ==========
    xacro_args = {
        "deploy_mode": str(deploy_mode).lower(),
        **devices_args,
        **controllers_args,
    }

    # =================
    # Robot Description
    # =================
    robot_description_config = build_xacro_command(
        xacro_file,
        xacro_args,
    )

    params = {
        "robot_description": ParameterValue(
            robot_description_config,
            value_type=str,
        ),
        "use_sim_time": use_sim_time,
    }

    # ==========================
    # Robot State Publisher Node
    # ==========================
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[params],
        arguments=["--ros-args", "--log-level", log_level],
    )

    return [node_robot_state_publisher]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "deploy_mode",
                default_value="false",
                description="set to deploy mode if running on real robot",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "devices_config_file",
                default_value=DEFAULT_DEVICES_CONFIG,
                description="Devices config file name or absolute path",
            ),
            DeclareLaunchArgument(
                "controllers_config_file",
                default_value=DEFAULT_CONTROLLERS_CONFIG,
                description="Controllers config file name or absolute path",
            ),
            OpaqueFunction(
                function=setup_launch,
            ),
        ]
    )
