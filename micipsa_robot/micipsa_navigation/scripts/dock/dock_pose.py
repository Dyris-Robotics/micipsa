#!/usr/bin/env python3

# ==============
# ROS2
# ==============
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult

# =============
# ROS2 Messages
# =============
from geometry_msgs.msg import PoseStamped

# ====================
# Custom ROS2 Messages
# ====================
from micipsa_msgs.msg import AprilTagPose, AprilTagPoseArray


class DockPose(Node):
    def __init__(self) -> None:
        super().__init__("dock_pose_node")

        self.get_logger().info(f"Initializing node '{self.get_name()}'")

        # ======
        # Params
        # ======
        self.declare_parameter("dock_frame", "home_dock")
        self.dock_frame_: str = (
            self.get_parameter("dock_frame").get_parameter_value().string_value
        )
        self.add_on_set_parameters_callback(self._on_set_parameters)

        # ========================
        # Publishers / Subscribers
        # ========================
        self.sub_ = self.create_subscription(
            AprilTagPoseArray,
            "/detected_apriltags_poses",
            self._on_detections,
            10,
        )

        self.pub_ = self.create_publisher(
            PoseStamped,
            "/detected_dock_pose",
            1,
        )

        self._log_configuration()

    # ============================================================================
    #                         Parameter Update Callback
    # ============================================================================
    def _on_set_parameters(self, params) -> SetParametersResult:
        for param in params:
            if param.name == "dock_frame":
                self.dock_frame_ = param.value

                self.get_logger().info(f"Updated dock frame to '{self.dock_frame_}'")

        return SetParametersResult(successful=True)

    # ============================================================================
    #                          Dock Pose Publishing
    # ============================================================================
    def _publish_dock_pose(self, tag: AprilTagPose) -> None:
        dock_pose = PoseStamped()
        dock_pose.header = tag.header
        dock_pose.pose = tag.pose
        self.pub_.publish(dock_pose)

        self.get_logger().debug(f"Published dock pose for frame '{self.dock_frame_}'")

    # ============================================================================
    #                          Dock Frame Check
    # ============================================================================
    def _is_dock_frame(self, tag_frame: str) -> bool:
        if tag_frame != self.dock_frame_:
            return False
        return True

    # ============================================================================
    #                        AprilTags Detection Callback
    # ============================================================================
    def _on_detections(self, msg: AprilTagPoseArray) -> None:
        self.get_logger().debug(f"Received {len(msg.tag_poses)} tag(s)")

        for tag in msg.tag_poses:
            if self._is_dock_frame(tag.frame):
                self.get_logger().debug(f"Detected dock frame '{self.dock_frame_}'")
                self._publish_dock_pose(tag)
                return

    # ============================================================================
    #                          Logging Configuration
    # ============================================================================
    def _log_configuration(self) -> None:
        self.get_logger().info(f"Configured dock frame: '{self.dock_frame_}'")


# ============================================================================
#                                   Main
# ============================================================================
def main(args=None) -> None:
    rclpy.init(args=args)

    node = DockPose()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info("Shutdown requested by user")

    finally:
        node.get_logger().info(f"Shutting down node '{node.get_name()}'")

        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
