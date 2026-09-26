import os
import unittest

import pytest
import rclpy
from rclpy.action.client import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node

from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions

from typing import Any, Optional

# ======================================================================
# Integration Test: micipsa_navigation (Nav2) — Full Navigation Stack
# ======================================================================
#
# Test Purpose
# ------------
# Validate that the full navigation pipeline initializes correctly in
# simulation and that Nav2 exposes its primary interfaces required for
# autonomous navigation.
#
# This test ensures that the robot can:
#   - start the navigation stack
#   - expose the navigation action server
#   - generate both global and local costmaps
#
#
# System Scope
# ------------
# The test launches the full robot stack:
#
#   micipsa_description
#       Robot model, URDF, TF tree
#
#   micipsa_simulation
#       Gazebo simulation environment
#
#   micipsa_control
#       ros2_control controllers providing robot motion interfaces
#
#   micipsa_localization
#       robot_localization EKF producing filtered odometry
#
#   micipsa_slam
#       SLAM Toolbox generating a live map
#
#   micipsa_navigation
#       Nav2 stack (planner, controller, BT navigator, costmaps)
#
#
# Test Dependencies
# -----------------
# The following subsystems must function correctly for this test to pass:
#
#   - Gazebo simulation
#   - ros2_control controller manager
#   - robot_localization EKF
#   - SLAM Toolbox
#   - Nav2 lifecycle manager
#
# Required ROS interfaces:
#
#   Action Servers:
#       /navigate_to_pose
#
#   Topics:
#       /global_costmap/costmap
#       /local_costmap/costmap
#
#
# Success Criteria
# ----------------
# The test passes if:
#
#   1. Nav2 action server becomes available
#        /navigate_to_pose
#
#   2. Global and local costmap topics appear
#        /global_costmap/costmap
#        /local_costmap/costmap
#
#   3. Both costmaps publish valid nav_msgs/OccupancyGrid messages
#
#   4. Global costmap frame is correctly set to:
#        frame_id == "map"
#
#   5. Costmap metadata fields are valid
#        width >= 0
#        height >= 0
#
#
# Failure Meaning
# ---------------
# If this test fails it may indicate:
#
#   - Nav2 lifecycle nodes failed to activate
#   - TF tree required for navigation is invalid
#   - localization or SLAM is not producing map/odom data
#   - costmap plugins failed to initialize
#   - Nav2 action servers were not created
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

    # ----- micipsa_localization bringup -----#
    localization_share = get_package_share_directory("micipsa_localization")
    localization_launch_file = os.path.join(
        localization_share, "launch", "rl_ekf_launch.py"
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(localization_launch_file),
        launch_arguments={
            "use_sim_time": "true",
        }.items(),
    )

    # ----- micipsa_slam bringup -----#
    slam_share = get_package_share_directory("micipsa_slam")
    slam_launch_file = os.path.join(slam_share, "launch", "slam_toolbox_launch.py")

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_file),
        launch_arguments={
            "use_sim_time": "true",
        }.items(),
    )

    # ----- micipsa_navigation bringup -----#
    navigation_share = get_package_share_directory("micipsa_navigation")
    navigation_launch_file = os.path.join(navigation_share, "launch", "nav2_launch.py")

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(navigation_launch_file),
        launch_arguments={
            "use_sim_time": "true",
        }.items(),
    )

    return LaunchDescription(
        [
            description_launch,
            gazebo_launch,
            controllers_launch,
            localization_launch,
            slam_launch,
            navigation_launch,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestNavigationIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node: Node = rclpy.create_node("test_navigation_integration")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _wait_for_topic(
        self,
        topic_name: str,
        *,
        timeout_sec: float = 60.0,
    ) -> None:
        end_time = self.node.get_clock().now() + Duration(seconds=timeout_sec)

        while self.node.get_clock().now() < end_time:
            topics = {name for name, _ in self.node.get_topic_names_and_types()}
            if topic_name in topics:
                return
            rclpy.spin_once(self.node, timeout_sec=0.5)

        self.fail(f"Topic '{topic_name}' did not appear within {timeout_sec}s")

    def _wait_for_message(
        self,
        msg_type,
        topic_name: str,
        *,
        timeout_sec: float = 60.0,
    ):
        received: dict[str, Optional[Any]] = {"msg": None}

        def _callback(msg: Any) -> None:
            received["msg"] = msg

        sub = self.node.create_subscription(
            msg_type,
            topic_name,
            _callback,
            10,
        )

        try:
            end_time = self.node.get_clock().now() + Duration(seconds=timeout_sec)
            while self.node.get_clock().now() < end_time:
                if received["msg"] is not None:
                    return received["msg"]
                rclpy.spin_once(self.node, timeout_sec=0.5)

            self.fail(f"No message received on '{topic_name}' within {timeout_sec}s")
        finally:
            self.node.destroy_subscription(sub)

    def test_navigation_action_server_available(self):
        client = ActionClient(self.node, NavigateToPose, "/navigate_to_pose")

        try:
            self.assertTrue(
                client.wait_for_server(timeout_sec=120.0),
                "Timed out waiting for Nav2 action server '/navigate_to_pose'",
            )
        finally:
            client.destroy()

    def test_navigation_costmaps_publish(self):
        self._wait_for_topic("/global_costmap/costmap", timeout_sec=120.0)
        self._wait_for_topic("/local_costmap/costmap", timeout_sec=120.0)

        global_costmap = self._wait_for_message(
            OccupancyGrid,
            "/global_costmap/costmap",
            timeout_sec=120.0,
        )
        local_costmap = self._wait_for_message(
            OccupancyGrid,
            "/local_costmap/costmap",
            timeout_sec=120.0,
        )

        self.assertEqual(global_costmap.header.frame_id, "map")
        self.assertNotEqual(local_costmap.header.frame_id, "")

        self.assertGreaterEqual(global_costmap.info.width, 0)
        self.assertGreaterEqual(global_costmap.info.height, 0)
        self.assertGreaterEqual(local_costmap.info.width, 0)
        self.assertGreaterEqual(local_costmap.info.height, 0)
