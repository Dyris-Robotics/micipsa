import os
import unittest

import pytest
import rclpy
from rclpy.time import Time

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions

from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformListener
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy, ReliabilityPolicy
from rclpy.duration import Duration

# ======================================================================
# Integration Test: micipsa_description — URDF / TF Bringup
# ======================================================================
#
# Test Purpose
# ------------
# Validate that the robot description stack initializes correctly and that
# robot_state_publisher publishes the expected static transforms generated
# from the micipsa URDF / Xacro model.
#
# This test ensures that the robot can:
#   - generate a valid robot_description from the description package
#   - start robot_state_publisher successfully
#   - publish static TF data on /tf_static
#   - expose the expected static transforms between key robot frames
#
#
# System Scope
# ------------
# The test launches the following robot stack component:
#
#   micipsa_description
#       Robot model, URDF/Xacro processing, and robot_state_publisher
#
#
# Test Dependencies
# -----------------
# The following subsystems must function correctly for this test to pass:
#
#   - micipsa_description launch file
#   - URDF / Xacro model generation
#   - robot_state_publisher
#   - TF static transform publication
#
# Required ROS interfaces:
#
#   Topics:
#       /tf_static
#
#   TF Transforms:
#       base_footprint <- base_link
#       base_link <- laser_frame
#
#
# Success Criteria
# ----------------
# The test passes if:
#
#   1. robot_state_publisher starts successfully
#
#   2. At least one /tf_static message is published within the timeout
#
#   3. The expected static transforms are available
#        base_footprint <- base_link
#        base_link <- laser_frame
#
#
# Failure Meaning
# ---------------
# If this test fails it may indicate:
#
#   - the URDF / Xacro model could not be generated correctly
#   - robot_state_publisher failed to start
#   - static TF data is not being published
#   - the robot description is missing required links or joints
#   - expected frame names in the URDF do not match the test assumptions
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

    return LaunchDescription(
        [
            description_launch,
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestUrdfIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("test_urdf_integration")
        cls.tf_static_msgs = []

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        cls.sub = cls.node.create_subscription(
            TFMessage,
            "/tf_static",
            lambda msg: cls.tf_static_msgs.append(msg),
            qos,
        )

        cls.tf_buffer = Buffer()
        cls.tf_listener = TransformListener(cls.tf_buffer, cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

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

    def test_robot_state_publisher_publishes_tf_static(self):
        end_time = self.node.get_clock().now() + Duration(seconds=3.0)
        while not self.tf_static_msgs and self.node.get_clock().now() < end_time:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertGreater(
            len(self.tf_static_msgs), 0, "Expected at least one /tf_static message"
        )

    def test_expected_static_transforms_exist(self):
        self._wait_for_transform("base_footprint", "base_link", timeout_sec=3.0)
        self._wait_for_transform("base_link", "laser_frame", timeout_sec=3.0)
