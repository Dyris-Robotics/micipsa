#!/usr/bin/env python3

# ==============
# Python
# ==============
import yaml

# ==============
# ROS2
# ==============
import rclpy
from rclpy.node import Node
from tf2_ros import (
    Buffer,
    TransformListener,
    LookupException,
    ConnectivityException,
    ExtrapolationException,
)

# =============
# ROS2 Messages
# =============
from apriltag_msgs.msg import AprilTagDetectionArray

# ====================
# Custom ROS2 Messages
# ====================
from micipsa_msgs.msg import AprilTagPose, AprilTagPoseArray


class AprilTagPoses(Node):
    def __init__(self) -> None:
        super().__init__("apriltag_poses")

        self.get_logger().info(f"Initializing node '{self.get_name()}'")

        # ======
        # Params
        # ======
        self.declare_parameter("config_file", "")
        self.declare_parameter("target_frame", "odom")
        config_file: str = (
            self.get_parameter("config_file").get_parameter_value().string_value
        )
        self.target_frame_: str = (
            self.get_parameter("target_frame").get_parameter_value().string_value
        )

        # ==
        # TF
        # ==
        self.tf_buffer_ = Buffer()
        self.tf_listener_ = TransformListener(self.tf_buffer_, self)

        # ========================
        # Publishers / Subscribers
        # ========================
        self.sub_ = self.create_subscription(
            AprilTagDetectionArray,
            "/detections",
            self._on_detections,
            10,
        )

        self.pub_ = self.create_publisher(
            AprilTagPoseArray,
            "/detected_apriltags_poses",
            10,
        )

        self.tag_map_: dict[int, str] = self._load_tag_map(config_file)
        self._log_configuration()

    # ============================================================================
    #                  AprilTags Transform To Target Frame
    # ============================================================================
    def _transform_tag_to_target_frame(self, tag_id: int, source_frame: str):
        try:
            return self.tf_buffer_.lookup_transform(
                self.target_frame_,
                source_frame,
                rclpy.time.Time(),
            )

        except (
            LookupException,
            ConnectivityException,
            ExtrapolationException,
        ) as e:
            self.get_logger().warn(
                f"Failed to lookup transform "
                f"'{source_frame}' -> '{self.target_frame_}' "
                f"for tag id={tag_id}: {e}",
                throttle_duration_sec=2.0,
            )

            return None

    # ============================================================================
    #                           AprilTags Pose Creation
    # ============================================================================
    def _create_tag_pose(
        self, tag_id: int, source_frame: str, transform
    ) -> AprilTagPose:
        msg = AprilTagPose()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.target_frame_

        msg.tag_id = tag_id
        msg.frame = source_frame

        msg.pose.position.x = transform.transform.translation.x
        msg.pose.position.y = transform.transform.translation.y
        msg.pose.position.z = transform.transform.translation.z

        msg.pose.orientation = transform.transform.rotation

        return msg

    # ============================================================================
    #                           AprilTags Check
    # ============================================================================
    def _is_known_tag(self, tag_id: int, source_frame: str) -> bool:
        if not source_frame:  # Checks if the string is empty ""
            self.get_logger().warn(
                f"Received detection for unknown tag id={tag_id}",
                throttle_duration_sec=5.0,
            )
            return False
        return True

    # ============================================================================
    #                       AprilTags Detection Publishing
    # ============================================================================
    def _publish_tag_poses(self, detections: list[AprilTagPose]):
        if detections:
            tag_poses_array = AprilTagPoseArray()
            tag_poses_array.header.stamp = self.get_clock().now().to_msg()
            tag_poses_array.header.frame_id = self.target_frame_
            tag_poses_array.tag_poses = detections

            self.pub_.publish(tag_poses_array)

            self.get_logger().debug(
                f"Published {len(detections)} transformed AprilTag pose(s)"
            )

    # ============================================================================
    #                       Apriltags Detection Callback
    # ============================================================================
    def _on_detections(self, msg: AprilTagDetectionArray) -> None:
        self.get_logger().debug(f"Received {len(msg.detections)} detection(s)")

        new_detections: list[AprilTagPose] = []

        for tag in msg.detections:
            tag_id: int = tag.id
            source_frame: str = self.tag_map_.get(tag_id, "")

            if not self._is_known_tag(tag_id, source_frame):
                continue

            assert source_frame is not None
            transform = self._transform_tag_to_target_frame(
                tag_id=tag_id,
                source_frame=source_frame,
            )

            if transform is None:
                continue

            new_detections.append(
                self._create_tag_pose(
                    tag_id=tag_id,
                    source_frame=source_frame,
                    transform=transform,
                )
            )

        self._publish_tag_poses(new_detections)

    # ============================================================================
    #                         Apriltags Config Load
    # ============================================================================
    def _load_tag_map(self, config_file: str) -> dict[int, str]:
        """Parse tag.ids and tag.frames directly from the apriltag yaml."""

        if not config_file:
            self.get_logger().error(
                "Parameter 'config_file' is empty. No tag mappings loaded."
            )
            return {}

        try:
            with open(config_file, "r") as f:
                data = yaml.safe_load(f)

        except FileNotFoundError:
            self.get_logger().error(f"Config file not found: '{config_file}'")
            return {}

        except yaml.YAMLError as e:
            self.get_logger().error(
                f"Failed to parse YAML config file '{config_file}': {e}"
            )
            return {}

        try:
            tag_cfg = data["apriltag"]["ros__parameters"]["tag"]
            ids: list[int] = tag_cfg["ids"]
            frames: list[str] = tag_cfg["frames"]

        except KeyError as e:
            self.get_logger().error(f"Missing required configuration key: {e}")
            return {}

        if len(ids) != len(frames):
            self.get_logger().warn(
                f"tag.ids length ({len(ids)}) does not match "
                f"tag.frames length ({len(frames)}). "
                f"Using shortest list."
            )

        tag_map = dict(zip(ids, frames))

        self.get_logger().info(
            f"Loaded {len(tag_map)} tag mappings from '{config_file}'"
        )

        return tag_map

    # ============================================================================
    #                          Logging Configuration
    # ============================================================================
    def _log_configuration(self) -> None:
        self.get_logger().info(f"Target frame: '{self.target_frame_}'")

        if not self.tag_map_:
            self.get_logger().warn("No AprilTag frame mappings configured.")
            return

        self.get_logger().info(
            f"Configured {len(self.tag_map_)} AprilTag frame mappings."
        )

        for tag_id, frame in self.tag_map_.items():
            self.get_logger().debug(f"Configured tag id={tag_id} -> frame='{frame}'")


# ============================================================================
#                                   Main
# ============================================================================
def main(args=None) -> None:
    rclpy.init(args=args)

    node = AprilTagPoses()

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
