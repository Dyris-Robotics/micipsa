# ============
# Standard Lib
# ============
import os
import time

# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import error_box, info, ok, title, warn
from micipsa_common.device_utils import get_all_devices_ports

# =========
# Constants
# =========
BRINGUP_PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CONFIG_FILE = "devices.yaml"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
RETRY_INTERVAL = TIMEOUT_SECONDS / MAX_RETRIES


def check_critical_devices(context, *args, **kwargs):
    bringup_pkg_share = FindPackageShare(BRINGUP_PACKAGE_NAME).perform(context)

    # ================
    # Launch Arguments
    # ================
    devices_config_file = (
        LaunchConfiguration("devices_config_file").perform(context).strip()
    )

    # =====================
    # Devices Ports Loading
    # =====================
    devices_ports = get_all_devices_ports(bringup_pkg_share, devices_config_file)

    print(title("Checking critical devices..."))

    start_time = time.time()
    missing_devices = []
    for attempt in range(1, MAX_RETRIES + 1):
        print(info(f"Attempt {attempt}/{MAX_RETRIES}"))

        missing_devices = []
        for device in devices_ports:
            name = device["name"]
            path = device["port"]

            if os.path.exists(path):
                print(ok(f"Found device: {name} ({path})"))
            else:
                missing_devices.append(device)
                print(warn(f"Missing device: {name} ({path})"))

        if not missing_devices:
            print(ok("All configured devices detected. Hardware ready."))
            return []

        print(warn(f"Attempt {attempt}/{MAX_RETRIES} failed."))

        elapsed = time.time() - start_time

        if attempt < MAX_RETRIES:
            remaining_time = TIMEOUT_SECONDS - elapsed
            sleep_time = min(RETRY_INTERVAL, max(0.0, remaining_time))
            print(warn(f"Retrying in {sleep_time:.1f} seconds..."))
            time.sleep(sleep_time)

    error_msg = "Hardware check failed after 30 seconds.\nMissing devices:\n"
    for device in missing_devices:
        error_msg += f" - {device['name']}: {device['port']}\n"

    print(error_box("HARDWARE FAILURE CAUSE", error_msg))
    raise RuntimeError(error_msg)


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "devices_config_file",
                default_value=DEFAULT_CONFIG_FILE,
                description="Devices config file name or absolute path",
            ),
            OpaqueFunction(function=check_critical_devices),
        ]
    )
