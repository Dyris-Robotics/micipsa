from utils.filesystem.file_utils import (
    get_yaml_config_data,
    get_file_path,
    ensure_is_dictionary,
)
from utils.console.console_utils import ok, error, info

DEVICE_CONFIG_DEFAULT_SUBDIR = "config/hardware"


# =====================================================================================
#                                    Devices
# =====================================================================================
def _extract_device_ports(
    category: str, device_name: str, device_configuration: dict, path: str
) -> list[dict]:
    """Extracts port entries from a single device's configuration block.

    Handles both single-port devices (port key) and multi-port devices (ports key).
    Each entry in the returned list contains a name and port field.
    Raises ValueError if neither port nor ports is defined.
    """
    device_ports = []

    # Case 1: Device with single port
    if "port" in device_configuration:
        device_ports.append(
            {
                "name": f"{category}.{device_name}",
                "port": str(device_configuration["port"]),
            }
        )

    # Case 2: Device with multiple ports
    elif "ports" in device_configuration:
        ports_dict = device_configuration["ports"]

        for sub_type, port_data in ports_dict.items():
            if isinstance(port_data, list):
                for i, port in enumerate(port_data):
                    device_ports.append(
                        {
                            "name": f"{category}.{device_name}.{sub_type}_{i}",
                            "port": str(port),
                        }
                    )
            else:
                device_ports.append(
                    {
                        "name": f"{category}.{device_name}.{sub_type}",
                        "port": str(port_data),
                    }
                )

    else:
        print(
            error(
                f"Invalid configuration for '{category}.{device_name}': must define 'port' or 'ports'. File: {path}"
            )
        )
        raise ValueError(
            f"Invalid configuration for '{category}.{device_name}': "
            f"Must define 'port' or 'ports'. File: {path}"
        )

    return device_ports


def get_device_config(
    pkg_share: str, device_config_file: str, device_category: str, device_name: str
) -> dict:
    """Retrieves the configuration block for a specific device from the hardware config file.

    Navigates the devices.<category>.<name> hierarchy and validates each level is a dictionary.
    Raises ValueError if the category, device, or port definition is missing.
    """
    config = get_yaml_config_data(
        pkg_share,
        device_config_file,
        config_subdir=DEVICE_CONFIG_DEFAULT_SUBDIR,
    )
    config_path = get_file_path(
        pkg_share,
        device_config_file,
        config_subdir=DEVICE_CONFIG_DEFAULT_SUBDIR,
    )

    devices = config.get("devices", {})

    if not devices:
        print(error(f"No devices defined in {config_path}"))
        raise ValueError(f"No devices defined in {config_path}")
    ensure_is_dictionary(devices, "devices", config_path)

    device_section = devices.get(device_category)
    if device_section is None:
        print(error(f"Missing section 'devices.{device_category}' in {config_path}"))
        raise ValueError(
            f"Missing section 'devices.{device_category}' in {config_path}"
        )
    ensure_is_dictionary(device_section, f"devices.{device_category}", config_path)

    device_config = device_section.get(device_name)
    if device_config is None:
        print(
            error(
                f"Device '{device_name}' not found in 'devices.{device_category}' in {config_path}"
            )
        )
        raise ValueError(
            f"Device '{device_name}' not found in 'devices.{device_category}' within {config_path}"
        )
    ensure_is_dictionary(
        device_config, f"devices.{device_category}.{device_name}", config_path
    )

    print(ok(f"Device config resolved: 'devices.{device_category}.{device_name}'"))
    return device_config


def get_all_devices_ports(pkg_share: str, device_config_file: str) -> list[dict]:
    """Extracts port entries for every device defined in the hardware config file.

    Iterates all categories and devices under the devices key, returning a flat list
    of name/port pairs. Raises ValueError if no ports are found.
    """
    config = get_yaml_config_data(
        pkg_share,
        device_config_file,
        config_subdir=DEVICE_CONFIG_DEFAULT_SUBDIR,
    )
    config_path = get_file_path(
        pkg_share,
        device_config_file,
        config_subdir=DEVICE_CONFIG_DEFAULT_SUBDIR,
    )

    devices = config.get("devices", {})

    all_ports = []
    for category_name, category_content in devices.items():
        ensure_is_dictionary(category_content, f"devices.{category_name}", config_path)
        print(info(f"Scanning device category: '{category_name}'"))

        for device_name, device_configuration in category_content.items():
            ensure_is_dictionary(
                device_configuration,
                f"devices.{category_name}.{device_name}",
                config_path,
            )
            device_results = _extract_device_ports(
                category_name, device_name, device_configuration, config_path
            )
            all_ports.extend(device_results)

    if not all_ports:
        print(error(f"No device ports found in {config_path}"))
        raise ValueError(f"No device ports found in {config_path}")

    print(ok(f"Extracted {len(all_ports)} device port(s) from {config_path}"))
    return all_ports
