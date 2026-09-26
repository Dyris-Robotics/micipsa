# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import subsection

# =========
# Constants
# =========
LOCALIZATION_PACKAGE_NAME = "micipsa_localization"


def setup_launch(context, *args, **kwargs):
    localization_pkg_share = FindPackageShare(LOCALIZATION_PACKAGE_NAME)

    # ================
    # Launch Arguments
    # ================
    deploy_mode = LaunchConfiguration("deploy_mode").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context)
    ekf_config_file = LaunchConfiguration("ekf_config_file").perform(context)

    # ===
    # EKF
    # ===
    ekf = GroupAction(
        actions=[
            LogInfo(msg=subsection("[📍 STARTING MICIPSA EKF]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            localization_pkg_share,
                            "launch",
                            "rl_ekf_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "log_level": log_level,
                    "ekf_config_file": ekf_config_file,
                }.items(),
            ),
        ],
    )

    # ===============
    # Madgwick Filter
    # ===============
    madgwick_imu_filter = GroupAction(
        actions=[
            LogInfo(msg=subsection("[🗃️ STARTING MICIPSA IMU MADGWICK FILTER]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            localization_pkg_share,
                            "launch",
                            "madgwick_filter_launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                }.items(),
            ),
        ],
        condition=IfCondition(deploy_mode),
    )

    return [ekf, madgwick_imu_filter]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "deploy_mode",
                description="Use real hardware if true, simulation if false",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "log_level",
                description="set to info, warn or error",
            ),
            DeclareLaunchArgument(
                "ekf_config_file",
                description="Config file name for ekf YAML file",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
