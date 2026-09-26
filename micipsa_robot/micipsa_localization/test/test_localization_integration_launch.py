import os
import unittest

import pytest
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node

from nav_msgs.msg import Odometry

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions

from typing import Any, Optional

# ======================================================================
# Integration Test: micipsa_localization (EKF) — State Estimation Stack
# ======================================================================
#
# Test Purpose
# ------------
# Validate that the localization pipeline initializes correctly in
# simulation and that the EKF publishes filtered odometry from the robot's
# controller output.
#
# This test ensures that the robot can:
#   - publish base odometry from the control stack
#   - start the robot_localization EKF node
#   - produce filtered odometry for downstream consumers
#
#
# System Scope
# ------------
# The test launches the following robot stack components:
#
#   micipsa_description
#       Robot model, URDF, and TF-related description
#
#   micipsa_simulation
#       Gazebo simulation environment
#
#   micipsa_control
#       ros2_control controllers publishing base odometry
#
#   micipsa_localization
#       robot_localization EKF node producing filtered odometry
#
#
# Test Dependencies
# -----------------
# The following subsystems must function correctly for this test to pass:
#
#   - Gazebo simulation
#   - robot description bringup
#   - ros2_control controllers
#   - base controller odometry publisher
#   - robot_localization EKF
#
# Required ROS interfaces:
#
#   Topics:
#       /micipsa_base_controller/odom
#       /odometry/filtered
#
#
# Success Criteria
# ----------------
# The test passes if:
#
#   1. Base controller odometry topic becomes available
#        /micipsa_base_controller/odom
#
#   2. EKF filtered odometry topic becomes available
#        /odometry/filtered
#
#   3. The EKF publishes a valid nav_msgs/Odometry message
#
#   4. The published filtered odometry contains valid frame information
#        header.frame_id != ""
#        child_frame_id != ""
#
#
# Failure Meaning
# ---------------
# If this test fails it may indicate:
#
#   - the base controller is not publishing odometry
#   - ros2_control controllers failed to start correctly
#   - robot_localization EKF failed to initialize
#   - the EKF is not receiving valid input data
#   - filtered odometry is not being published or is malformed
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

    return LaunchDescription(
        [
            description_launch,
            gazebo_launch,
            controllers_launch,
            localization_launch,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestLocalizationIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node: Node = rclpy.create_node("test_localization_integration")

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

    def test_localization_ekf_publishes_filtered_odom(self):
        self._wait_for_topic(
            "/micipsa_base_controller/odom",
            timeout_sec=90.0,
        )

        self._wait_for_topic(
            "/odometry/filtered",
            timeout_sec=90.0,
        )

        msg = self._wait_for_message(
            Odometry,
            "/odometry/filtered",
            timeout_sec=90.0,
        )

        self.assertIsInstance(msg, Odometry)
        self.assertNotEqual(
            msg.header.frame_id, "", "Filtered odometry has an empty header.frame_id"
        )
        self.assertNotEqual(
            msg.child_frame_id, "", "Filtered odometry has an empty child_frame_id"
        )
