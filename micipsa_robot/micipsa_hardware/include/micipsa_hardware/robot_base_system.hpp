#ifndef MICIPSA_HARDWARE__ROBOT_BASE_HPP_
#define MICIPSA_HARDWARE__ROBOT_BASE_HPP_

#include <vector>
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

#include "rclcpp/clock.hpp"
#include "rclcpp/duration.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp/time.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include "visibility_control.h"

#include "micipsa_common/time.h"
#include "micipsa_core/robot_base/robot_base.h"

namespace micipsa_hardware {

class RobotBaseSystem : public hardware_interface::SystemInterface {
 public:
    RCLCPP_SHARED_PTR_DEFINITIONS(RobotBaseSystem)

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::CallbackReturn on_init(
            const hardware_interface::HardwareComponentInterfaceParams &params) override;

    MICIPSA_HARDWARE_PUBLIC
    std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

    MICIPSA_HARDWARE_PUBLIC
    std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::CallbackReturn on_configure(
            const rclcpp_lifecycle::State &previous_state) override;

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::CallbackReturn on_activate(
            const rclcpp_lifecycle::State &previous_state) override;

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::CallbackReturn on_deactivate(
            const rclcpp_lifecycle::State &previous_state) override;

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::return_type read(const rclcpp::Time &time,
                                         const rclcpp::Duration &period) override;

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::return_type write(const rclcpp::Time &time,
                                          const rclcpp::Duration &period) override;

    MICIPSA_HARDWARE_PUBLIC
    hardware_interface::CallbackReturn on_cleanup(
            const rclcpp_lifecycle::State &previous_state) override;

 protected:
    RobotBase robot_base_;
    bool new_data_received_;
};

}  // namespace micipsa_hardware

#endif  // MICIPSA_HARDWARE__ROBOT_BASE_HPP_