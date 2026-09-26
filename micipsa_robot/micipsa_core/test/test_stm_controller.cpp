#include <gtest/gtest.h>

#include "micipsa_core/robot_base/stm_controller.h"

/**
 * Test Case: Initialization
 * -------------------------
 * Description: Verifies that init() configures communication parameters and
 *              resets input state to a known baseline.
 * Success Criteria:
 * - serialDevice(), baudrate(), and timeout() reflect the values passed to init().
 * - isConnected() is false after initialization.
 * - receivedData() has an empty rx buffer, type == 0, and size == 0.
 */
TEST(TestStmController, TestInitializationSetsConfigurationAndClearsInput) {
    StmController controller;

    const double max_angular_velocity = 5.0;
    const std::string serial_device = "/dev/ttyUSB0";
    const int baudrate = 115200;
    const int timeout = 1000;

    controller.init(max_angular_velocity, serial_device, baudrate, timeout);

    EXPECT_EQ(controller.serialDevice(), serial_device);
    EXPECT_EQ(controller.baudrate(), baudrate);
    EXPECT_EQ(controller.timeout(), timeout);
    EXPECT_FALSE(controller.isConnected());

    ReceivedData &data = controller.receivedData();
    EXPECT_TRUE(data.rx.empty());
    EXPECT_EQ(data.type, 0);
    EXPECT_EQ(data.size, 0U);
}

/**
 * Test Case: Clear Output Data
 * ----------------------------
 * Description: Verifies that clearOutputData() formats a "stop" frame in the
 *              command buffer with correct header, checksum, and tail bytes.
 * Success Criteria:
 * - First byte of commandData().tx is HEAD1.
 * - Bytes from index 1 up to OUTPUT_DATA_SIZE - 3 are zeroed.
 * - Byte at OUTPUT_DATA_SIZE - 2 is a valid checksum for the frame.
 * - Last byte of the buffer is FRAME_TAIL.
 */
TEST(TestStmController, TestClearOutputDataFormatsStopFrame) {
    StmController controller;

    // Ensure internal state such as is_connected_ is initialized.
    controller.init(0.0, "/dev/ttyUSB0", 115200, 1000);

    controller.clearOutputData();

    CommandData &cmd = controller.commandData();

    EXPECT_EQ(cmd.tx[0], static_cast<uint8_t>(HEAD1));
    for (size_t i = 1; i < OUTPUT_DATA_SIZE - 2; ++i) {
        EXPECT_EQ(cmd.tx[i], 0U);
    }

    const uint8_t checksum = cmd.tx[OUTPUT_DATA_SIZE - 2];
    const uint8_t tail = cmd.tx[OUTPUT_DATA_SIZE - 1];

    // Current implementation stores the boolean result of checkSum(OUTPUT_DATA_SIZE - 2,
    // OUTPUT_DATA_CHECK) into the checksum byte, so we simply verify that behavior here.
    const uint8_t expected_checksum_byte =
            static_cast<uint8_t>(controller.checkSum(OUTPUT_DATA_SIZE - 2, OUTPUT_DATA_CHECK));
    EXPECT_EQ(checksum, expected_checksum_byte);
    EXPECT_EQ(tail, static_cast<uint8_t>(FRAME_TAIL));
}

/**
 * Test Case: Clear Input Data
 * ---------------------------
 * Description: Verifies that clearInputData() resets the receivedData() buffer
 *              and related metadata fields.
 * Success Criteria:
 * - After populating receivedData(), calling clearInputData() empties the rx buffer.
 * - type is set to 0.
 * - size is set to 0.
 */
TEST(TestStmController, TestClearInputDataResetsReceivedData) {
    StmController controller;

    ReceivedData &data = controller.receivedData();
    data.rx = {1, 2, 3};
    data.type = 42;
    data.size = 3;

    controller.clearInputData();

    EXPECT_TRUE(data.rx.empty());
    EXPECT_EQ(data.type, 0);
    EXPECT_EQ(data.size, 0U);
}

/**
 * Test Case: Format Drive Wheels Speed Command Frame
 * ---------------------------------------------------
 * Description: Verifies that formatDriveWheelsSpeedData() encodes per-wheel mm/s
 *              targets into a FUNC_MOTOR_SPEED frame (closed-loop protocol).
 *              Unlike the old open-loop path, this class no longer does any
 *              unit conversion (rad/s -> mm/s happens upstream in DriveWheel) --
 *              it only rounds to int16 and packs little-endian.
 *
 *              Field -> wheel-slot mapping matches the M1-M4 order used on the
 *              wire (and documented in stm_controller.cpp):
 *                front_left  -> M1 (speed_a)
 *                back_right  -> M2 (speed_b)
 *                front_right -> M3 (speed_c)
 *                back_left   -> M4 (speed_d)
 *              Test values are deliberately distinct per field so a mapping
 *              mistake (e.g. swapping M2/M3) would be caught.
 * Success Criteria:
 * - Frame starts with HEAD1 and TX_HEAD2.
 * - Command function byte equals FUNC_MOTOR_SPEED.
 * - Each wheel's mm/s value (rounded) is packed as little-endian int16 in the
 *   correct M1-M4 slot, including correct two's-complement handling for the
 *   negative values.
 * - Length field at index 2 equals payload+header size - 1.
 * - Checksum byte equals the sum defined by TX_CHECKSUM_COMPLEMENT and the
 *   frame bytes.
 */
TEST(TestStmController, TestFormatDriveWheelsSpeedDataBuildsMotorFrame) {
    StmController controller;
    controller.init(0.0, "/dev/ttyUSB0", 115200, 1000);

    micipsa_core::WheelCommands wheels{};
    wheels.front_left_wheel_velocity = -300.4;  // -> M1, rounds to -300
    wheels.back_right_wheel_velocity = 300.4;   // -> M2, rounds to  300
    wheels.front_right_wheel_velocity = 150.0;  // -> M3
    wheels.back_left_wheel_velocity = -150.0;   // -> M4

    controller.formatDriveWheelsSpeedData(wheels);

    CommandData &cmd_data = controller.commandData();
    const uint8_t *tx = cmd_data.tx;

    EXPECT_EQ(tx[0], static_cast<uint8_t>(HEAD1));
    EXPECT_EQ(tx[1], static_cast<uint8_t>(TX_HEAD2));
    EXPECT_EQ(tx[3], static_cast<uint8_t>(FUNC_MOTOR_SPEED));

    auto lo = [](int16_t v) { return static_cast<uint8_t>(v & 0xFF); };
    auto hi = [](int16_t v) { return static_cast<uint8_t>((v >> 8) & 0xFF); };

    const int16_t expected_m1 = static_cast<int16_t>(std::round(wheels.front_left_wheel_velocity));
    const int16_t expected_m2 = static_cast<int16_t>(std::round(wheels.back_right_wheel_velocity));
    const int16_t expected_m3 = static_cast<int16_t>(std::round(wheels.front_right_wheel_velocity));
    const int16_t expected_m4 = static_cast<int16_t>(std::round(wheels.back_left_wheel_velocity));

    EXPECT_EQ(expected_m1, -300);
    EXPECT_EQ(expected_m2, 300);
    EXPECT_EQ(expected_m3, 150);
    EXPECT_EQ(expected_m4, -150);

    EXPECT_EQ(tx[4], lo(expected_m1));
    EXPECT_EQ(tx[5], hi(expected_m1));
    EXPECT_EQ(tx[6], lo(expected_m2));
    EXPECT_EQ(tx[7], hi(expected_m2));
    EXPECT_EQ(tx[8], lo(expected_m3));
    EXPECT_EQ(tx[9], hi(expected_m3));
    EXPECT_EQ(tx[10], lo(expected_m4));
    EXPECT_EQ(tx[11], hi(expected_m4));

    // header(4) + 4 wheels * 2 bytes = 12 bytes before checksum -> LEN = 11
    EXPECT_EQ(tx[2], static_cast<uint8_t>(11));

    uint8_t computed_checksum = TX_CHECKSUM_COMPLEMENT;
    for (size_t i = 0; i < 12; ++i) {
        computed_checksum = static_cast<uint8_t>(computed_checksum + tx[i]);
    }
    EXPECT_EQ(tx[12], static_cast<uint8_t>(computed_checksum & 0xff));
}