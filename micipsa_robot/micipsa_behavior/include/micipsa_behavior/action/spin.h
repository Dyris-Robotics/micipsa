#ifndef MICIPSA_BEHAVIOR_ACTION_SPIN_H
#define MICIPSA_BEHAVIOR_ACTION_SPIN_H

#include <math.h>
#include <atomic>
#include <memory>
#include <string>

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>

#include "behaviortree_cpp/action_node.h"
#include "behaviortree_cpp/bt_factory.h"

#include <nav2_msgs/action/spin.hpp>

namespace micipsa_behavior {

class Spin : public BT::StatefulActionNode {
 public:
    Spin(const std::string &name, const BT::NodeConfig &config);

    static BT::PortsList providedPorts();

    BT::NodeStatus onStart() override;
    BT::NodeStatus onRunning() override;
    void onHalted() override;

 private:
    using SpinAction = nav2_msgs::action::Spin;
    using GoalHandleSpin = rclcpp_action::ClientGoalHandle<SpinAction>;

    rclcpp::Node::SharedPtr node_;
    rclcpp_action::Client<SpinAction>::SharedPtr action_client_;
    GoalHandleSpin::SharedPtr goal_handle_;

    enum class State { IDLE, RUNNING, SUCCESS, FAILURE };
    std::atomic<State> state_;

    void resetState();
    void sendGoal(float angle);
    void resultCallback(const GoalHandleSpin::WrappedResult &result);
    void feedbackCallback(GoalHandleSpin::SharedPtr,
                          const std::shared_ptr<const SpinAction::Feedback> feedback);
};

}  // namespace micipsa_behavior

#endif  // MICIPSA_BEHAVIOR_ACTION_SPIN_H