#ifndef ROBOT_BASE_H
#define ROBOT_BASE_H

#include <cstdint>
#include <cstring>

#include "drive_wheel.h"
#include "imu.h"
#include "micipsa_core/stm_protocol/command.h"
#include "stm_controller.h"

#include "micipsa_common/time.h"

class RobotBase {
 public:
    RobotBase();
    ~RobotBase();

    void update(double period, micipsa_common::TimeStamp stamp);
    bool readCurrentState();
    bool sendCommands();

    void prepareWheelCommands();
    int32_t unpackInt32(const uint8_t *bytes);
    int16_t unpackInt16(const uint8_t *bytes);

    StmController &microController();
    DriveWheel &frontRightWheel();
    DriveWheel &frontLeftWheel();
    DriveWheel &backRightWheel();
    DriveWheel &backLeftWheel();
    Imu &imu();

 private:
    StmController micro_controller_;
    DriveWheel front_right_wheel_;
    DriveWheel front_left_wheel_;
    DriveWheel back_right_wheel_;
    DriveWheel back_left_wheel_;
    Imu imu_;

    ReceivedData latest_data_;
};

#endif  // ROBOT_BASE_H