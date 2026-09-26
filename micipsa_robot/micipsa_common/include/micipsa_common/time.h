#ifndef MICIPSA_COMMON_TIME_HPP
#define MICIPSA_COMMON_TIME_HPP

#include <cstdint>

namespace micipsa_common {

struct TimeStamp {
    int64_t sec{0};
    uint32_t nsec{0};
};

}  // namespace micipsa_common

#endif