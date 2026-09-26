cmake_minimum_required(VERSION 3.8)
project(micipsa_core)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# --------------- Dependencies --------------- #
set(ROBOT_BASE_IMU_DEPENDENCIES
  micipsa_common
)

set(ROBOT_BASE_STM_CONTROLLER_DEPENDENCIES
  serial
)

set(ROBOT_BASE_DRIVE_WHEEL_DEPENDENCIES
)

set(ROBOT_BASE_DEPENDENCIES
    ${ROBOT_BASE_IMU_DEPENDENCIES}
    ${ROBOT_BASE_STM_CONTROLLER_DEPENDENCIES}
    ${ROBOT_BASE_DRIVE_WHEEL_DEPENDENCIES}

)

find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${ROBOT_BASE_DEPENDENCIES})
  find_package(${Dependency} REQUIRED)
endforeach()

# --------------- STM PROTOCOL Files --------------- #
set(STM_PROTOCOL_HEADER_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_core/stm_protocol/command.h
)
# --------------- Robot Base Files --------------- #
set(ROBOT_BASE_SOURCE_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/robot_base/imu.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/robot_base/stm_controller.cpp 
    ${CMAKE_CURRENT_SOURCE_DIR}/src/robot_base/drive_wheel.cpp 
    ${CMAKE_CURRENT_SOURCE_DIR}/src/robot_base/robot_base.cpp
)

set(ROBOT_BASE_HEADER_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_core/robot_base/imu.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_core/robot_base/stm_controller.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_core/robot_base/drive_wheel.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_core/robot_base/robot_base.h
)

# --------------- Robot Base Library --------------- #
add_library(${PROJECT_NAME} ${ROBOT_BASE_SOURCE_FILES})
ament_target_dependencies(
  ${PROJECT_NAME}
  ${ROBOT_BASE_DEPENDENCIES}
)

set_property(TARGET ${PROJECT_NAME} PROPERTY POSITION_INDEPENDENT_CODE ON)

include_directories(include)

# --------------- Installing Libraries --------------- #
install(TARGETS ${PROJECT_NAME}
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(FILES ${ROBOT_BASE_HEADER_FILES}
  DESTINATION include/micipsa_core/robot_base)

install(FILES ${STM_PROTOCOL_HEADER_FILES}
  DESTINATION include/micipsa_core/stm_protocol)

# --------------- Testing --------------- #
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_drive_wheel
    test/test_drive_wheel.cpp
  )
  target_link_libraries(test_drive_wheel
    ${PROJECT_NAME}
  )

  ament_target_dependencies(test_drive_wheel
    ${ROBOT_BASE_DRIVE_WHEEL_DEPENDENCIES}
  )

  ament_add_gtest(test_imu
    test/test_imu.cpp
  )
  target_link_libraries(test_imu
    ${PROJECT_NAME}
  )

  ament_target_dependencies(test_imu
    ${ROBOT_BASE_IMU_DEPENDENCIES}
  )

  ament_add_gtest(test_stm_controller
    test/test_stm_controller.cpp
  )
  target_link_libraries(test_stm_controller
    ${PROJECT_NAME}
  )

  ament_target_dependencies(test_stm_controller
    ${ROBOT_BASE_STM_CONTROLLER_DEPENDENCIES}
  )

  ament_add_gtest(test_robot_base
    test/test_robot_base.cpp
  )
  target_link_libraries(test_robot_base
    ${PROJECT_NAME}
  )

  ament_target_dependencies(test_robot_base
    ${ROBOT_BASE_DEPENDENCIES}
  )

endif()

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME})
ament_export_dependencies(serial)
ament_package()
