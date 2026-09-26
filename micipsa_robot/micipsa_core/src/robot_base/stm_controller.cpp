#include "micipsa_core/robot_base/stm_controller.h"

#include <chrono>

StmController::StmController()
        : max_angular_velocity_(0.0),
          serial_device_(""),
          baudrate_(0),
          timeout_(0),
          is_connected_(false) {
    clearInputData();
    clearOutputData();
}

StmController::~StmController() {
    stopReaderThread();

    if (is_connected_) {
        disconnect();
    }
}

void StmController::init(double max_angular_velocity,
                         std::string serial_device,
                         int baudrate,
                         int timeout) {
    max_angular_velocity_ = max_angular_velocity;
    serial_device_ = serial_device;
    baudrate_ = baudrate;
    timeout_ = timeout;
    is_connected_ = false;
}

bool StmController::connect() {
    serial::Timeout timeout = serial::Timeout::simpleTimeout(timeout_);

    stm32_serial_.setPort(serial_device_);
    stm32_serial_.setBaudrate(baudrate_);
    stm32_serial_.setTimeout(timeout);
    stm32_serial_.open();

    if (stm32_serial_.isOpen()) {
        is_connected_ = true;
        return true;
    }

    is_connected_ = false;
    return false;
}

bool StmController::disconnect() {
    stopReaderThread();

    clearOutputData();

    if (!stm32_serial_.isOpen()) {
        is_connected_ = false;
        return true;
    }

    try {
        stm32_serial_.write(command_data_.tx, sizeof(command_data_.tx));
    } catch (serial::IOException &) {
        return false;
    }

    stm32_serial_.close();
    is_connected_ = false;
    return true;
}

bool StmController::readData() {
    size_t available = 0;
    try {
        available = stm32_serial_.available();
    } catch (serial::IOException &) {
        return false;
    }

    if (available > 0) {
        std::vector<uint8_t> chunk(available);
        size_t bytes_read = 0;
        try {
            bytes_read = stm32_serial_.read(chunk.data(), available);
        } catch (serial::IOException &) {
            return false;
        }
        chunk.resize(bytes_read);
        rx_accum_buffer_.insert(rx_accum_buffer_.end(), chunk.begin(), chunk.end());
    }

    return tryParseFrame();
}

bool StmController::tryParseFrame() {
    // Resync: drop leading bytes until we see HEAD1
    while (!rx_accum_buffer_.empty() && rx_accum_buffer_[0] != HEAD1) {
        rx_accum_buffer_.erase(rx_accum_buffer_.begin());
    }

    // Need HEAD1 + RX_HEAD2 + LENGTH + TYPE before we even know the frame size
    if (rx_accum_buffer_.size() < 4) {
        return false;
    }

    if (rx_accum_buffer_[1] != RX_HEAD2) {
        rx_accum_buffer_.erase(rx_accum_buffer_.begin());
        return false;
    }

    const uint8_t packet_length = rx_accum_buffer_[2];
    if (packet_length < MIN_PACKET_SIZE) {
        rx_accum_buffer_.erase(rx_accum_buffer_.begin());
        return false;
    }

    const size_t payload_plus_checksum = packet_length - 2;
    if (payload_plus_checksum > MAX_PACKET_SIZE) {
        rx_accum_buffer_.erase(rx_accum_buffer_.begin());
        return false;
    }

    const size_t full_frame_size = 4 + payload_plus_checksum;

    if (rx_accum_buffer_.size() < full_frame_size) {
        return false;
    }

    received_data_.type = rx_accum_buffer_[3];
    received_data_.size = payload_plus_checksum;
    received_data_.rx.assign(rx_accum_buffer_.begin() + 4,
                             rx_accum_buffer_.begin() + full_frame_size);

    uint8_t check_sum = packet_length + received_data_.type;
    for (size_t i = 0; i + 1 < received_data_.rx.size(); ++i) {
        check_sum += received_data_.rx[i];
    }
    const uint8_t rx_check_num = received_data_.rx.back();

    rx_accum_buffer_.erase(rx_accum_buffer_.begin(), rx_accum_buffer_.begin() + full_frame_size);

    return checkSum(check_sum, rx_check_num);
}

bool StmController::sendData(micipsa_core::StmCommands commands) {
    formatDriveWheelsSpeedData(commands.wheels_command);

    try {
        stm32_serial_.write(command_data_.tx, sizeof(command_data_.tx));
        return true;
    } catch (serial::IOException &) {
        return false;
    }
}

void StmController::formatDriveWheelsSpeedData(micipsa_core::WheelCommands wheels_command) {
    int16_t speed_a =
            static_cast<int16_t>(std::round(wheels_command.front_left_wheel_velocity));  // M1
    int16_t speed_b =
            static_cast<int16_t>(std::round(wheels_command.back_right_wheel_velocity));  // M2
    int16_t speed_c =
            static_cast<int16_t>(std::round(wheels_command.front_right_wheel_velocity));  // M3
    int16_t speed_d =
            static_cast<int16_t>(std::round(wheels_command.back_left_wheel_velocity));  // M4

    auto lo = [](int16_t v) { return static_cast<uint8_t>(v & 0xFF); };
    auto hi = [](int16_t v) { return static_cast<uint8_t>((v >> 8) & 0xFF); };

    std::vector<uint8_t> cmd = {HEAD1,
                                TX_HEAD2,
                                0x00,
                                FUNC_MOTOR_SPEED,
                                lo(speed_a),
                                hi(speed_a),
                                lo(speed_b),
                                hi(speed_b),
                                lo(speed_c),
                                hi(speed_c),
                                lo(speed_d),
                                hi(speed_d)};

    cmd[2] = static_cast<uint8_t>(cmd.size() - 1);
    uint8_t checksum = std::accumulate(cmd.begin(), cmd.end(), TX_CHECKSUM_COMPLEMENT) & 0xff;
    cmd.push_back(checksum);
    std::copy(cmd.begin(), cmd.end(), command_data_.tx);
}

void StmController::clearOutputData() {
    command_data_.tx[0] = HEAD1;

    for (size_t i = 1; i < OUTPUT_DATA_SIZE - 2; ++i) {
        command_data_.tx[i] = 0;
    }

    command_data_.tx[OUTPUT_DATA_SIZE - 2] = checkSum(OUTPUT_DATA_SIZE - 2, OUTPUT_DATA_CHECK);

    command_data_.tx[OUTPUT_DATA_SIZE - 1] = FRAME_TAIL;
}

void StmController::clearInputData() {
    received_data_.rx.clear();
    received_data_.type = 0;
    received_data_.size = 0;
    rx_accum_buffer_.clear();
}

bool StmController::checkSum(uint8_t check_sum, uint8_t rx_check_num) {
    return (check_sum % 256) == rx_check_num;
}

ReceivedData &StmController::receivedData() {
    return received_data_;
}

CommandData &StmController::commandData() {
    return command_data_;
}

bool StmController::isConnected() {
    return is_connected_;
}

std::string StmController::serialDevice() {
    return serial_device_;
}

int StmController::baudrate() {
    return baudrate_;
}

int StmController::timeout() {
    return timeout_;
}

void StmController::startReaderThread() {
    if (reader_thread_running_) {
        return;
    }
    reader_thread_running_ = true;
    reader_thread_ = std::thread(&StmController::readerThreadLoop, this);
}

void StmController::stopReaderThread() {
    reader_thread_running_ = false;
    if (reader_thread_.joinable()) {
        reader_thread_.join();
    }
}

void StmController::readerThreadLoop() {
    while (reader_thread_running_) {
        if (readData()) {
            std::lock_guard<std::mutex> lock(rx_mutex_);
            latest_received_data_ = received_data_;
            has_new_data_ = true;
        } else {
            std::this_thread::sleep_for(std::chrono::microseconds(500));
        }
    }
}

bool StmController::getLatestData(ReceivedData &out) {
    std::lock_guard<std::mutex> lock(rx_mutex_);
    if (!has_new_data_) {
        return false;
    }
    out = latest_received_data_;
    has_new_data_ = false;
    return true;
}