#ifndef MICIPSA_BEHAVIOR_DEFAULT_MISSION_H
#define MICIPSA_BEHAVIOR_DEFAULT_MISSION_H

#include <memory>
#include <string>
#include <thread>

#include <rclcpp/rclcpp.hpp>

#include "behaviortree_cpp/bt_factory.h"

#include "micipsa_behavior/action/dock.h"
#include "micipsa_behavior/action/select_dock.h"
#include "micipsa_behavior/action/spin.h"
#include "micipsa_behavior/action/undock.h"

class DefaultMission {
 public:
    DefaultMission();

    void run();

 private:
    void registerBehaviorTreeNodes();

    rclcpp::Node::SharedPtr node_;

    BT::Blackboard::Ptr blackboard_;
    BT::BehaviorTreeFactory factory_;
    BT::Tree behavior_tree_;

    std::string bt_xml_;
};

#endif  // MICIPSA_BEHAVIOR_DEFAULT_MISSION_H