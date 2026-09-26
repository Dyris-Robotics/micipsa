from utils.filesystem.file_utils import construct_file_path, is_file_available
from utils.console.console_utils import ok, warn

from launch_ros.substitutions import FindPackageShare


# =====================================================================================
#                         Launch File Config Resolution
# =====================================================================================
def find_file(pkg_share: str, file: str, file_subdir: str) -> str | None:
    """Returns the absolute path to a file if it exists, None otherwise.

    Does not raise on missing files, intended for optional existence checks.
    """
    file_path = construct_file_path(pkg_share, file, file_subdir)
    if is_file_available(file_path):
        return file_path
    return None


def resolve_config_path(
    config_file: str,
    bringup_pkg_share: str,
    calling_pkg_share: str,
    bringup_config_subdir: str,
    calling_config_subdir: str,
) -> str | None:
    """Resolves a config file path by searching the bringup package first, then the calling package.

    Returns the first match found, or None if the file is not present in either location.
    Logs which package the file was found in, or which packages it was missing from.
    """
    # Check in Bringup Package
    if bringup_pkg_share:
        config_path = find_file(bringup_pkg_share, config_file, bringup_config_subdir)
        if config_path is not None:
            print(ok(f"Config found in Bringup package: '{config_path}'"))
            return config_path
        print(warn(f"'{config_file}' not found in Bringup package"))

    # Check in Calling Package
    if calling_pkg_share:
        config_path = find_file(calling_pkg_share, config_file, calling_config_subdir)
        if config_path is not None:
            print(ok(f"Config found in Calling package: '{config_path}'"))
            return config_path
        print(warn(f"'{config_file}' not found in Calling package"))

    return None


# =====================================================================================
#                               Find ROS2 Package
# =====================================================================================
def find_package_share(package_name: str, context) -> str:
    try:
        pkg_share = FindPackageShare(package_name).perform(context)
        print(ok(f"Package share found for '{package_name}': '{pkg_share}'"))
        return pkg_share
    except Exception:
        print(warn(f"Package '{package_name}' not found"))
        return ""
