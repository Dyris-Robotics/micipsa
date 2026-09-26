# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

# =============
# Micipsa Utils
# =============
from micipsa_common.launch_utils import (
    resolve_config_path,
    find_file,
    find_package_share,
)
from utils.console.console_utils import warn, error

# =========
# Constants
# =========
NAVIGATION_PACKAGE_NAME = "micipsa_navigation"
BRINGUP_PACKAGE_NAME = "micipsa_bringup"
MAPS_PACKAGE_NAME = "micipsa_maps"
DEFAULT_CONFIG_FILE_NAME = "nav2_params.yaml"
DEFAULT_MAP_FILE_NAME = "mappy.yaml"
DEFAULT_DOCK_DATABASE_FILE_NAME = "dock_database.yaml"


def setup_launch(context, *args, **kwargs):
    navigation_pkg_share = find_package_share(NAVIGATION_PACKAGE_NAME, context)
    bringup_pkg_share = find_package_share(BRINGUP_PACKAGE_NAME, context)
    maps_pkg_share = find_package_share(MAPS_PACKAGE_NAME, context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    nav2_config_file = LaunchConfiguration("nav2_config_file").perform(context).strip()
    map_file = LaunchConfiguration("map_file").perform(context).strip()
    dock_database_file = LaunchConfiguration("dock_database").perform(context).strip()
    use_intra_process_comms = LaunchConfiguration("use_intra_process_comms")

    # ===================
    # Nav2 Config Loading
    # ===================
    config_path = resolve_config_path(
        nav2_config_file,
        bringup_pkg_share,
        navigation_pkg_share,
        bringup_config_subdir="config/navigation",
        calling_config_subdir="config",
    )
    if config_path is None:
        if navigation_pkg_share:
            print(
                warn(
                    f"Given Config file not found, using default config: '{DEFAULT_CONFIG_FILE_NAME}'"
                )
            )
            config_path = os.path.join(
                navigation_pkg_share, "config", DEFAULT_CONFIG_FILE_NAME
            )
        else:
            print(
                warn(
                    f"Cannot fall back to default config: '{NAVIGATION_PACKAGE_NAME}' package not found, skipping nav2 launch"
                )
            )
            return []

    # ================
    # Map File Loading
    # ================
    map_path = find_file(maps_pkg_share, map_file, file_subdir="maps")
    if map_path is None:
        print(
            error(
                f"Given map file not found, using default map: '{DEFAULT_MAP_FILE_NAME}'"
            )
        )
        map_path = os.path.join(maps_pkg_share, "maps", DEFAULT_MAP_FILE_NAME)

    # ==========================
    # Dock Database File Loading
    # ==========================
    dock_database_config_path = resolve_config_path(
        dock_database_file,
        bringup_pkg_share,
        navigation_pkg_share,
        bringup_config_subdir="config/navigation",
        calling_config_subdir="config",
    )
    if dock_database_config_path is None:
        print(
            warn(
                f"Given Config file not found, using default config: '{DEFAULT_DOCK_DATABASE_FILE_NAME}'"
            )
        )
        dock_database_config_path = os.path.join(
            navigation_pkg_share, "config", DEFAULT_DOCK_DATABASE_FILE_NAME
        )

    # ==========
    # Nav2 Stack
    # ==========
    nav2_container = ComposableNodeContainer(
        name="nav2_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container_isolated",
        output="screen",
        arguments=[
            "--ros-args",
            "--log-level",
            log_level,
            "--params-file",
            config_path,
        ],
        composable_node_descriptions=[
            ComposableNode(
                package="nav2_map_server",
                plugin="nav2_map_server::MapServer",
                name="map_server",
                parameters=[
                    config_path,
                    {"yaml_filename": map_path, "use_sim_time": use_sim_time},
                ],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_amcl",
                plugin="nav2_amcl::AmclNode",
                name="amcl",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_planner",
                plugin="nav2_planner::PlannerServer",
                name="planner_server",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_controller",
                plugin="nav2_controller::ControllerServer",
                name="controller_server",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_bt_navigator",
                plugin="nav2_bt_navigator::BtNavigator",
                name="bt_navigator",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_smoother",
                plugin="nav2_smoother::SmootherServer",
                name="smoother_server",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_behaviors",
                plugin="behavior_server::BehaviorServer",
                name="behavior_server",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_velocity_smoother",
                plugin="nav2_velocity_smoother::VelocitySmoother",
                name="velocity_smoother",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_collision_monitor",
                plugin="nav2_collision_monitor::CollisionMonitor",
                name="collision_monitor",
                parameters=[config_path, {"use_sim_time": use_sim_time}],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="opennav_docking",
                plugin="opennav_docking::DockingServer",
                name="docking_server",
                parameters=[
                    config_path,
                    {"use_sim_time": use_sim_time},
                    {"dock_database": dock_database_config_path},
                ],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
            ComposableNode(
                package="nav2_lifecycle_manager",
                plugin="nav2_lifecycle_manager::LifecycleManager",
                name="lifecycle_manager_navigation",
                parameters=[
                    {
                        "use_sim_time": use_sim_time,
                        "autostart": True,
                        "node_names": [
                            "map_server",
                            "amcl",
                            "planner_server",
                            "controller_server",
                            "bt_navigator",
                            "smoother_server",
                            "behavior_server",
                            "velocity_smoother",
                            "collision_monitor",
                            "docking_server",
                        ],
                    }
                ],
                extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            ),
        ],
    )

    launch_nav2 = GroupAction(actions=[nav2_container])

    return [launch_nav2]


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
            DeclareLaunchArgument(
                "nav2_config_file",
                default_value=DEFAULT_CONFIG_FILE_NAME,
                description="Name of the nav2 config file",
            ),
            DeclareLaunchArgument(
                "map_file",
                default_value=DEFAULT_MAP_FILE_NAME,
                description="Name of the map file",
            ),
            DeclareLaunchArgument(
                "dock_database",
                default_value=DEFAULT_DOCK_DATABASE_FILE_NAME,
                description="Name of the dock database file",
            ),
            DeclareLaunchArgument(
                "use_intra_process_comms",
                default_value="True",
                description="Enable zero-copy intra-process comms between composed nodes",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
