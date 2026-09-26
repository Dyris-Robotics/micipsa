cmake_minimum_required(VERSION 3.8)
project(micipsa_navigation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(utils
  PACKAGE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../utils"
)

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}/
)

install(PROGRAMS
  scripts/dock/dock_pose.py
  DESTINATION lib/${PROJECT_NAME}
)


if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)
  find_package(ament_cmake_ros REQUIRED)

  function(add_ros_isolated_launch_test path)
    set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
    add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
  endfunction()

  add_ros_isolated_launch_test(test/test_navigation_integration_launch.py)

endif()

ament_package()
