#include <gtest/gtest.h>

#include "micipsa_core/robot_base/imu.h"

/**
 * Test Case: Initialization
 * -------------------------
 * Description: Verifies that a default-constructed Imu object exposes imuData()
 *              with the expected default values defined in the message types.
 * Success Criteria:
 * - Orientation is identity quaternion (0, 0, 0, 1).
 * - Angular velocity is (0, 0, 0).
 * - Linear acceleration is (0, 0, 0).
 * - Orientation covariance matches the default array
 *   {1e6, 0, 0, 0, 1e6, 0, 0, 0, 1e-6}.
 * - Angular velocity covariance matches the default array
 *   {1e6, 0, 0, 0, 1e6, 0, 0, 0, 1e-6}.
 * - Linear acceleration covariance matches the default array
 *   {1e6, 0, 0, 0, 1e6, 0, 0, 0, 1e6}.
 */
TEST(TestImu, TestInitializationSetsDefaultState) {
    Imu imu;

    ImuMsg &data = imu.imuData();

    EXPECT_DOUBLE_EQ(data.orientation.x, 0.0);
    EXPECT_DOUBLE_EQ(data.orientation.y, 0.0);
    EXPECT_DOUBLE_EQ(data.orientation.z, 0.0);
    EXPECT_DOUBLE_EQ(data.orientation.w, 1.0);

    EXPECT_DOUBLE_EQ(data.angular_velocity.x, 0.0);
    EXPECT_DOUBLE_EQ(data.angular_velocity.y, 0.0);
    EXPECT_DOUBLE_EQ(data.angular_velocity.z, 0.0);

    EXPECT_DOUBLE_EQ(data.linear_acceleration.x, 0.0);
    EXPECT_DOUBLE_EQ(data.linear_acceleration.y, 0.0);
    EXPECT_DOUBLE_EQ(data.linear_acceleration.z, 0.0);

    const std::array<double, 9> expected_orientation_covariance{
            1e6, 0.0, 0.0, 0.0, 1e6, 0.0, 0.0, 0.0, 1e-6};
    const std::array<double, 9> expected_angular_velocity_covariance{
            1e6, 0.0, 0.0, 0.0, 1e6, 0.0, 0.0, 0.0, 1e-6};
    const std::array<double, 9> expected_linear_acceleration_covariance{
            1e6, 0.0, 0.0, 0.0, 1e6, 0.0, 0.0, 0.0, 1e6};

    EXPECT_EQ(data.orientation_covariance, expected_orientation_covariance);
    EXPECT_EQ(data.angular_velocity_covariance, expected_angular_velocity_covariance);
    EXPECT_EQ(data.linear_acceleration_covariance, expected_linear_acceleration_covariance);
}

/**
 * Test Case: Update Applies Gyroscope Ratio And Z Sign Correction
 * ---------------------------------------------------------------
 * Description: Verifies that calling update() scales angular velocity using
 *              GYROSCOPE_RATIO and then negates the Z axis in correctAxisSigns().
 * Success Criteria:
 * - angular_velocity.x = input.x * GYROSCOPE_RATIO
 * - angular_velocity.y = input.y * GYROSCOPE_RATIO
 * - angular_velocity.z = -(input.z * GYROSCOPE_RATIO)
 */
TEST(TestImu, TestUpdateAppliesGyroscopeRatioAndZSignCorrection) {
    Imu imu;

    ImuMsg msg;
    msg.angular_velocity.x = 1000.0;
    msg.angular_velocity.y = 2000.0;
    msg.angular_velocity.z = 3000.0;

    imu.update(msg);

    ImuMsg &data = imu.imuData();

    EXPECT_DOUBLE_EQ(data.angular_velocity.x, 1000.0 * GYROSCOPE_RATIO);
    EXPECT_DOUBLE_EQ(data.angular_velocity.y, 2000.0 * GYROSCOPE_RATIO);
    EXPECT_DOUBLE_EQ(data.angular_velocity.z, -(3000.0 * GYROSCOPE_RATIO));
}

/**
 * Test Case: Update Applies Acceleration Ratio And Z Sign Correction
 * ------------------------------------------------------------------
 * Description: Verifies that calling update() scales linear acceleration using
 *              ACCEL_RATIO and then negates the Z axis in correctAxisSigns().
 * Success Criteria:
 * - linear_acceleration.x = input.x * ACCEL_RATIO
 * - linear_acceleration.y = input.y * ACCEL_RATIO
 * - linear_acceleration.z = -(input.z * ACCEL_RATIO)
 */
TEST(TestImu, TestUpdateAppliesAccelerationRatioAndZSignCorrection) {
    Imu imu;

    ImuMsg msg;
    msg.linear_acceleration.x = 100.0;
    msg.linear_acceleration.y = 200.0;
    msg.linear_acceleration.z = 300.0;

    imu.update(msg);

    ImuMsg &data = imu.imuData();

    EXPECT_DOUBLE_EQ(data.linear_acceleration.x, 100.0 * ACCEL_RATIO);
    EXPECT_DOUBLE_EQ(data.linear_acceleration.y, 200.0 * ACCEL_RATIO);
    EXPECT_DOUBLE_EQ(data.linear_acceleration.z, -(300.0 * ACCEL_RATIO));
}

/**
 * Test Case: Update Preserves Orientation
 * ---------------------------------------
 * Description: Verifies that update() does not modify the orientation quaternion.
 * Success Criteria:
 * - Orientation values are copied unchanged.
 */
TEST(TestImu, TestUpdatePreservesOrientation) {
    Imu imu;

    ImuMsg msg;
    msg.orientation.x = 0.1;
    msg.orientation.y = 0.2;
    msg.orientation.z = 0.3;
    msg.orientation.w = 0.9;

    imu.update(msg);

    ImuMsg &data = imu.imuData();

    EXPECT_DOUBLE_EQ(data.orientation.x, 0.1);
    EXPECT_DOUBLE_EQ(data.orientation.y, 0.2);
    EXPECT_DOUBLE_EQ(data.orientation.z, 0.3);
    EXPECT_DOUBLE_EQ(data.orientation.w, 0.9);
}

/**
 * Test Case: Update Preserves Header
 * ----------------------------------
 * Description: Verifies that update() copies header fields unchanged.
 * Success Criteria:
 * - frame_id is copied unchanged.
 */
TEST(TestImu, TestUpdatePreservesHeader) {
    Imu imu;

    ImuMsg msg;
    msg.header.frame_id = "imu_link";

    imu.update(msg);

    ImuMsg &data = imu.imuData();

    EXPECT_EQ(data.header.frame_id, "imu_link");
}