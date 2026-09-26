import os
import unittest

import pytest
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.client import Client

from ament_index_python.packages import get_package_share_directory
from controller_manager_msgs.srv import ListControllers
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions


# ======================================================================
# Integration Test: micipsa_control — Controller Bringup in Simulation
# ======================================================================
#
# Test Purpose
# ------------
# Validate that the ros2_control stack initializes correctly in simulation
# and that the expected controllers are loaded and activated by
# controller_manager.
#
# This test ensures that the robot can:
#   - start controller_manager through the simulation / ros2_control setup
#   - load the required runtime controllers
#   - activate the base motion controller
#   - expose the expected controller topics
#
#
# System Scope
# ------------
# The test launches the following robot stack components:
#
#   micipsa_description
#       Robot model, URDF, and ros2_control hardware/plugin description
#
#   micipsa_simulation
#       Gazebo simulation environment, expected to start controller_manager
#       through the ros2_control simulation plugin
#
#   micipsa_control
#       Controller bringup launch file responsible for spawning and
#       activating the required controllers
#
#
# Test Dependencies
# -----------------
# The following subsystems must function correctly for this test to pass:
#
#   - robot description bringup
#   - Gazebo simulation
#   - ros2_control Gazebo plugin
#   - controller_manager
#   - controller spawners in micipsa_control
#
# Required ROS interfaces:
#
#   Services:
#       /controller_manager/list_controllers
#
#   Controllers:
#       joint_state_broadcaster
#       micipsa_base_controller
#
#   Topics:
#       /micipsa_base_controller/cmd_vel
#       /micipsa_base_controller/odom
#
#
# Success Criteria
# ----------------
# The test passes if:
#
#   1. The controller_manager service becomes available
#        /controller_manager/list_controllers
#
#   2. The joint state broadcaster is present and reaches the active state
#        joint_state_broadcaster == "active"
#
#   3. The base controller is present and reaches the active state
#        micipsa_base_controller == "active"
#
#   4. The base controller publishes / exposes its expected topics
#        /micipsa_base_controller/cmd_vel
#        /micipsa_base_controller/odom
#
#
# Failure Meaning
# ---------------
# If this test fails it may indicate:
#
#   - Gazebo did not start the ros2_control plugin correctly
#   - controller_manager was not created
#   - controller spawners failed to load one or more controllers
#   - a controller remained unconfigured or inactive
#   - the base controller failed to expose its command or odometry topics
#
# ======================================================================


@pytest.mark.launch_test
def generate_test_description():
    # ----- micipsa_description bringup -----#
    desc_share = get_package_share_directory("micipsa_description")
    desc_launch_file = os.path.join(
        desc_share, "launch", "micipsa_description_launch.py"
    )

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(desc_launch_file),
        launch_arguments={
            "use_sim_time": "true",
            "deploy_mode": "false",
        }.items(),
    )

    # ----- micipsa_simulation bringup -----#
    gazebo_share = get_package_share_directory("micipsa_simulation")
    gazebo_launch_file = os.path.join(gazebo_share, "launch", "gazebo_launch.py")

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_file),
        launch_arguments={
            "use_sim_time": "true",
            "headless": "true",
        }.items(),
    )

    # ----- micipsa_control bringup -----#
    ctrl_share = get_package_share_directory("micipsa_control")
    controllers_launch_file = os.path.join(
        ctrl_share, "launch", "controllers_launch.py"
    )

    controllers_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(controllers_launch_file),
        launch_arguments={
            "use_sim_time": "true",
            "deploy_mode": "false",
        }.items(),
    )

    return LaunchDescription(
        [
            description_launch,
            gazebo_launch,
            controllers_launch,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestControllersIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node: Node = rclpy.create_node("test_controllers_integration")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _list_controllers(self, client: Client) -> dict:
        future = client.call_async(ListControllers.Request())
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=5.0)
        resp = future.result()
        if resp is None:
            return {}
        return {c.name: c for c in resp.controller}

    def _wait_for_controller_state(
        self,
        client: Client,
        *,
        name: str,
        desired_state: str,
        timeout_sec: float = 90.0,
    ) -> None:
        """
        Wait until a controller exists and reaches the desired lifecycle state.
        This avoids flakiness due to Gazebo/ros2_control startup and spawner timing.
        """
        end_time = self.node.get_clock().now() + Duration(seconds=timeout_sec)
        last_state = None
        last_names = []

        while self.node.get_clock().now() < end_time:
            by_name = self._list_controllers(client)
            last_names = sorted(by_name.keys())

            if name in by_name:
                last_state = by_name[name].state
                if last_state == desired_state:
                    return

            rclpy.spin_once(self.node, timeout_sec=0.5)

        self.fail(
            f"Controller '{name}' did not reach state '{desired_state}' within {timeout_sec}s. "
            f"Last state: {last_state}. Controllers seen: {last_names}"
        )

    def test_expected_controllers_loaded(self):
        client = self.node.create_client(
            ListControllers, "/controller_manager/list_controllers"
        )

        self.assertTrue(
            client.wait_for_service(timeout_sec=90.0),
            "Timed out waiting for /controller_manager/list_controllers. "
            "Gazebo ros2_control may not have started controller_manager.",
        )

        self._wait_for_controller_state(
            client,
            name="joint_state_broadcaster",
            desired_state="active",
            timeout_sec=90.0,
        )
        self._wait_for_controller_state(
            client,
            name="micipsa_base_controller",
            desired_state="active",
            timeout_sec=90.0,
        )

        topics = {name for name, _ in self.node.get_topic_names_and_types()}
        self.assertIn("/micipsa_base_controller/cmd_vel", topics)
        self.assertIn("/micipsa_base_controller/odom", topics)
