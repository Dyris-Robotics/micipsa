#ifndef MICIPSA_CORE_COMMAND_H
#define MICIPSA_CORE_COMMAND_H

namespace micipsa_core {

struct WheelCommands {
    double front_left_wheel_velocity{0.0};
    double front_right_wheel_velocity{0.0};
    double back_left_wheel_velocity{0.0};
    double back_right_wheel_velocity{0.0};
};

struct StmCommands {
    WheelCommands wheels_command;
};

}  // namespace micipsa_core

#endif