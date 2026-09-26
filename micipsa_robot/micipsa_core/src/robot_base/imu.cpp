#include "micipsa_core/robot_base/imu.h"

Imu::Imu() {
}

Imu::~Imu() {
}

void Imu::update(ImuMsg new_data) {
    imu_data_ = new_data;

    applyRatios();
    correctAxisSigns();
}

void Imu::applyRatios() {
    // The data read from ICM20948 is scaled to 1/1000.0 and divided by 1000.0 to get the actual
    // value.
    imu_data_.angular_velocity.x *= GYROSCOPE_RATIO;
    imu_data_.angular_velocity.y *= GYROSCOPE_RATIO;
    imu_data_.angular_velocity.z *= GYROSCOPE_RATIO;

    imu_data_.linear_acceleration.x *= ACCEL_RATIO;
    imu_data_.linear_acceleration.y *= ACCEL_RATIO;
    imu_data_.linear_acceleration.z *= ACCEL_RATIO;
}

void Imu::correctAxisSigns() {
    // The IMU driver sends Z-axis data with an inverted sign relative to
    // REP-103 convention (which requires z pointing up with gravity = +9.81 when
    // flat). Negating linear acceleration on Z corrects
    // the raw driver output to conform to the ROS FLU frame.
    imu_data_.linear_acceleration.z = -imu_data_.linear_acceleration.z;
}

ImuMsg &Imu::imuData() {
    return imu_data_;
}