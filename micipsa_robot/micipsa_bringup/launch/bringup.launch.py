# ==============
# Launch Imports
# ==============
from launch import LaunchDescription
from launch.action import Action
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# =============
# Micipsa Utils
# =============
from utils.console.console_utils import banner, title, section
from utils.conversions.data_conversion_utils import bool_to_str
from utils.filesystem.file_utils import get_yaml_config_data

# =========
# Constants
# =========
PACKAGE_NAME = "micipsa_bringup"
DEFAULT_CONFIG_FILE = "bringup_config.yaml"


def setup_launch(context, *args, **kwargs):
    pkg_share = FindPackageShare(PACKAGE_NAME).perform(context)

    # ================
    # Launch Arguments
    # ================
    bringup_config_filename = LaunchConfiguration("bringup_config_file").perform(
        context
    )

    # ==============
    # Config Loading
    # ==============
    config_data = get_yaml_config_data(
        pkg_share,
        bringup_config_filename,
        config_subdir="config",
    )
    bringup_settings = config_data.get("settings", {})

    # ======================================================================
    #                     Bringup Settings Pre-processing
    # ======================================================================
    # ======
    # Common
    # ======
    deploy_mode = bool_to_str(bringup_settings.get("deploy_mode"))
    use_sim_time = bool_to_str(bringup_settings.get("use_sim_time"))
    enable_perception = bool_to_str(bringup_settings.get("enable_perception"))
    enable_behavior = bool_to_str(bringup_settings.get("enable_behavior"))
    localization_mode = str(bringup_settings.get("localization_mode"))
    log_level = str(bringup_settings.get("log_level"))

    # ========
    # Hardware
    # ========
    devices_config_file = bringup_settings.get("devices_config_file")

    # =============
    # Camera driver
    # =============
    front_camera_config_file = str(bringup_settings.get("front_camera_config_file"))
    front_camera_device_name = str(bringup_settings.get("front_camera_device_name"))

    # ============
    # Lidar driver
    # ============
    base_lidar_config_file = str(bringup_settings.get("base_lidar_config_file"))
    base_lidar_device_name = str(bringup_settings.get("base_lidar_device_name"))

    # =========
    # Actuation
    # =========
    ros2_control_controllers_config_file = str(
        bringup_settings.get("ros2_control_controllers_config_file")
    )
    twist_mux_config_file = str(bringup_settings.get("twist_mux_config_file"))

    # ============
    # Localization
    # ============
    ekf_config_file = str(bringup_settings.get("ekf_config_file"))

    # ====
    # SLAM
    # ====
    slam_toolbox_config_file = str(bringup_settings.get("slam_toolbox_config_file"))
    map_saver_config_file = str(bringup_settings.get("map_saver_config_file"))

    # ==========
    # Navigation
    # ==========
    nav2_config_file = str(bringup_settings.get("nav2_config_file"))
    map_file = str(bringup_settings.get("map_file"))
    dock_database = str(bringup_settings.get("dock_database"))

    # ==========
    # Perception
    # ==========
    pointcloud_config_file = str(bringup_settings.get("pointcloud_config_file"))
    apriltags_config_file = str(bringup_settings.get("apriltags_config_file"))

    # ==========
    # Behavior
    # ==========
    behavior_config_file = str(bringup_settings.get("behavior_config_file"))

    # ==========
    # Simulation
    # ==========
    headless_sim = bool_to_str(bringup_settings.get("headless_sim"))
    simulation_world_file = str(bringup_settings.get("simulation_world_file"))

    actions: list[Action] = [
        LogInfo(msg=banner("🤖 MICIPSA ROBOT BRINGUP")),
        LogInfo(msg=title(f"Used Bringup Config: {bringup_config_filename}")),
    ]

    # ======================================================================
    #                       Layer 1: Hardware Layer
    # ======================================================================
    hardware_launch = GroupAction(
        actions=[
            LogInfo(msg=section("1", "[🔌 HARDWARE]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "hardware", "hardware.launch.py"]
                    )
                ),
                launch_arguments={
                    "devices_config_file": devices_config_file,
                }.items(),
            ),
        ],
        condition=IfCondition(deploy_mode),
    )

    # ======================================================================
    #                       Layer 2: Drivers Layer
    # ======================================================================
    drivers_launch = GroupAction(
        actions=[
            LogInfo(msg=section("2", "[📡 DRIVERS]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "drivers", "drivers.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "devices_config_file": devices_config_file,
                    "front_camera_config_file": front_camera_config_file,
                    "front_camera_device_name": front_camera_device_name,
                    "base_lidar_config_file": base_lidar_config_file,
                    "base_lidar_device_name": base_lidar_device_name,
                }.items(),
            ),
        ],
        condition=IfCondition(deploy_mode),
    )

    # ======================================================================
    #                       Layer 3: Description Layer
    # ======================================================================
    description_launch = GroupAction(
        actions=[
            LogInfo(msg=section("3", "[📖 DESCRIPTION]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "description", "description.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "deploy_mode": deploy_mode,
                    "use_sim_time": use_sim_time,
                    "devices_config_file": devices_config_file,
                    "controllers_config_file": ros2_control_controllers_config_file,
                }.items(),
            ),
        ],
    )

    # ======================================================================
    #                      Layer X: Simulation Layer
    # ======================================================================
    simulation_launch = GroupAction(
        actions=[
            LogInfo(msg=section("X", "[💻 SIMULATION]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "simulation", "simulation.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "headless": headless_sim,
                    "simulation_world_file": simulation_world_file,
                }.items(),
            ),
        ],
        condition=UnlessCondition(deploy_mode),
    )

    # ======================================================================
    #                       Layer 4: Actuation Layer
    # ======================================================================
    actuation_launch = GroupAction(
        actions=[
            LogInfo(msg=section("4", "[🛞 ACTUATION]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "actuation", "actuation.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "deploy_mode": deploy_mode,
                    "use_sim_time": use_sim_time,
                    "ros2_control_controllers_config_file": ros2_control_controllers_config_file,
                    "twist_mux_config_file": twist_mux_config_file,
                }.items(),
            ),
        ],
    )

    # ======================================================================
    #                       Layer 5: Localization Layer
    # ======================================================================
    localization_launch = GroupAction(
        actions=[
            LogInfo(msg=section("5", "[📍 Localization]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "localization", "localization.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "deploy_mode": deploy_mode,
                    "use_sim_time": use_sim_time,
                    "ekf_config_file": ekf_config_file,
                }.items(),
            ),
        ],
    )

    # ======================================================================
    #                         Layer 6: SLAM Layer
    # ======================================================================
    slam_launch = (
        GroupAction(
            actions=[
                LogInfo(msg=section("6", "[🗺️ SLAM]")),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution(
                            [pkg_share, "launch", "slam", "slam.launch.py"]
                        )
                    ),
                    launch_arguments={
                        "log_level": log_level,
                        "use_sim_time": use_sim_time,
                        "slam_toolbox_config_file": slam_toolbox_config_file,
                        "map_saver_config_file": map_saver_config_file,
                    }.items(),
                ),
            ],
        )
        if localization_mode == "mapping"
        else GroupAction(actions=[])
    )

    # ======================================================================
    #                       Layer 7: Navigation Layer
    # ======================================================================
    navigation_launch = (
        GroupAction(
            actions=[
                LogInfo(msg=section("7", "[🧭 Navigation]")),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution(
                            [pkg_share, "launch", "navigation", "navigation.launch.py"]
                        )
                    ),
                    launch_arguments={
                        "log_level": log_level,
                        "use_sim_time": use_sim_time,
                        "nav2_config_file": nav2_config_file,
                        "map_file": map_file,
                        "dock_database": dock_database,
                    }.items(),
                ),
            ],
        )
        if localization_mode == "localization"
        else GroupAction(actions=[])
    )

    # ======================================================================
    #                       Layer 8: Perception Layer
    # ======================================================================
    perception_launch = GroupAction(
        actions=[
            LogInfo(msg=section("8", "[📷 Perception]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "perception", "perception.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "use_sim_time": use_sim_time,
                    "pointcloud_config_file": pointcloud_config_file,
                    "apriltags_config_file": apriltags_config_file,
                }.items(),
            ),
        ],
        condition=IfCondition(enable_perception),
    )

    # ======================================================================
    #                       Layer 9: Behavior Layer
    # ======================================================================
    behavior_launch = GroupAction(
        actions=[
            LogInfo(msg=section("9", "[🌳 Behavior]")),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_share, "launch", "behavior", "behavior.launch.py"]
                    )
                ),
                launch_arguments={
                    "log_level": log_level,
                    "use_sim_time": use_sim_time,
                    "behavior_config_file": behavior_config_file,
                }.items(),
            ),
        ],
        condition=IfCondition(enable_behavior),
    )

    # Temporary solution for startup order
    T_HARDWARE = 0.0
    T_DRIVERS = 2.0
    T_DESCRIPTION = 4.0
    T_SIMULATION = 6.0
    T_ACTUATION = 15.0
    T_LOCALIZATION = 19.0
    T_SLAM = 22.0
    T_NAVIGATION = 26.0
    T_PERCEPTION = 30.0
    T_BEHAVIOR = 35.0

    actions.append(TimerAction(period=T_HARDWARE, actions=[hardware_launch]))
    actions.append(TimerAction(period=T_DRIVERS, actions=[drivers_launch]))
    actions.append(TimerAction(period=T_DESCRIPTION, actions=[description_launch]))
    actions.append(TimerAction(period=T_SIMULATION, actions=[simulation_launch]))
    actions.append(TimerAction(period=T_ACTUATION, actions=[actuation_launch]))
    actions.append(TimerAction(period=T_LOCALIZATION, actions=[localization_launch]))
    actions.append(TimerAction(period=T_SLAM, actions=[slam_launch]))
    actions.append(TimerAction(period=T_NAVIGATION, actions=[navigation_launch]))
    actions.append(TimerAction(period=T_PERCEPTION, actions=[perception_launch]))
    actions.append(TimerAction(period=T_BEHAVIOR, actions=[behavior_launch]))

    return actions


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "bringup_config_file",
                default_value=DEFAULT_CONFIG_FILE,
                description="Bringup config file for the robot stack",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
