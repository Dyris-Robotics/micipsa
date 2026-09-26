#include "micipsa_behavior/action/undock.h"

namespace micipsa_behavior {

UnDock::UnDock(const std::string &name, const BT::NodeConfig &config)
        : BT::StatefulActionNode(name, config), state_(State::IDLE) {
    node_ = config.blackboard->get<rclcpp::Node::SharedPtr>("node");

    if (!node_) {
        throw std::runtime_error("Failed to get ROS2 node from blackboard");
    }

    action_client_ = rclcpp_action::create_client<UnDockAction>(node_, "/undock_robot");

    RCLCPP_INFO(node_->get_logger(), "UnDock action client created");
}

BT::PortsList UnDock::providedPorts() {
    return {};
}

void UnDock::resetState() {
    state_ = State::IDLE;
    goal_handle_.reset();
}

BT::NodeStatus UnDock::onStart() {
    std::string dock_type;

    if (!config().blackboard->get("selected_dock_type", dock_type)) {
        RCLCPP_ERROR(node_->get_logger(), "No dock type selected");

        return BT::NodeStatus::FAILURE;
    }

    // Non-blocking server availability check
    if (!action_client_->action_server_is_ready()) {
        RCLCPP_ERROR(node_->get_logger(), "UnDock action server unavailable");
        return BT::NodeStatus::FAILURE;
    }

    resetState();

    state_ = State::RUNNING;

    sendGoal(dock_type);

    return BT::NodeStatus::RUNNING;
}

BT::NodeStatus UnDock::onRunning() {
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

void UnDock::onHalted() {
    RCLCPP_WARN(node_->get_logger(), "UnDock node halted");

    if (goal_handle_) {
        action_client_->async_cancel_goal(goal_handle_);
    }

    resetState();
}

void UnDock::sendGoal(const std::string &dock_type) {
    UnDockAction::Goal goal;

    goal.dock_type = dock_type;

    rclcpp_action::Client<UnDockAction>::SendGoalOptions goal_options;

    goal_options.goal_response_callback = [this](const GoalHandleUnDock::SharedPtr &goal_handle) {
        if (!goal_handle) {
            RCLCPP_ERROR(node_->get_logger(), "UnDock goal rejected");
            state_ = State::FAILURE;
            return;
        }

        RCLCPP_INFO(node_->get_logger(), "UnDock Goal Accepted");
        goal_handle_ = goal_handle;
    };

    goal_options.feedback_callback = std::bind(
            &UnDock::feedbackCallback, this, std::placeholders::_1, std::placeholders::_2);

    goal_options.result_callback = std::bind(&UnDock::resultCallback, this, std::placeholders::_1);

    action_client_->async_send_goal(goal, goal_options);
}

void UnDock::resultCallback(const GoalHandleUnDock::WrappedResult &result) {
    switch (result.code) {
        case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(node_->get_logger(), "UnDock succeeded");
            state_ = State::SUCCESS;
            break;

        case rclcpp_action::ResultCode::ABORTED:
            RCLCPP_ERROR(node_->get_logger(), "UnDock aborted");
            state_ = State::FAILURE;
            break;

        case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(node_->get_logger(), "UnDock canceled");
            state_ = State::FAILURE;
            break;

        default:
            RCLCPP_ERROR(node_->get_logger(),
                         "Unknown UnDock result code: %d",
                         static_cast<int>(result.code));
            state_ = State::FAILURE;

            break;
    }
}

void UnDock::feedbackCallback(GoalHandleUnDock::SharedPtr /*goal_handle*/,
                              const std::shared_ptr<const UnDockAction::Feedback> feedback) {
}

}  // namespace micipsa_behavior