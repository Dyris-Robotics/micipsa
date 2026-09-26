#ifndef MICIPSA_BEHAVIOR_ACTION_DOCK_H
#define MICIPSA_BEHAVIOR_ACTION_DOCK_H

#include <atomic>
#include <string>

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>

#include "behaviortree_cpp/action_node.h"
#include "behaviortree_cpp/bt_factory.h"

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav2_msgs/action/dock_robot.hpp>

namespace micipsa_behavior {

class Dock : public BT::StatefulActionNode {
 public:
    Dock(const std::string &name, const BT::NodeConfig &config);

    static BT::PortsList providedPorts();

    BT::NodeStatus onStart() override;
    BT::NodeStatus onRunning() override;
    void onHalted() override;

 private:
    using DockAction = nav2_msgs::action::DockRobot;
    using GoalHandleDock = rclcpp_action::ClientGoalHandle<DockAction>;

    rclcpp::Node::SharedPtr node_;
    rclcpp_action::Client<DockAction>::SharedPtr action_client_;
    GoalHandleDock::SharedPtr goal_handle_;

    enum class State { IDLE, RUNNING, SUCCESS, FAILURE };
    std::atomic<State> state_;

    void resetState();
    void sendGoal(const std::string &dock_id);
    void resultCallback(const GoalHandleDock::WrappedResult &result);
    void feedbackCallback(GoalHandleDock::SharedPtr,
                          const std::shared_ptr<const DockAction::Feedback> feedback);
};

}  // namespace micipsa_behavior

#endif  // MICIPSA_BEHAVIOR_ACTION_DOCK_H