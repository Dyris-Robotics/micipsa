#ifndef MICIPSA_BEHAVIOR_ACTION_UNDOCK_H
#define MICIPSA_BEHAVIOR_ACTION_UNDOCK_H

#include <atomic>
#include <string>

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>

#include "behaviortree_cpp/action_node.h"
#include "behaviortree_cpp/bt_factory.h"

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav2_msgs/action/undock_robot.hpp>

namespace micipsa_behavior {

class UnDock : public BT::StatefulActionNode {
 public:
    UnDock(const std::string &name, const BT::NodeConfig &config);

    static BT::PortsList providedPorts();

    BT::NodeStatus onStart() override;
    BT::NodeStatus onRunning() override;
    void onHalted() override;

 private:
    using UnDockAction = nav2_msgs::action::UndockRobot;
    using GoalHandleUnDock = rclcpp_action::ClientGoalHandle<UnDockAction>;

    rclcpp::Node::SharedPtr node_;
    rclcpp_action::Client<UnDockAction>::SharedPtr action_client_;
    GoalHandleUnDock::SharedPtr goal_handle_;

    enum class State { IDLE, RUNNING, SUCCESS, FAILURE };
    std::atomic<State> state_;

    void resetState();
    void sendGoal(const std::string &dock_type);
    void resultCallback(const GoalHandleUnDock::WrappedResult &result);
    void feedbackCallback(GoalHandleUnDock::SharedPtr,
                          const std::shared_ptr<const UnDockAction::Feedback> feedback);
};

}  // namespace micipsa_behavior

#endif  // MICIPSA_BEHAVIOR_ACTION_UNDOCK_H