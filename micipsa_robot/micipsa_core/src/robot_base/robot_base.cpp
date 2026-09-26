#include "micipsa_core/robot_base/robot_base.h"

RobotBase::RobotBase() {
}

RobotBase::~RobotBase() {
}

void RobotBase::update(double period, micipsa_common::TimeStamp stamp) {
    switch (latest_data_.type) {
        // MOTORS
        case FUNC_REPORT_ENCODER:
            front_left_wheel_.update(period, unpackInt32(&latest_data_.rx[0]));
            back_right_wheel_.update(period, unpackInt32(&latest_data_.rx[4]));
            front_right_wheel_.update(period, unpackInt32(&latest_data_.rx[8]));
            back_left_wheel_.update(period, unpackInt32(&latest_data_.rx[12]));

            break;

        // IMU
        case FUNC_REPORT_ICM_RAW: {
            ImuMsg raw_imu_msg;
            raw_imu_msg.header.stamp = stamp;

            raw_imu_msg.angular_velocity.x = unpackInt16(&latest_data_.rx[0]);
            raw_imu_msg.angular_velocity.y = unpackInt16(&latest_data_.rx[2]);
            raw_imu_msg.angular_velocity.z = unpackInt16(&latest_data_.rx[4]);

            raw_imu_msg.linear_acceleration.x = unpackInt16(&latest_data_.rx[6]);
            raw_imu_msg.linear_acceleration.y = unpackInt16(&latest_data_.rx[8]);
            raw_imu_msg.linear_acceleration.z = unpackInt16(&latest_data_.rx[10]);

            imu_.update(raw_imu_msg);

            break;
        }

        default:
            break;
    }
}

bool RobotBase::readCurrentState() {
    return micro_controller_.getLatestData(latest_data_);
}

bool RobotBase::sendCommands() {
    prepareWheelCommands();

    micipsa_core::StmCommands commands;
    commands.wheels_command.front_left_wheel_velocity = front_left_wheel_.commandMmPerSec();
    commands.wheels_command.front_right_wheel_velocity = front_right_wheel_.commandMmPerSec();
    commands.wheels_command.back_left_wheel_velocity = back_left_wheel_.commandMmPerSec();
    commands.wheels_command.back_right_wheel_velocity = back_right_wheel_.commandMmPerSec();

    if (micro_controller_.sendData(commands)) {
        return true;
    }
    return false;
}

void RobotBase::prepareWheelCommands() {
    front_left_wheel_.adjustCommand();
    front_right_wheel_.adjustCommand();
    back_left_wheel_.adjustCommand();
    back_right_wheel_.adjustCommand();
}

int16_t RobotBase::unpackInt16(const uint8_t *bytes) {
    int16_t value;
    std::memcpy(&value, bytes, sizeof(int16_t));
    return value;
}

int32_t RobotBase::unpackInt32(const uint8_t *bytes) {
    int32_t value;
    std::memcpy(&value, bytes, sizeof(int32_t));
    return value;
}

StmController &RobotBase::microController() {
    return micro_controller_;
}

Imu &RobotBase::imu() {
    return imu_;
}

DriveWheel &RobotBase::frontRightWheel() {
    return front_right_wheel_;
}

DriveWheel &RobotBase::frontLeftWheel() {
    return front_left_wheel_;
}

DriveWheel &RobotBase::backRightWheel() {
    return back_right_wheel_;
}

DriveWheel &RobotBase::backLeftWheel() {
    return back_left_wheel_;
}