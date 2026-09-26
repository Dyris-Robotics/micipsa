#include "micipsa_behavior/action/select_dock.h"

namespace micipsa_behavior {

SelectDock::SelectDock(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config) {
    node_ = config.blackboard->get<rclcpp::Node::SharedPtr>("node");

    if (!node_) {
        throw std::runtime_error("Failed to get ROS2 node from blackboard");
    }

    param_client_ = std::make_shared<rclcpp::AsyncParametersClient>(node_, "/dock_pose_node");

    RCLCPP_INFO(node_->get_logger(), "SelectDock parameter client created");
}

BT::PortsList SelectDock::providedPorts() {
    return {BT::InputPort<std::string>("dock"), BT::InputPort<std::string>("dock_type")};
}

BT::NodeStatus SelectDock::tick() {
    auto dock = getInput<std::string>("dock");
    auto dock_type = getInput<std::string>("dock_type");
    if (!dock) {
        RCLCPP_ERROR(node_->get_logger(), "No dock provided");

        return BT::NodeStatus::FAILURE;
    }
    if (!dock_type) {
        RCLCPP_ERROR(node_->get_logger(), "No dock type provided");
        return BT::NodeStatus::FAILURE;
    }

    if (!param_client_->wait_for_service(std::chrono::seconds(2))) {
        RCLCPP_ERROR(node_->get_logger(), "dock_pose_node parameter service unavailable");

        return BT::NodeStatus::FAILURE;
    }

    auto future = param_client_->set_parameters({rclcpp::Parameter("dock_frame", *dock)});

    auto results = future.get();

    if (results.empty() || !results[0].successful) {
        RCLCPP_ERROR(node_->get_logger(), "Failed to set dock to '%s'", dock->c_str());

        return BT::NodeStatus::FAILURE;
    }

    config().blackboard->set("selected_dock", *dock);
    config().blackboard->set("selected_dock_type", *dock_type);

    RCLCPP_INFO(node_->get_logger(), "Selected dock '%s'", dock->c_str());

    return BT::NodeStatus::SUCCESS;
}

}  // namespace micipsa_behavior