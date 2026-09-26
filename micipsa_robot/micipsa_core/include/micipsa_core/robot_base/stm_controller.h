#ifndef STM_CONTROLLER_H
#define STM_CONTROLLER_H

#include <atomic>
#include <cmath>
#include <cstdint>
#include <mutex>
#include <numeric>
#include <thread>
#include <vector>

#include "serial/serial.h"

#include "micipsa_core/stm_protocol/command.h"

#define HEAD1 0XFF
#define RX_HEAD2 0xFB
#define TX_HEAD2 0xFC

#define FRAME_TAIL 0X7D
#define TX_CHECKSUM_COMPLEMENT 257 - TX_HEAD2

#define OUTPUT_DATA_CHECK 1
#define OUTPUT_DATA_SIZE 13

#define FUNC_MOTOR_SPEED 0x16

#define FUNC_REPORT_ENCODER 0x0D

#define FUNC_REPORT_ICM_RAW 0x0E

#define MIN_PACKET_SIZE 3
#define MAX_PACKET_SIZE 0x15

typedef struct ReceivedData {
    std::vector<uint8_t> rx;
    uint8_t type;
    long unsigned int size;
} ReceivedData;

typedef struct CommandData {
    uint8_t tx[OUTPUT_DATA_SIZE];
} CommandData;

class StmController {
 public:
    StmController();
    ~StmController();

    void init(double max_angular_velocity, std::string serial_device, int baudrate, int timeout);

    bool checkSum(uint8_t check_sum, uint8_t rx_check_num);

    bool connect();
    bool disconnect();
    bool readData();
    bool sendData(micipsa_core::StmCommands commands);

    void formatDriveWheelsSpeedData(micipsa_core::WheelCommands wheels_command);

    void clearOutputData();
    void clearInputData();

    ReceivedData &receivedData();
    CommandData &commandData();
    bool isConnected();
    std::string serialDevice();
    int baudrate();
    int timeout();

    // --- Background reader thread ---
    void startReaderThread();
    void stopReaderThread();
    bool getLatestData(ReceivedData &out);

 private:
    bool tryParseFrame();
    void readerThreadLoop();

    serial::Serial stm32_serial_;
    ReceivedData received_data_;
    CommandData command_data_;

    std::vector<uint8_t> rx_accum_buffer_;

    std::string serial_device_;
    int baudrate_;
    int timeout_;

    bool is_connected_;
    double max_angular_velocity_;

    std::thread reader_thread_;
    std::atomic<bool> reader_thread_running_{false};
    std::mutex rx_mutex_;
    ReceivedData latest_received_data_;
    bool has_new_data_ = false;
};

#endif  // STM_CONTROLLER_H