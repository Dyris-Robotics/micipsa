#ifndef MICIPSA_BEHAVIOR_ACTION_SELECT_DOCK_H
#define MICIPSA_BEHAVIOR_ACTION_SELECT_DOCK_H

#include <memory>
#include <string>

#include <rclcpp/parameter_client.hpp>
#include <rclcpp/rclcpp.hpp>

#include "behaviortree_cpp/action_node.h"
#include "behaviortree_cpp/bt_factory.h"

namespace micipsa_behavior {

class SelectDock : public BT::SyncActionNode {
 public:
    SelectDock(const std::string &name, const BT::NodeConfig &config);

    static BT::PortsList providedPorts();

    BT::NodeStatus tick() override;

 private:
    rclcpp::Node::SharedPtr node_;
    std::shared_ptr<rclcpp::AsyncParametersClient> param_client_;
};

}  // namespace micipsa_behavior

#endif  // MICIPSA_BEHAVIOR_ACTION_SELECT_DOCK_H