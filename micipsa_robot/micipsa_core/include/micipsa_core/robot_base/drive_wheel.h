#ifndef DRIVE_WHEEL_H
#define DRIVE_WHEEL_H

#include <algorithm>
#include <cmath>
#include <string>
class DriveWheel {
 public:
    DriveWheel();
    ~DriveWheel();

    void init(const std::string &wheel_name,
              double counts_per_rev,
              bool invert_vel,
              bool invert_encoder,
              double wheel_radius,
              double max_velocity);

    double calculateAngleFromEncoderCounts();

    void update(double period, int32_t total_count);

    void updateEncoderCount(int total_count);
    void updateWheelPosition(double previous_position);
    void updateWheelVelocities(double period, double previous_position);

    void adjustCommand();
    void clampCommandVelocity();
    void mirrorCommandVelocity();
    void convertCommandToMmPerSec();

    std::string name();
    int &encoderCounts();
    double &position();
    double &linearVelocity();
    double &angularVelocity();
    double &command();
    double &commandMmPerSec();

 private:
    std::string name_;
    double counts_per_rev_;
    bool invert_vel_;
    bool invert_encoder_;
    double wheel_radius_;
    double max_velocity_;

    int32_t encoder_counts_;
    int32_t last_total_counts_;

    double position_;
    double linear_velocity_;
    double angular_velocity_;

    double command_;
    double command_mm_s_;

    bool first_iteration_;
};

#endif  // DRIVE_WHEEL_H