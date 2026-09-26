#ifndef MICIPSA_PERCEPTION__POINTCLOUD__POINTCLOUD_NODE_HPP_
#define MICIPSA_PERCEPTION__POINTCLOUD__POINTCLOUD_NODE_HPP_

#include <unordered_set>

#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/transform_listener.h>

#include <pcl_conversions/pcl_conversions.h>
#include <memory>

#include <pcl_ros/transforms.hpp>
#include <string>
#include "micipsa_perception/pointcloud/pointcloud_processor.h"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "visualization_msgs/msg/marker.hpp"

#include <pcl/common/transforms.h>
#include <tf2_eigen/tf2_eigen.hpp>

static constexpr int DEFAULT_TF_LOOKUP_TIMEOUT = 3;

class PointCloudNode : public rclcpp::Node {
 public:
    PointCloudNode();

 private:
    // ============================================
    //               Class Members
    // ============================================
    std::string pointcloud_sensor_name_;
    std::string pointcloud_input_topic_;
    std::string pointcloud_output_topic_;
    std::string pointcloud_world_frame_;

    rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr pointcloud_subscriber_;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr voxel_publisher_;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr crop_publisher_;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr sor_publisher_;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr no_ground_publisher_;

    std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

    rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr params_callback_;

    PointCloudProcessor processor_;

    // =====================================
    //         Pointcloud Callback
    // =====================================
    void pointcloud_callback(const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg);

    // ===============================================
    //         Pointcloud Helpers Functions
    // ===============================================
    pcl::PointCloud<pcl::PointXYZI>::Ptr convert_ros_to_pcl(
            const sensor_msgs::msg::PointCloud2::ConstSharedPtr &msg);

    bool lookup_transform(const sensor_msgs::msg::PointCloud2::ConstSharedPtr &msg,
                          Eigen::Matrix4f &out);

    void publish_results(const PcProcessingResult &result, const rclcpp::Time &stamp);

    void publish_cloud(rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr &pub,
                       const pcl::PointCloud<pcl::PointXYZI> &cloud,
                       const rclcpp::Time &stamp);

    // ==============================================================
    //         Pointcloud Parameters Initialization & Update
    // ==============================================================
    void declare_params();
    PcProcessingParams load_params();
    rcl_interfaces::msg::SetParametersResult params_callback(
            const std::vector<rclcpp::Parameter> &parameters);

    bool update_crop_param(const rclcpp::Parameter &param,
                           PcProcessingParams &params,
                           std::string &reason);

    bool update_voxel_param(const rclcpp::Parameter &param,
                            PcProcessingParams &params,
                            std::string &reason);

    bool update_sor_param(const rclcpp::Parameter &param,
                          PcProcessingParams &params,
                          std::string &reason);

    bool update_plane_param(const rclcpp::Parameter &param,
                            PcProcessingParams &params,
                            std::string &reason);
};

#endif  // MICIPSA_PERCEPTION__POINTCLOUD__POINTCLOUD_NODE_HPP_