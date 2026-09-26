# ================
# Standard Library
# ================
import os

# ============
# ROS 2 Launch
# ============
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# =======================
# ROS 2 Package Utilities
# =======================
from ament_index_python.packages import get_package_share_directory

# ==============
# Micipsa Utils
# ==============
from micipsa_common.launch_utils import find_file
from utils.console.console_utils import error

# =========
# Constants
# =========
SIMULATION_PACKAGE_NAME = "micipsa_simulation"
ROBOT_NAME = "micipsa"
GZ_BRIDGE_FILENAME = "gz_bridge.yaml"
DEFAULT_SIMULATION_WORLD = "dock_area.world"


# =========================================================================
#                         Gazbo Simulation Launch
# =========================================================================
def launch_gazebo(log_level, headless, gazebo_world):
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                )
            ]
        ),
        launch_arguments={
            "gz_args": [
                # Map info to -v3, otherwise (warn/error) use -v1
                PythonExpression(
                    ["'-r -v3 ' if '", log_level, "' == 'info' else '-r -v1 '"]
                ),
                # Handle headless mode
                PythonExpression(["'-s ' if '", headless, "' == 'true' else ''"]),
                gazebo_world,
            ],
            "on_exit_shutdown": "true",
        }.items(),
    )

    return gazebo


# =========================================================================
#                               Robot Spawn
# =========================================================================
def spawn_entity(log_level, use_sim_time):
    pose = {
        "x": LaunchConfiguration("x_pose", default="0.00"),
        "y": LaunchConfiguration("y_pose", default="0.00"),
        "z": LaunchConfiguration("z_pose", default="0.2"),
        "R": LaunchConfiguration("roll", default="0.00"),
        "P": LaunchConfiguration("pitch", default="0.00"),
        "Y": LaunchConfiguration("yaw", default="0.00"),
    }

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            ROBOT_NAME,
            "-x",
            pose["x"],
            "-y",
            pose["y"],
            "-z",
            pose["z"],
            "-R",
            pose["R"],
            "-P",
            pose["P"],
            "-Y",
            pose["Y"],
            "--ros-args",
            "--log-level",
            log_level,
        ],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return spawn_entity


# =========================================================================
#                           GZ Bridge Launch
# =========================================================================
def launch_gz_bridge(log_level):
    bridge_params = os.path.join(
        get_package_share_directory(SIMULATION_PACKAGE_NAME),
        "config",
        GZ_BRIDGE_FILENAME,
    )

    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        parameters=[
            {"config_file": bridge_params},
            {
                "use_sim_time": True,
                # Scan
                "qos_overrides./scan.publisher.reliability": "best_effort",
                "qos_overrides./scan.publisher.durability": "volatile",
                "qos_overrides./scan.publisher.history": "keep_last",
                "qos_overrides./scan.publisher.depth": 10,
                # Pointcloud
                "qos_overrides./front_camera/depth/color/points.publisher.reliability": "best_effort",
                "qos_overrides./front_camera/depth/color/points.publisher.durability": "volatile",
                "qos_overrides./front_camera/depth/color/points.publisher.history": "keep_last",
                "qos_overrides./front_camera/depth/color/points.publisher.depth": 1,
            },
        ],
        arguments=["--ros-args", "--log-level", log_level],
    )

    return ros_gz_bridge


# =========================================================================
#                               Setup Launch
# =========================================================================
def setup_launch(context, *args, **kwargs):
    simulation_pkg_share = FindPackageShare(SIMULATION_PACKAGE_NAME).perform(context)

    # ================
    # Launch Arguments
    # ================
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    log_level = LaunchConfiguration("log_level").perform(context).strip()
    headless = LaunchConfiguration("headless")
    simulation_world_file = (
        LaunchConfiguration("simulation_world_file").perform(context).strip()
    )

    # =============================
    # Simulation World File Loading
    # =============================
    gazebo_world_path = find_file(
        simulation_pkg_share, simulation_world_file, file_subdir="resources/worlds"
    )
    if gazebo_world_path is None:
        print(
            error(
                f"Given Simulation World file not found, using default World: '{DEFAULT_SIMULATION_WORLD}'"
            )
        )
        gazebo_world_path = os.path.join(
            simulation_pkg_share, "resources/worlds", DEFAULT_SIMULATION_WORLD
        )

    gazebo_world = LaunchConfiguration(
        "gazebo_world",
        default=gazebo_world_path,
    )

    # =================
    # Gazebo Ressources
    # =================
    resources_path = os.path.join(
        get_package_share_directory(SIMULATION_PACKAGE_NAME), "resources"
    )
    set_gazebo_model_path_env = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", resources_path
    )

    # ================
    # Simulator Launch
    # ================
    gazebo_node = launch_gazebo(log_level, headless, gazebo_world)
    spawn_entity_node = spawn_entity(log_level, use_sim_time)
    gz_bridge_node = launch_gz_bridge(log_level)

    return [set_gazebo_model_path_env, gazebo_node, spawn_entity_node, gz_bridge_node]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "log_level",
                default_value="info",
                description="info, warn, error, debug",
            ),
            DeclareLaunchArgument(
                "headless",
                default_value="false",
                description='Set to "true" to run Gazebo headlessly',
            ),
            DeclareLaunchArgument(
                "simulation_world_file",
                default_value=DEFAULT_SIMULATION_WORLD,
                description="Name of the simulation world",
            ),
            OpaqueFunction(function=setup_launch),
        ]
    )
