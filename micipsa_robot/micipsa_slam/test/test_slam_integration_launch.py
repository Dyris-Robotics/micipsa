import os
import unittest
from typing import Any, Optional

import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions
from nav_msgs.msg import OccupancyGrid
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

# ======================================================================
# Integration Test: micipsa_slam (SLAM Toolbox) — Mapping Stack
# ======================================================================
#
# Test Purpose
# ------------
# Validate that the SLAM pipeline initializes correctly in simulation and
# that SLAM Toolbox produces a map from the robot's sensor and transform
# data.
#
# This test ensures that the robot can:
#   - publish laser scan data required for SLAM
#   - provide the TF transforms required by the mapping pipeline
#   - generate and publish a map
#
#
# System Scope
# ------------
# The test launches the following robot stack components:
#
#   micipsa_description
#       Robot model, URDF, and static TF structure
#
#   micipsa_simulation
#       Gazebo simulation environment
#
#   micipsa_control
#       ros2_control controllers providing robot motion interfaces
#
#   micipsa_localization
#       robot_localization EKF providing odometry estimation
#
#   micipsa_slam
#       SLAM Toolbox node generating a live occupancy grid map
#
#
# Test Dependencies
# -----------------
# The following subsystems must function correctly for this test to pass:
#
#   - Gazebo simulation
#   - robot description and TF publishers
#   - ros2_control controllers
#   - LiDAR / scan topic publisher
#   - robot_localization EKF
#   - SLAM Toolbox
#
# Required ROS interfaces:
#
#   Topics:
#       /scan
#       /tf
#       /map
#
#   TF Transforms:
#       base_footprint <- laser_frame
#       odom <- base_footprint
#
#
# Success Criteria
# ----------------
# The test passes if:
#
#   1. Required input topics become available
#        /scan
#        /tf
#
#   2. SLAM output topic becomes available
#        /map
#
#   3. Required TF transforms are available
#        base_footprint <- laser_frame
#        odom <- base_footprint
#
#   4. A valid nav_msgs/OccupancyGrid message is published on /map
#
#   5. The published map uses the correct global frame
#        header.frame_id == "map"
#
#
# Failure Meaning
# ---------------
# If this test fails it may indicate:
#
#   - the LiDAR scan topic is not being published
#   - required TF transforms are missing or delayed
#   - robot_localization is not providing usable odometry
#   - SLAM Toolbox failed to initialize or activate
#   - the mapping pipeline is not producing a map
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

    return LaunchDescription(
        [
            description_launch,
            gazebo_launch,
            controllers_launch,
            localization_launch,
            slam_launch,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestSlamIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node: Node = rclpy.create_node("test_slam_integration")
        cls.tf_buffer = Buffer()
        cls.tf_listener = TransformListener(cls.tf_buffer, cls.node)

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

    def _wait_for_transform(
        self,
        target_frame: str,
        source_frame: str,
        *,
        timeout_sec: float = 3.0,
    ) -> None:
        end_time = self.node.get_clock().now() + Duration(seconds=timeout_sec)

        while self.node.get_clock().now() < end_time:
            if self.tf_buffer.can_transform(
                target_frame,
                source_frame,
                Time(),
                timeout=Duration(seconds=0.1),
            ):
                return
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.fail(
            f"Transform '{target_frame} <- {source_frame}' not available within {timeout_sec}s"
        )

    def test_slam_publishes_map(self):
        self._wait_for_topic("/scan", timeout_sec=90.0)
        self._wait_for_topic("/tf", timeout_sec=90.0)
        self._wait_for_topic("/map", timeout_sec=120.0)

        self._wait_for_transform("base_footprint", "laser_frame", timeout_sec=90.0)
        self._wait_for_transform("odom", "base_footprint", timeout_sec=90.0)

        msg = self._wait_for_message(OccupancyGrid, "/map", timeout_sec=120.0)
        self.assertEqual(msg.header.frame_id, "map")
