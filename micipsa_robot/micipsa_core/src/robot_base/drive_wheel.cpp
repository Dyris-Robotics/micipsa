#include "micipsa_core/robot_base/drive_wheel.h"

DriveWheel::DriveWheel() {
}

DriveWheel::~DriveWheel() {
}

void DriveWheel::init(const std::string &wheel_name,
                      double counts_per_rev,
                      bool invert_vel,
                      bool invert_encoder,
                      double wheel_radius,
                      double max_velocity) {
    name_ = wheel_name;
    counts_per_rev_ = counts_per_rev;
    invert_vel_ = invert_vel;
    invert_encoder_ = invert_encoder;
    wheel_radius_ = wheel_radius;
    max_velocity_ = max_velocity;

    encoder_counts_ = 0;
    last_total_counts_ = 0;

    position_ = 0.0;
    linear_velocity_ = 0.0;
    angular_velocity_ = 0.0;

    first_iteration_ = true;
    command_ = 0.0;
    command_mm_s_ = 0.0;
}

double DriveWheel::calculateAngleFromEncoderCounts() {
    return (encoder_counts_ * (2 * M_PI)) / counts_per_rev_;
}

void DriveWheel::update(double period, int32_t total_count) {
    if (invert_encoder_) {
        total_count = -1 * total_count;  // Mirror rotation
    }

    // The microcontrolLEr send the encoder counts known, not between last and new
    // state It means that if you turn the wheel, and the encoder counts is 100
    // then the microcontrolelr will keep sending 100.
    float previous_position = position_;

    // As the micrcontroller keeps sending the total count known (until its
    // rebooted) this boolean was created to avoid having a starting wheel position
    // different than 0 when relaunching nodes without restating stm
    if (first_iteration_) {
        updateEncoderCount(0);
        first_iteration_ = false;
    } else {
        updateEncoderCount(total_count);
    }

    updateWheelPosition(previous_position);
    updateWheelVelocities(period, previous_position);

    last_total_counts_ = total_count;
}

void DriveWheel::updateEncoderCount(int total_count) {
    encoder_counts_ = total_count - last_total_counts_;
}

void DriveWheel::updateWheelPosition(double previous_position) {
    position_ = calculateAngleFromEncoderCounts() + previous_position;
}

void DriveWheel::updateWheelVelocities(double period, double previous_position) {
    angular_velocity_ = (position_ - previous_position) / period;
    linear_velocity_ = angular_velocity_ * wheel_radius_;
}

void DriveWheel::adjustCommand() {
    clampCommandVelocity();
    mirrorCommandVelocity();
    convertCommandToMmPerSec();
}

void DriveWheel::clampCommandVelocity() {
    command_ = std::clamp(command_, -max_velocity_, max_velocity_);
}

void DriveWheel::mirrorCommandVelocity() {
    if (invert_vel_) {
        command_ = -command_;
    }
}

void DriveWheel::convertCommandToMmPerSec() {
    command_mm_s_ = command_ * wheel_radius_ * 1000.0;
}

std::string DriveWheel::name() {
    return name_;
}

int &DriveWheel::encoderCounts() {
    return encoder_counts_;
}

double &DriveWheel::position() {
    return position_;
}

double &DriveWheel::linearVelocity() {
    return linear_velocity_;
}

double &DriveWheel::angularVelocity() {
    return angular_velocity_;
}

double &DriveWheel::command() {
    return command_;
}

double &DriveWheel::commandMmPerSec() {
    return command_mm_s_;
}