#include "micipsa_perception/pointcloud/pointcloud_node.h"

#include <tf2_sensor_msgs/tf2_sensor_msgs.hpp>

// =====================================
//           Constructor
// =====================================
PointCloudNode::PointCloudNode() : Node("pointcloud_node") {
    // Params Initizalization
    declare_params();
    PcProcessingParams pointcloud_params = load_params();
    processor_.update_params(pointcloud_params);

    // QOS
    auto qos = rclcpp::QoS(rclcpp::KeepLast(1)).best_effort().durability_volatile();

    // Publishers
    const std::string topic_base_name = pointcloud_sensor_name_ + "/pointcloud";
    voxel_publisher_ =
            create_publisher<sensor_msgs::msg::PointCloud2>(topic_base_name + "/voxel", qos);
    crop_publisher_ =
            create_publisher<sensor_msgs::msg::PointCloud2>(topic_base_name + "/cropped", qos);
    sor_publisher_ = create_publisher<sensor_msgs::msg::PointCloud2>(topic_base_name + "/sor", qos);
    no_ground_publisher_ =
            create_publisher<sensor_msgs::msg::PointCloud2>(topic_base_name + "/no_ground", qos);

    // Subscribers
    pointcloud_subscriber_ = create_subscription<sensor_msgs::msg::PointCloud2>(
            pointcloud_input_topic_,
            qos,
            std::bind(&PointCloudNode::pointcloud_callback, this, std::placeholders::_1));

    // TF
    tf_buffer_ = std::make_unique<tf2_ros::Buffer>(get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

    params_callback_ = add_on_set_parameters_callback(
            std::bind(&PointCloudNode::params_callback, this, std::placeholders::_1));

    RCLCPP_INFO(get_logger(), "PointCloud Node Ready");
}

// =====================================
//         Pointcloud Callback
// =====================================
void PointCloudNode::pointcloud_callback(const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) {
    if (voxel_publisher_->get_subscription_count() == 0 &&
        crop_publisher_->get_subscription_count() == 0 &&
        sor_publisher_->get_subscription_count() == 0 &&
        no_ground_publisher_->get_subscription_count() == 0) {
        return;
    }

    auto input = convert_ros_to_pcl(msg);

    Eigen::Matrix4f transform;
    if (!lookup_transform(msg, transform)) {
        return;
    }

    const auto result = processor_.process(input, transform);

    publish_results(result, msg->header.stamp);
}

// ===============================================
//         Pointcloud Helpers Functions
// ===============================================
pcl::PointCloud<pcl::PointXYZI>::Ptr PointCloudNode::convert_ros_to_pcl(
        const sensor_msgs::msg::PointCloud2::ConstSharedPtr &msg) {
    pcl::console::setVerbosityLevel(pcl::console::L_ALWAYS);

    auto cloud = std::make_shared<pcl::PointCloud<pcl::PointXYZI>>();
    pcl::fromROSMsg(*msg, *cloud);

    pcl::console::setVerbosityLevel(pcl::console::L_INFO);
    return cloud;
}

bool PointCloudNode::lookup_transform(const sensor_msgs::msg::PointCloud2::ConstSharedPtr &msg,
                                      Eigen::Matrix4f &out) {
    try {
        auto tf = tf_buffer_->lookupTransform(pointcloud_world_frame_,
                                              msg->header.frame_id,
                                              tf2::TimePointZero,
                                              tf2::durationFromSec(DEFAULT_TF_LOOKUP_TIMEOUT));

        out = tf2::transformToEigen(tf).matrix().cast<float>();
        return true;

    } catch (const tf2::TransformException &ex) {
        RCLCPP_ERROR(get_logger(), "TF lookup failed: %s", ex.what());
        return false;
    }
}

void PointCloudNode::publish_results(const PcProcessingResult &result, const rclcpp::Time &stamp) {
    if (voxel_publisher_->get_subscription_count() > 0) {
        publish_cloud(voxel_publisher_, *result.voxel_filtered, stamp);
    }

    if (crop_publisher_->get_subscription_count() > 0) {
        publish_cloud(crop_publisher_, *result.cropped, stamp);
    }

    if (sor_publisher_->get_subscription_count() > 0) {
        publish_cloud(sor_publisher_, *result.sor_filtered, stamp);
    }

    if (no_ground_publisher_->get_subscription_count() > 0) {
        publish_cloud(no_ground_publisher_, *result.no_ground, stamp);
    }
}

void PointCloudNode::publish_cloud(rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr &pub,
                                   const pcl::PointCloud<pcl::PointXYZI> &cloud,
                                   const rclcpp::Time &stamp) {
    sensor_msgs::msg::PointCloud2 ros_cloud;
    pcl::toROSMsg(cloud, ros_cloud);
    ros_cloud.header.stamp = stamp;
    ros_cloud.header.frame_id = pointcloud_world_frame_;
    pub->publish(ros_cloud);
}

// ==============================================================
//         Pointcloud Parameters Initialization & Update
// ==============================================================
void PointCloudNode::declare_params() {
    const PcProcessingParams default_params;

    // Input / output
    declare_parameter("pointcloud_sensor_name", std::string("unknown_pointcloud_sensor"));
    declare_parameter("pointcloud_input_topic", std::string("/camera/depth/color/points"));
    declare_parameter("pointcloud_world_frame", std::string("map"));
    declare_parameter("pointcloud_is_3d", default_params.is_3d);

    // Voxel Grid
    declare_parameter("voxel_leaf_size", static_cast<double>(default_params.voxel_leaf_size));

    // Crop Box
    declare_parameter("x_crop_min", static_cast<double>(default_params.x_crop_min));
    declare_parameter("x_crop_max", static_cast<double>(default_params.x_crop_max));
    declare_parameter("y_crop_min", static_cast<double>(default_params.y_crop_min));
    declare_parameter("y_crop_max", static_cast<double>(default_params.y_crop_max));
    declare_parameter("z_crop_min", static_cast<double>(default_params.z_crop_min));
    declare_parameter("z_crop_max", static_cast<double>(default_params.z_crop_max));

    // SOR
    declare_parameter("sor_mean_k", default_params.sor_mean_k);
    declare_parameter("sor_stddev_multhresh",
                      static_cast<double>(default_params.sor_stddev_multhresh));

    // Plane Segmentation
    declare_parameter("plane_axis", default_params.plane_axis);
    declare_parameter("eps_angle", static_cast<double>(default_params.eps_angle));
    declare_parameter("optimize_coefficients", default_params.optimize_coefficients);
    declare_parameter("model_type", default_params.model_type);
    declare_parameter("method_type", default_params.method_type);
    declare_parameter("plane_max_iterations", default_params.plane_max_iterations);
    declare_parameter("plane_distance_threshold",
                      static_cast<double>(default_params.plane_distance_threshold));
}

PcProcessingParams PointCloudNode::load_params() {
    PcProcessingParams pointcloud_params;

    // Input / output
    pointcloud_sensor_name_ = get_parameter("pointcloud_sensor_name").as_string();
    pointcloud_input_topic_ = get_parameter("pointcloud_input_topic").as_string();
    pointcloud_world_frame_ = get_parameter("pointcloud_world_frame").as_string();
    pointcloud_params.is_3d = get_parameter("pointcloud_is_3d").as_bool();

    // Voxel Grid
    pointcloud_params.voxel_leaf_size =
            static_cast<float>(get_parameter("voxel_leaf_size").as_double());

    // Crop Box
    pointcloud_params.x_crop_min = static_cast<float>(get_parameter("x_crop_min").as_double());
    pointcloud_params.x_crop_max = static_cast<float>(get_parameter("x_crop_max").as_double());
    pointcloud_params.y_crop_min = static_cast<float>(get_parameter("y_crop_min").as_double());
    pointcloud_params.y_crop_max = static_cast<float>(get_parameter("y_crop_max").as_double());
    pointcloud_params.z_crop_min = static_cast<float>(get_parameter("z_crop_min").as_double());
    pointcloud_params.z_crop_max = static_cast<float>(get_parameter("z_crop_max").as_double());

    // SOR
    pointcloud_params.sor_mean_k = static_cast<int>(get_parameter("sor_mean_k").as_int());
    pointcloud_params.sor_stddev_multhresh =
            static_cast<float>(get_parameter("sor_stddev_multhresh").as_double());

    // Plane Segmentation
    pointcloud_params.plane_axis = get_parameter("plane_axis").as_string();
    pointcloud_params.eps_angle = static_cast<float>(get_parameter("eps_angle").as_double());
    pointcloud_params.optimize_coefficients = get_parameter("optimize_coefficients").as_bool();
    pointcloud_params.model_type = get_parameter("model_type").as_string();
    pointcloud_params.method_type = get_parameter("method_type").as_string();
    pointcloud_params.plane_max_iterations =
            static_cast<int>(get_parameter("plane_max_iterations").as_int());
    pointcloud_params.plane_distance_threshold =
            static_cast<float>(get_parameter("plane_distance_threshold").as_double());
    return pointcloud_params;
}

rcl_interfaces::msg::SetParametersResult PointCloudNode::params_callback(
        const std::vector<rclcpp::Parameter> &parameters) {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;

    PcProcessingParams updated_params = processor_.params();

    for (const auto &param : parameters) {
        const auto &name = param.get_name();

        bool success = false;

        if (name == "pointcloud_is_3d") {
            updated_params.is_3d = param.as_bool();
            continue;
        }

        success = update_crop_param(param, updated_params, result.reason) ||
                  update_voxel_param(param, updated_params, result.reason) ||
                  update_sor_param(param, updated_params, result.reason) ||
                  update_plane_param(param, updated_params, result.reason);

        if (!success && !result.reason.empty()) {
            result.successful = false;
            return result;
        }
    }

    processor_.update_params(updated_params);

    return result;
}

bool PointCloudNode::update_crop_param(const rclcpp::Parameter &param,
                                       PcProcessingParams &params,
                                       std::string &reason) {
    const auto &name = param.get_name();
    const float value = static_cast<float>(param.as_double());

    if (name == "x_crop_min") {
        if (value >= params.x_crop_max) {
            reason = "x_crop_min must be < x_crop_max";
            return false;
        }

        params.x_crop_min = value;
        return true;
    }

    if (name == "x_crop_max") {
        if (value <= params.x_crop_min) {
            reason = "x_crop_max must be > x_crop_min";
            return false;
        }

        params.x_crop_max = value;
        return true;
    }

    if (name == "y_crop_min") {
        if (value >= params.y_crop_max) {
            reason = "y_crop_min must be < y_crop_max";
            return false;
        }

        params.y_crop_min = value;
        return true;
    }

    if (name == "y_crop_max") {
        if (value <= params.y_crop_min) {
            reason = "y_crop_max must be > y_crop_min";
            return false;
        }

        params.y_crop_max = value;
        return true;
    }

    if (name == "z_crop_min") {
        if (value >= params.z_crop_max) {
            reason = "z_crop_min must be < z_crop_max";
            return false;
        }

        params.z_crop_min = value;
        return true;
    }

    if (name == "z_crop_max") {
        if (value <= params.z_crop_min) {
            reason = "z_crop_max must be > z_crop_min";
            return false;
        }

        params.z_crop_max = value;
        return true;
    }

    return false;
}

bool PointCloudNode::update_voxel_param(const rclcpp::Parameter &param,
                                        PcProcessingParams &params,
                                        std::string &reason) {
    if (param.get_name() != "voxel_leaf_size") {
        return false;
    }

    if (param.as_double() <= 0.0) {
        reason = "voxel_leaf_size must be > 0";
        return false;
    }

    params.voxel_leaf_size = static_cast<float>(param.as_double());

    return true;
}

bool PointCloudNode::update_sor_param(const rclcpp::Parameter &param,
                                      PcProcessingParams &params,
                                      std::string &reason) {
    const auto &name = param.get_name();

    if (name == "sor_mean_k") {
        if (param.as_int() <= 0) {
            reason = "sor_mean_k must be > 0";
            return false;
        }

        params.sor_mean_k = param.as_int();
        return true;
    }

    if (name == "sor_stddev_multhresh") {
        if (param.as_double() <= 0.0) {
            reason = "sor_stddev_multhresh must be > 0";
            return false;
        }

        params.sor_stddev_multhresh = static_cast<float>(param.as_double());

        return true;
    }

    return false;
}

bool PointCloudNode::update_plane_param(const rclcpp::Parameter &param,
                                        PcProcessingParams &params,
                                        std::string &reason) {
    const auto &name = param.get_name();

    if (name == "plane_axis") {
        const std::string value = param.as_string();

        const std::unordered_set<std::string> valid_axes = {"UnitX", "UnitY", "UnitZ"};

        if (valid_axes.find(value) == valid_axes.end()) {
            reason = "plane_axis must be one of: UnitX, UnitY, UnitZ";
            return false;
        }

        params.plane_axis = value;
        return true;
    }

    if (name == "eps_angle") {
        if (param.as_double() <= 0.0) {
            reason = "eps_angle must be > 0";
            return false;
        }

        params.eps_angle = static_cast<float>(param.as_double());

        return true;
    }

    if (name == "optimize_coefficients") {
        params.optimize_coefficients = param.as_bool();
        return true;
    }

    if (name == "model_type") {
        const std::string value = param.as_string();

        const std::unordered_set<std::string> valid_models = {
                "SACMODEL_PLANE", "SACMODEL_PARALLEL_PLANE", "SACMODEL_PERPENDICULAR_PLANE"};

        if (valid_models.find(value) == valid_models.end()) {
            reason = "invalid model_type";
            return false;
        }

        params.model_type = value;
        return true;
    }

    if (name == "method_type") {
        const std::string value = param.as_string();

        const std::unordered_set<std::string> valid_methods = {
                "SAC_RANSAC", "SAC_LMEDS", "SAC_MSAC", "SAC_RRANSAC"};

        if (valid_methods.find(value) == valid_methods.end()) {
            reason = "invalid method_type";
            return false;
        }

        params.method_type = value;
        return true;
    }

    if (name == "plane_max_iterations") {
        if (param.as_int() <= 0) {
            reason = "plane_max_iterations must be > 0";
            return false;
        }

        params.plane_max_iterations = param.as_int();
        return true;
    }

    if (name == "plane_distance_threshold") {
        if (param.as_double() <= 0.0) {
            reason = "plane_distance_threshold must be > 0";
            return false;
        }

        params.plane_distance_threshold = static_cast<float>(param.as_double());

        return true;
    }

    return false;
}

/*---------------- Main ----------------*/
int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PointCloudNode>());
    rclcpp::shutdown();
    return 0;
}