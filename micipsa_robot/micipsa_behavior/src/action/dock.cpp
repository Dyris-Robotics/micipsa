#include "micipsa_behavior/action/dock.h"

namespace micipsa_behavior {

Dock::Dock(const std::string &name, const BT::NodeConfig &config)
        : BT::StatefulActionNode(name, config), state_(State::IDLE) {
    node_ = config.blackboard->get<rclcpp::Node::SharedPtr>("node");

    if (!node_) {
        throw std::runtime_error("Failed to get ROS2 node from blackboard");
    }

    action_client_ = rclcpp_action::create_client<DockAction>(node_, "/dock_robot");

    RCLCPP_INFO(node_->get_logger(), "Dock action client created");
}

BT::PortsList Dock::providedPorts() {
    return {};
}

void Dock::resetState() {
    state_ = State::IDLE;
    goal_handle_.reset();
}

BT::NodeStatus Dock::onStart() {
    std::string dock_id;

    if (!config().blackboard->get("selected_dock", dock_id)) {
        RCLCPP_ERROR(node_->get_logger(), "No dock selected");
        return BT::NodeStatus::FAILURE;
    }

    // Non-blocking server availability check
    if (!action_client_->action_server_is_ready()) {
        RCLCPP_ERROR(node_->get_logger(), "Dock action server unavailable");
        return BT::NodeStatus::FAILURE;
    }

    resetState();

    state_ = State::RUNNING;

    sendGoal(dock_id);

    return BT::NodeStatus::RUNNING;
}

BT::NodeStatus Dock::onRunning() {
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

void Dock::onHalted() {
    RCLCPP_WARN(node_->get_logger(), "Dock node halted");

    if (goal_handle_) {
        action_client_->async_cancel_goal(goal_handle_);
    }

    resetState();
}

void Dock::sendGoal(const std::string &dock_id) {
    DockAction::Goal goal;

    goal.dock_id = dock_id;

    rclcpp_action::Client<DockAction>::SendGoalOptions goal_options;

    goal_options.goal_response_callback = [this](const GoalHandleDock::SharedPtr &goal_handle) {
        if (!goal_handle) {
            RCLCPP_ERROR(node_->get_logger(), "Dock goal rejected");
            state_ = State::FAILURE;
            return;
        }

        RCLCPP_INFO(node_->get_logger(), "Dock Goal Accepted");
        goal_handle_ = goal_handle;
    };

    goal_options.feedback_callback =
            std::bind(&Dock::feedbackCallback, this, std::placeholders::_1, std::placeholders::_2);

    goal_options.result_callback = std::bind(&Dock::resultCallback, this, std::placeholders::_1);

    action_client_->async_send_goal(goal, goal_options);
}

void Dock::resultCallback(const GoalHandleDock::WrappedResult &result) {
    switch (result.code) {
        case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(node_->get_logger(), "Dock succeeded");
            state_ = State::SUCCESS;
            break;

        case rclcpp_action::ResultCode::ABORTED:
            RCLCPP_ERROR(node_->get_logger(), "Dock aborted");
            state_ = State::FAILURE;
            break;

        case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(node_->get_logger(), "Dock canceled");
            state_ = State::FAILURE;
            break;

        default:
            RCLCPP_ERROR(node_->get_logger(),
                         "Unknown Dock result code: %d",
                         static_cast<int>(result.code));
            state_ = State::FAILURE;

            break;
    }
}

void Dock::feedbackCallback(GoalHandleDock::SharedPtr /*goal_handle*/,
                            const std::shared_ptr<const DockAction::Feedback> feedback) {
    RCLCPP_DEBUG_THROTTLE(node_->get_logger(),
                          *node_->get_clock(),
                          2000,
                          "Docking in progress | state=%u | retries=%u",
                          feedback->state,
                          feedback->num_retries);
}

}  // namespace micipsa_behavior