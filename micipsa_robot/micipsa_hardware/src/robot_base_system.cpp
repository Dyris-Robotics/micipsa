#include "micipsa_hardware/robot_base_system.hpp"

namespace micipsa_hardware {

/*--------------------- HELPERS ---------------------*/
static micipsa_common::TimeStamp toTimeStamp(const rclcpp::Time &t) {
    const int64_t ns = t.nanoseconds();
    micipsa_common::TimeStamp ts;
    ts.sec = ns / 1000000000LL;
    ts.nsec = static_cast<uint32_t>(ns % 1000000000LL);
    return ts;
}

double string_to_double(const hardware_interface::HardwareInfo &info, const std::string &key) {
    return std::stod(info.hardware_parameters.at(key));
}

bool string_to_bool(const hardware_interface::HardwareInfo &info, const std::string &key) {
    const auto v = info.hardware_parameters.at(key);

    if (v == "true" || v == "True" || v == "1") return true;

    if (v == "false" || v == "False" || v == "0") return false;

    RCLCPP_WARN(rclcpp::get_logger("RobotBaseSystem"),
                "Invalid boolean value for param: %s. Setting default value to false.",
                key.c_str());
    return false;
}

int string_to_int(const hardware_interface::HardwareInfo &info, const std::string &key) {
    return std::stoi(info.hardware_parameters.at(key));
}
/*--------------------------------------------*/

hardware_interface::CallbackReturn RobotBaseSystem::on_init(
        const hardware_interface::HardwareComponentInterfaceParams &params) {
    if (hardware_interface::SystemInterface::on_init(params) !=
        hardware_interface::CallbackReturn::SUCCESS) {
        return hardware_interface::CallbackReturn::ERROR;
    }

    new_data_received_ = false;

    const auto &hardware_params = info_.hardware_parameters;
    const double wheel_radius = string_to_double(info_, "wheel_radius");
    const double max_angular_velocity = string_to_double(info_, "max_wheel_angular_velocity");

    robot_base_.frontLeftWheel().init(hardware_params.at("m1_joint_name"),
                                      string_to_int(info_, "m1_encoder_cpr"),
                                      string_to_bool(info_, "m1_vel_invert"),
                                      string_to_bool(info_, "m1_encoder_invert"),
                                      wheel_radius,
                                      max_angular_velocity);

    robot_base_.frontRightWheel().init(hardware_params.at("m2_joint_name"),
                                       string_to_int(info_, "m2_encoder_cpr"),
                                       string_to_bool(info_, "m2_vel_invert"),
                                       string_to_bool(info_, "m2_encoder_invert"),
                                       wheel_radius,
                                       max_angular_velocity);

    robot_base_.backLeftWheel().init(hardware_params.at("m3_joint_name"),
                                     string_to_int(info_, "m3_encoder_cpr"),
                                     string_to_bool(info_, "m3_vel_invert"),
                                     string_to_bool(info_, "m3_encoder_invert"),
                                     wheel_radius,
                                     max_angular_velocity);

    robot_base_.backRightWheel().init(hardware_params.at("m4_joint_name"),
                                      string_to_int(info_, "m4_encoder_cpr"),
                                      string_to_bool(info_, "m4_vel_invert"),
                                      string_to_bool(info_, "m4_encoder_invert"),
                                      wheel_radius,
                                      max_angular_velocity);

    robot_base_.microController().init(max_angular_velocity,
                                       hardware_params.at("mcu_serial_device"),
                                       string_to_int(info_, "mcu_baudrate"),
                                       string_to_int(info_, "mcu_timeout"));

    for (const hardware_interface::ComponentInfo &joint : info_.joints) {
        /*------ Command interfaces ------*/
        if (joint.command_interfaces.size() != 1) {
            RCLCPP_FATAL(rclcpp::get_logger("RobotBaseSystem"),
                         "Joint '%s' has %zu command interfaces found. 1 expected.",
                         joint.name.c_str(),
                         joint.command_interfaces.size());
            return hardware_interface::CallbackReturn::ERROR;
        }

        if (joint.command_interfaces[0].name != hardware_interface::HW_IF_VELOCITY) {
            RCLCPP_FATAL(rclcpp::get_logger("RobotBaseSystem"),
                         "Joint '%s' have %s command interfaces found. '%s' expected.",
                         joint.name.c_str(),
                         joint.command_interfaces[0].name.c_str(),
                         hardware_interface::HW_IF_VELOCITY);
            return hardware_interface::CallbackReturn::ERROR;
        }

        /*------ State interfaces ------*/
        if (joint.state_interfaces.size() != 2) {
            RCLCPP_FATAL(rclcpp::get_logger("RobotBaseSystem"),
                         "Joint '%s' has %zu state interface. 2 expected.",
                         joint.name.c_str(),
                         joint.state_interfaces.size());
            return hardware_interface::CallbackReturn::ERROR;
        }

        if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION) {
            RCLCPP_FATAL(rclcpp::get_logger("RobotBaseSystem"),
                         "Joint '%s' have '%s' as first state interface. '%s' expected.",
                         joint.name.c_str(),
                         joint.state_interfaces[0].name.c_str(),
                         hardware_interface::HW_IF_POSITION);
            return hardware_interface::CallbackReturn::ERROR;
        }

        if (joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY) {
            RCLCPP_FATAL(rclcpp::get_logger("RobotBaseSystem"),
                         "Joint '%s' have '%s' as second state interface. '%s' expected.",
                         joint.name.c_str(),
                         joint.state_interfaces[1].name.c_str(),
                         hardware_interface::HW_IF_VELOCITY);
            return hardware_interface::CallbackReturn::ERROR;
        }
    }

    return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> RobotBaseSystem::export_state_interfaces() {
    std::vector<hardware_interface::StateInterface> state_interfaces;

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.frontLeftWheel().name(),
                                               hardware_interface::HW_IF_POSITION,
                                               &robot_base_.frontLeftWheel().position()));
    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.frontLeftWheel().name(),
                                               hardware_interface::HW_IF_VELOCITY,
                                               &robot_base_.frontLeftWheel().angularVelocity()));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.backLeftWheel().name(),
                                               hardware_interface::HW_IF_POSITION,
                                               &robot_base_.backLeftWheel().position()));
    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.backLeftWheel().name(),
                                               hardware_interface::HW_IF_VELOCITY,
                                               &robot_base_.backLeftWheel().angularVelocity()));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.frontRightWheel().name(),
                                               hardware_interface::HW_IF_POSITION,
                                               &robot_base_.frontRightWheel().position()));
    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.frontRightWheel().name(),
                                               hardware_interface::HW_IF_VELOCITY,
                                               &robot_base_.frontRightWheel().angularVelocity()));
    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.backRightWheel().name(),
                                               hardware_interface::HW_IF_POSITION,
                                               &robot_base_.backRightWheel().position()));
    state_interfaces.emplace_back(
            hardware_interface::StateInterface(robot_base_.backRightWheel().name(),
                                               hardware_interface::HW_IF_VELOCITY,
                                               &robot_base_.backRightWheel().angularVelocity()));

    // SENSORS
    state_interfaces.emplace_back(hardware_interface::StateInterface(
            info_.sensors[0].name, "orientation.x", &robot_base_.imu().imuData().orientation.x));

    state_interfaces.emplace_back(hardware_interface::StateInterface(
            info_.sensors[0].name, "orientation.y", &robot_base_.imu().imuData().orientation.y));

    state_interfaces.emplace_back(hardware_interface::StateInterface(
            info_.sensors[0].name, "orientation.z", &robot_base_.imu().imuData().orientation.z));

    state_interfaces.emplace_back(hardware_interface::StateInterface(
            info_.sensors[0].name, "orientation.w", &robot_base_.imu().imuData().orientation.w));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.sensors[0].name,
                                               "angular_velocity.x",
                                               &robot_base_.imu().imuData().angular_velocity.x));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.sensors[0].name,
                                               "angular_velocity.y",
                                               &robot_base_.imu().imuData().angular_velocity.y));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.sensors[0].name,
                                               "angular_velocity.z",
                                               &robot_base_.imu().imuData().angular_velocity.z));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.sensors[0].name,
                                               "linear_acceleration.x",
                                               &robot_base_.imu().imuData().linear_acceleration.x));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.sensors[0].name,
                                               "linear_acceleration.y",
                                               &robot_base_.imu().imuData().linear_acceleration.y));

    state_interfaces.emplace_back(
            hardware_interface::StateInterface(info_.sensors[0].name,
                                               "linear_acceleration.z",
                                               &robot_base_.imu().imuData().linear_acceleration.z));

    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> RobotBaseSystem::export_command_interfaces() {
    std::vector<hardware_interface::CommandInterface> command_interfaces;

    command_interfaces.emplace_back(
            hardware_interface::CommandInterface(robot_base_.frontLeftWheel().name(),
                                                 hardware_interface::HW_IF_VELOCITY,
                                                 &robot_base_.frontLeftWheel().command()));

    command_interfaces.emplace_back(
            hardware_interface::CommandInterface(robot_base_.frontRightWheel().name(),
                                                 hardware_interface::HW_IF_VELOCITY,
                                                 &robot_base_.frontRightWheel().command()));

    command_interfaces.emplace_back(
            hardware_interface::CommandInterface(robot_base_.backLeftWheel().name(),
                                                 hardware_interface::HW_IF_VELOCITY,
                                                 &robot_base_.backLeftWheel().command()));

    command_interfaces.emplace_back(
            hardware_interface::CommandInterface(robot_base_.backRightWheel().name(),
                                                 hardware_interface::HW_IF_VELOCITY,
                                                 &robot_base_.backRightWheel().command()));

    return command_interfaces;
}

hardware_interface::CallbackReturn RobotBaseSystem::on_configure(
        const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"),
                "Configuring Microcontroller connection ...please wait...");

    if (robot_base_.microController().isConnected()) {
        if (robot_base_.microController().disconnect()) {
            RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "STM controller disconnected");
        } else {
            RCLCPP_ERROR(rclcpp::get_logger("RobotBaseSystem"),
                         "STM controller Failed to send shutdown frame");
        }
    }

    if (robot_base_.microController().connect()) {
        RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"),
                    "Serial port opened: %s",
                    robot_base_.microController().serialDevice().c_str());
    } else {
        RCLCPP_ERROR(rclcpp::get_logger("RobotBaseSystem"),
                     "Failed to open serial port %s",
                     robot_base_.microController().serialDevice().c_str());
        RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"),
                    "Failed to configure, connection couldn't be established with STM MCU!");
        return hardware_interface::CallbackReturn::ERROR;
    }

    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"),
                "Successfully configured, connection established with Microcontroller!");

    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotBaseSystem::on_activate(
        const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Activating ...please wait...");

    if (!robot_base_.microController().isConnected()) {
        return hardware_interface::CallbackReturn::ERROR;
    }

    robot_base_.microController().startReaderThread();

    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Successfully activated!");

    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotBaseSystem::on_deactivate(
        const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Deactivating ...please wait...");

    robot_base_.microController().stopReaderThread();

    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Successfully deactivated!");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RobotBaseSystem::read(const rclcpp::Time &time,
                                                      const rclcpp::Duration &period) {
    if (!robot_base_.microController().isConnected()) {
        return hardware_interface::return_type::ERROR;
    }

    if (robot_base_.readCurrentState()) {
        new_data_received_ = true;
        robot_base_.update(period.seconds(), toTimeStamp(time));
    }

    return hardware_interface::return_type::OK;
}

hardware_interface::return_type RobotBaseSystem::write(const rclcpp::Time & /*time*/,
                                                       const rclcpp::Duration & /*period*/) {
    if (!robot_base_.microController().isConnected()) {
        return hardware_interface::return_type::ERROR;
    }

    if (robot_base_.sendCommands()) {
        return hardware_interface::return_type::OK;
    }

    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Failed to send commands to STM MCU");
    return hardware_interface::return_type::ERROR;
}

hardware_interface::CallbackReturn RobotBaseSystem::on_cleanup(
        const rclcpp_lifecycle::State & /*previous_state*/) {
    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Cleaning up ...please wait...");

    robot_base_.microController().stopReaderThread();

    if (robot_base_.microController().isConnected()) {
        robot_base_.microController().disconnect();
    }

    RCLCPP_INFO(rclcpp::get_logger("RobotBaseSystem"), "Successfully cleaned up!");

    return hardware_interface::CallbackReturn::SUCCESS;
}

}  // namespace micipsa_hardware

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(micipsa_hardware::RobotBaseSystem, hardware_interface::SystemInterface)