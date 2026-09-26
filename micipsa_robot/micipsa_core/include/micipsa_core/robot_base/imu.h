#ifndef IMU_H
#define IMU_H

/* ------ Genereal includes ------ */
#include <array>
#include <cstdint>
#include <string>

#include "micipsa_common/time.h"

/* ------ Constants ------ */
#define GYROSCOPE_RATIO 0.001
#define ACCEL_RATIO 0.001
#define MAG_RATIO 0.001

/* ------ IMU MESSAGE ------ */
struct Header {
    micipsa_common::TimeStamp stamp{};
    std::string frame_id{};
};

struct Vec3 {
    double x{0.0};
    double y{0.0};
    double z{0.0};
};

struct Quaternion {
    double x{0.0};
    double y{0.0};
    double z{0.0};
    double w{1.0};
};

struct ImuMsg {
    Header header{};

    Quaternion orientation{};
    Vec3 angular_velocity{};
    Vec3 linear_acceleration{};

    std::array<double, 9> orientation_covariance{1e6, 0, 0, 0, 1e6, 0, 0, 0, 1e-6};
    std::array<double, 9> angular_velocity_covariance{1e6, 0, 0, 0, 1e6, 0, 0, 0, 1e-6};
    std::array<double, 9> linear_acceleration_covariance{1e6, 0, 0, 0, 1e6, 0, 0, 0, 1e6};
};

class Imu {
 public:
    Imu();
    ~Imu();

    void update(ImuMsg new_data);

    ImuMsg &imuData();

 private:
    void applyRatios();
    void correctAxisSigns();

 private:
    ImuMsg imu_data_;
};

#endif  // IMU_H