#include "micipsa_behavior/default_mission.h"

DefaultMission::DefaultMission() : node_(rclcpp::Node::make_shared("behavior_node")) {
    node_->declare_parameter<std::string>("behavior_tree_xml", "none.xml");

    node_->get_parameter("behavior_tree_xml", bt_xml_);

    registerBehaviorTreeNodes();

    blackboard_ = BT::Blackboard::create();

    blackboard_->set("node", node_);

    try {
        behavior_tree_ = factory_.createTreeFromFile(bt_xml_, blackboard_);

        RCLCPP_INFO(node_->get_logger(), "Behavior Tree loaded: %s", bt_xml_.c_str());

    } catch (const std::exception &e) {
        RCLCPP_FATAL(node_->get_logger(), "Failed to load Behavior Tree: %s", e.what());

        throw;
    }
}

void DefaultMission::run() {
    rclcpp::executors::MultiThreadedExecutor executor;

    executor.add_node(node_);

    std::thread spin_thread([&executor]() { executor.spin(); });

    rclcpp::Rate rate(10.0);

    while (rclcpp::ok()) {
        const auto status = behavior_tree_.tickOnce();

        if (status == BT::NodeStatus::FAILURE) {
            RCLCPP_ERROR(node_->get_logger(), "Behavior Tree returned FAILURE");
        }

        rate.sleep();
    }

    executor.cancel();

    if (spin_thread.joinable()) {
        spin_thread.join();
    }
}

void DefaultMission::registerBehaviorTreeNodes() {
    factory_.registerNodeType<micipsa_behavior::Spin>("Spin");
    factory_.registerNodeType<micipsa_behavior::Dock>("Dock");
    factory_.registerNodeType<micipsa_behavior::UnDock>("UnDock");
    factory_.registerNodeType<micipsa_behavior::SelectDock>("SelectDock");
}

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);

    try {
        DefaultMission behavior;

        behavior.run();

    } catch (const std::exception &e) {
        RCLCPP_FATAL(rclcpp::get_logger("behavior_node"), "Unhandled exception: %s", e.what());
    }

    rclcpp::shutdown();

    return 0;
}