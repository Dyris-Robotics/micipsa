#include <gtest/gtest.h>

#include "micipsa_core/robot_base/robot_base.h"

#include <cstdint>
#include <cstring>

/**
 * Test Case: Unpack 16-bit Integer
 * --------------------------------
 * Description: Verifies that unpack() reconstructs a signed 16-bit integer
 *              from a two-byte buffer using the same endianness as used on
 *              the host platform.
 * Success Criteria:
 * - Given a pair of bytes produced from an int16_t value, unpack() returns
 *   the original value.
 */
TEST(TestRobotBase, TestUnpackReconstructsInt16FromBytes) {
    RobotBase robot;

    const int16_t positive_value = 12345;
    uint8_t positive_bytes[sizeof(int16_t)];
    std::memcpy(positive_bytes, &positive_value, sizeof(int16_t));

    EXPECT_EQ(robot.unpackInt16(positive_bytes), positive_value);

    const int16_t negative_value = -2345;
    uint8_t negative_bytes[sizeof(int16_t)];
    std::memcpy(negative_bytes, &negative_value, sizeof(int16_t));

    EXPECT_EQ(robot.unpackInt16(negative_bytes), negative_value);
}

/**
 * Test Case: Update From Encoder Report
 * -------------------------------------
 * Description: Verifies that update() routes FUNC_REPORT_ENCODER frames to
 *              each wheel and that wheel kinematics (position and velocities)
 *              are updated consistently with the DriveWheel integration logic.
 * Success Criteria:
 * - After a first "zero" encoder report followed by a second report with
 *   non-zero counts, each wheel's position, angular velocity, and linear
 *   velocity match the analytical values computed from:
 *       angle = counts * 2π / counts_per_rev
 *       angular_velocity = angle / period
 *       linear_velocity = angular_velocity * wheel_radius
 */
TEST(TestRobotBase, TestUpdateProcessesEncoderReportsForAllWheels) {
    RobotBase robot;

    const double counts_per_rev = 200.0;
    const double wheel_radius = 0.1;
    const double max_velocity = 10.0;

    robot.frontLeftWheel().init(
            "front_left", counts_per_rev, false, false, wheel_radius, max_velocity);
    robot.frontRightWheel().init(
            "front_right", counts_per_rev, false, false, wheel_radius, max_velocity);
    robot.backLeftWheel().init(
            "back_left", counts_per_rev, false, false, wheel_radius, max_velocity);
    robot.backRightWheel().init(
            "back_right", counts_per_rev, false, false, wheel_radius, max_velocity);

    ReceivedData &received = robot.microController().receivedData();
    received.rx.assign(16, 0U);
    received.type = FUNC_REPORT_ENCODER;

    const double period = 0.1;
    micipsa_common::TimeStamp stamp{};
    stamp.sec = 1;
    stamp.nsec = 0;

    // First call: establishes the initial encoder baseline with zero counts.
    robot.update(period, stamp);

    auto encode_int16 = [](int16_t value, std::vector<uint8_t> &buffer, size_t offset) {
        std::memcpy(&buffer[offset], &value, sizeof(int16_t));
    };

    const int16_t back_left_counts = 10;
    const int16_t back_right_counts = 20;
    const int16_t front_left_counts = 30;
    const int16_t front_right_counts = 40;

    encode_int16(back_left_counts, received.rx, 0);
    encode_int16(back_right_counts, received.rx, 4);
    encode_int16(front_left_counts, received.rx, 8);
    encode_int16(front_right_counts, received.rx, 12);

    // Second call: encoder deltas are applied and wheel kinematics updated.
    robot.update(period, stamp);

    const double kTwoPi = 2.0 * M_PI;

    const double bl_angle = (back_left_counts * kTwoPi) / counts_per_rev;
    const double bl_expected_position = bl_angle;
    const double bl_expected_angular_velocity = bl_angle / period;
    const double bl_expected_linear_velocity = bl_expected_angular_velocity * wheel_radius;

    const double br_angle = (back_right_counts * kTwoPi) / counts_per_rev;
    const double br_expected_position = br_angle;
    const double br_expected_angular_velocity = br_angle / period;
    const double br_expected_linear_velocity = br_expected_angular_velocity * wheel_radius;

    const double fl_angle = (front_left_counts * kTwoPi) / counts_per_rev;
    const double fl_expected_position = fl_angle;
    const double fl_expected_angular_velocity = fl_angle / period;
    const double fl_expected_linear_velocity = fl_expected_angular_velocity * wheel_radius;

    const double fr_angle = (front_right_counts * kTwoPi) / counts_per_rev;
    const double fr_expected_position = fr_angle;
    const double fr_expected_angular_velocity = fr_angle / period;
    const double fr_expected_linear_velocity = fr_expected_angular_velocity * wheel_radius;

    EXPECT_NEAR(robot.backLeftWheel().position(), bl_expected_position, 1e-6);
    EXPECT_NEAR(robot.backLeftWheel().angularVelocity(), bl_expected_angular_velocity, 1e-6);
    EXPECT_NEAR(robot.backLeftWheel().linearVelocity(), bl_expected_linear_velocity, 1e-6);

    EXPECT_NEAR(robot.backRightWheel().position(), br_expected_position, 1e-6);
    EXPECT_NEAR(robot.backRightWheel().angularVelocity(), br_expected_angular_velocity, 1e-6);
    EXPECT_NEAR(robot.backRightWheel().linearVelocity(), br_expected_linear_velocity, 1e-6);

    EXPECT_NEAR(robot.frontLeftWheel().position(), fl_expected_position, 1e-6);
    EXPECT_NEAR(robot.frontLeftWheel().angularVelocity(), fl_expected_angular_velocity, 1e-6);
    EXPECT_NEAR(robot.frontLeftWheel().linearVelocity(), fl_expected_linear_velocity, 1e-6);

    EXPECT_NEAR(robot.frontRightWheel().position(), fr_expected_position, 1e-6);
    EXPECT_NEAR(robot.frontRightWheel().angularVelocity(), fr_expected_angular_velocity, 1e-6);
    EXPECT_NEAR(robot.frontRightWheel().linearVelocity(), fr_expected_linear_velocity, 1e-6);
}

/**
 * Test Case: Update From Raw IMU Report
 * -------------------------------------
 * Description: Verifies that RobotBase routes FUNC_REPORT_ICM_RAW frames to the
 *              Imu instance and populates the timestamp correctly.
 * Success Criteria:
 * - imu().imuData().header.stamp matches the TimeStamp passed to update().
 * - Raw gx, gy, gz, ax, ay, az values are forwarded to the IMU layer.
 *
 * Note:
 * - Scaling ratios and axis corrections are tested in Imu unit tests.
 */
TEST(TestRobotBase, TestUpdateProcessesImuReport) {
    RobotBase robot;

    ReceivedData &received = robot.microController().receivedData();
    received.rx.assign(12, 0U);
    received.type = FUNC_REPORT_ICM_RAW;

    auto encode_int16 = [](int16_t value, std::vector<uint8_t> &buffer, size_t offset) {
        std::memcpy(&buffer[offset], &value, sizeof(int16_t));
    };

    const int16_t gx = 1;
    const int16_t gy = 2;
    const int16_t gz = -3;
    const int16_t ax = 4;
    const int16_t ay = -5;
    const int16_t az = 6;

    encode_int16(gx, received.rx, 0);
    encode_int16(gy, received.rx, 2);
    encode_int16(gz, received.rx, 4);
    encode_int16(ax, received.rx, 6);
    encode_int16(ay, received.rx, 8);
    encode_int16(az, received.rx, 10);

    micipsa_common::TimeStamp stamp{};
    stamp.sec = 42;
    stamp.nsec = 100;

    robot.update(0.01, stamp);

    ImuMsg &data = robot.imu().imuData();

    EXPECT_EQ(data.header.stamp.sec, stamp.sec);
    EXPECT_EQ(data.header.stamp.nsec, stamp.nsec);

    // Verify values reached the IMU layer (exact values handled in Imu tests)
    EXPECT_NEAR(data.angular_velocity.x, gx * GYROSCOPE_RATIO, 1e-9);
    EXPECT_NEAR(data.angular_velocity.y, gy * GYROSCOPE_RATIO, 1e-9);
    EXPECT_NEAR(data.linear_acceleration.x, ax * ACCEL_RATIO, 1e-9);
    EXPECT_NEAR(data.linear_acceleration.y, ay * ACCEL_RATIO, 1e-9);
}
