#include <gtest/gtest.h>

#include "micipsa_core/robot_base/drive_wheel.h"

/**
 * Test Case: Initialization
 * -------------------------
 * Description: Verifies that init() sets the public state to a known zero baseline
 *              and stores the configured wheel name.
 * Success Criteria:
 * - Name matches the provided wheel_name.
 * - Encoder counts are zero.
 * - Position is zero.
 * - Linear velocity is zero.
 * - Angular velocity is zero.
 * - Command is zero.
 */
TEST(TestDriveWheel, TestInitializationSetsDefaultState) {
    DriveWheel wheel;

    const std::string wheel_name = "left_wheel";
    const double counts_per_rev = 100.0;
    const bool invert_vel = false;
    const bool invert_encoder = false;
    const double wheel_radius = 0.05;
    const double max_velocity = 1.0;

    wheel.init(wheel_name, counts_per_rev, invert_vel, invert_encoder, wheel_radius, max_velocity);

    EXPECT_EQ(wheel.name(), wheel_name);
    EXPECT_EQ(wheel.encoderCounts(), 0);
    EXPECT_DOUBLE_EQ(wheel.position(), 0.0);
    EXPECT_DOUBLE_EQ(wheel.linearVelocity(), 0.0);
    EXPECT_DOUBLE_EQ(wheel.angularVelocity(), 0.0);
    EXPECT_DOUBLE_EQ(wheel.command(), 0.0);
}

/**
 * Test Case: Angle From Encoder Counts
 * ------------------------------------
 * Description: Verifies that calculateAngleFromEncoderCounts() converts encoder
 *              counts to radians using the configured counts_per_rev.
 * Success Criteria:
 * - For a quarter turn (counts_per_rev / 4), the computed angle equals
 *   (counts_per_rev / 4) * 2π / counts_per_rev within a small tolerance.
 */
TEST(TestDriveWheel, TestCalculatesAngleFromEncoderCounts) {
    DriveWheel wheel;

    const double counts_per_rev = 200.0;
    wheel.init("wheel", counts_per_rev, false, false, 0.05, 1.0);

    // Quarter turn
    wheel.encoderCounts() = static_cast<int>(counts_per_rev / 4.0);
    const double expected_angle = (counts_per_rev / 4.0) * (2.0 * M_PI) / counts_per_rev;

    EXPECT_NEAR(wheel.calculateAngleFromEncoderCounts(), expected_angle, 1e-6);
}

/**
 * Test Case: Update Kinematics
 * ----------------------------
 * Description: Verifies that update() computes wheel position, angular velocity,
 *              and linear velocity based on encoder counts and the update period.
 * Success Criteria:
 * - Position increases by the angle corresponding to the encoder delta.
 * - Angular velocity equals delta_angle / period.
 * - Linear velocity equals angular_velocity * wheel_radius.
 */
TEST(TestDriveWheel, TestUpdateComputesPositionAndVelocities) {
    DriveWheel wheel;

    const double counts_per_rev = 100.0;
    const double wheel_radius = 0.1;
    const double period = 0.1;  // seconds
    wheel.init("wheel", counts_per_rev, false, false, wheel_radius, 10.0);

    // First call only initializes encoder state (first_iteration_ logic).
    wheel.update(period, 0);

    // Second call: simulate 10 encoder counts since last update.
    const int total_count = 10;
    wheel.update(period, total_count);

    const double angle = (total_count * (2.0 * M_PI)) / counts_per_rev;
    const double expected_position = angle;
    const double expected_angular_velocity = angle / period;
    const double expected_linear_velocity = expected_angular_velocity * wheel_radius;

    EXPECT_NEAR(wheel.position(), expected_position, 1e-6);
    EXPECT_NEAR(wheel.angularVelocity(), expected_angular_velocity, 1e-6);
    EXPECT_NEAR(wheel.linearVelocity(), expected_linear_velocity, 1e-6);
}

/**
 * Test Case: Inverted Command Mirroring
 * -------------------------------------
 * Description: Verifies that adjustCommand() mirrors the sign of the command when
 *              the wheel is configured as inverted.
 * Success Criteria:
 * - With invert_vel = true and a positive command, the resulting command is negative
 *   with the same magnitude (ignoring any clamping behavior).
 */
TEST(TestDriveWheel, TestAdjustCommandMirrorsWhenInverted) {
    DriveWheel wheel;

    wheel.init("wheel", 100.0, true, true, 0.1, 5.0);

    wheel.command() = 1.5;  // below max_velocity so clamping does not affect it
    wheel.adjustCommand();

    EXPECT_DOUBLE_EQ(wheel.command(), -1.5);
}

/**
 * Test Case: Command Clamping (Disabled)
 * --------------------------------------
 * Description: Describes the desired future behavior of adjustCommand() with
 *              respect to max_velocity limits once clamping is implemented.
 * Success Criteria (once enabled):
 * - Commands within [-max_velocity, max_velocity] remain unchanged.
 * - Commands above +max_velocity are reduced to +max_velocity.
 * - Commands below -max_velocity are raised to -max_velocity.
 */
TEST(TestDriveWheel, TestClampCommandVelocity) {
    DriveWheel wheel;

    const double max_velocity = 5.0;
    wheel.init("wheel", 100.0, false, false, 0.1, max_velocity);

    // Command within limits should remain unchanged after adjustCommand.
    wheel.command() = 3.0;
    wheel.adjustCommand();
    EXPECT_DOUBLE_EQ(wheel.command(), 3.0);

    // Command above max velocity should be clamped to +max_velocity.
    wheel.command() = 100.0;
    wheel.adjustCommand();
    EXPECT_LE(wheel.command(), max_velocity);

    // Command below -max velocity should be clamped to -max_velocity.
    wheel.command() = -100.0;
    wheel.adjustCommand();
    EXPECT_GE(wheel.command(), -max_velocity);
}
