#include "micipsa_behavior/action/spin.h"

namespace micipsa_behavior {

Spin::Spin(const std::string &name, const BT::NodeConfig &config)
        : BT::StatefulActionNode(name, config), state_(State::IDLE) {
    node_ = config.blackboard->get<rclcpp::Node::SharedPtr>("node");

    if (!node_) {
        throw std::runtime_error("Failed to get ROS2 node from blackboard");
    }

    action_client_ = rclcpp_action::create_client<SpinAction>(node_, "/spin");

    RCLCPP_INFO(node_->get_logger(), "Spin action client created");
}

BT::PortsList Spin::providedPorts() {
    return {BT::InputPort<float>("angle")};
}

void Spin::resetState() {
    state_ = State::IDLE;
    goal_handle_.reset();
}

BT::NodeStatus Spin::onStart() {
    auto angle = getInput<float>("angle");

    if (!angle) {
        RCLCPP_ERROR(node_->get_logger(), "Missing input port [angle]");
        return BT::NodeStatus::FAILURE;
    }

    // Non-blocking server availability check
    if (!action_client_->action_server_is_ready()) {
        RCLCPP_ERROR(node_->get_logger(), "Spin action server unavailable");
        return BT::NodeStatus::FAILURE;
    }

    resetState();

    state_ = State::RUNNING;

    sendGoal(*angle);

    return BT::NodeStatus::RUNNING;
}

BT::NodeStatus Spin::onRunning() {
    switch (state_) {
        case State::RUNNING:
            return BT::NodeStatus::RUNNING;

        case State::SUCCESS:
            return BT::NodeStatus::SUCCESS;

        case State::FAILURE:
        case State::IDLE:
        default:
            return BT::NodeStatus::FAILURE;
    }
}

void Spin::onHalted() {
    RCLCPP_WARN(node_->get_logger(), "Spin node halted");

    if (goal_handle_) {
        action_client_->async_cancel_goal(goal_handle_);
    }

    resetState();
}

void Spin::sendGoal(float angle) {
    SpinAction::Goal goal;

    goal.target_yaw = angle;

    rclcpp_action::Client<SpinAction>::SendGoalOptions goal_options;

    goal_options.goal_response_callback = [this](const GoalHandleSpin::SharedPtr &goal_handle) {
        if (!goal_handle) {
            RCLCPP_ERROR(node_->get_logger(), "Spin goal rejected");
            state_ = State::FAILURE;
            return;
        }

        RCLCPP_INFO(node_->get_logger(), "Spin Goal Accepted");
        goal_handle_ = goal_handle;
    };

    goal_options.feedback_callback =
            std::bind(&Spin::feedbackCallback, this, std::placeholders::_1, std::placeholders::_2);

    goal_options.result_callback = std::bind(&Spin::resultCallback, this, std::placeholders::_1);

    action_client_->async_send_goal(goal, goal_options);
}

void Spin::resultCallback(const GoalHandleSpin::WrappedResult &result) {
    switch (result.code) {
        case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(node_->get_logger(), "Spin succeeded");
            state_ = State::SUCCESS;
            break;

        case rclcpp_action::ResultCode::ABORTED:
            RCLCPP_ERROR(node_->get_logger(), "Spin aborted");
            state_ = State::FAILURE;
            break;

        case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(node_->get_logger(), "Spin canceled");
            state_ = State::FAILURE;
            break;

        default:
            RCLCPP_ERROR(node_->get_logger(),
                         "Unknown spin result code: %d",
                         static_cast<int>(result.code));
            state_ = State::FAILURE;

            break;
    }
}

void Spin::feedbackCallback(GoalHandleSpin::SharedPtr /*goal_handle*/,
                            const std::shared_ptr<const SpinAction::Feedback> feedback) {
    RCLCPP_DEBUG_THROTTLE(node_->get_logger(),
                          *node_->get_clock(),
                          1000,
                          "Angular distance traveled: %.2f",
                          feedback->angular_distance_traveled);
}

}  // namespace micipsa_behavior