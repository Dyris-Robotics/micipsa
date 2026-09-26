cmake_minimum_required(VERSION 3.8)
project(micipsa_perception)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# --------------- Dependencies --------------- #
# --------------- Pointcloud --------------- #
set(POINTCLOUD_PROCESSOR_DEPENDENCIES
  pcl_ros
)

set(POINTCLOUD_NODE_DEPENDENCIES
  ${POINTCLOUD_PROCESSOR_DEPENDENCIES}
  rclcpp
  sensor_msgs
  geometry_msgs
  visualization_msgs
  tf2_ros
  pcl_conversions
  tf2_sensor_msgs
)

set(POINTCLOUD_DEPENDENCIES
  ${POINTCLOUD_PROCESSOR_DEPENDENCIES}
  ${POINTCLOUD_NODE_DEPENDENCIES}
)

# --------------- AprilTags --------------- #
set(APRILTAGS_DEPENDENCIES
  rclcpp
  geometry_msgs
  tf2_ros
  tf2_geometry_msgs
  apriltag_msgs
)

# --------------- Full Dependencies --------------- #
set(PERCEPTION_DEPENDENCIES
  ${POINTCLOUD_DEPENDENCIES}
  ${APRILTAGS_DEPENDENCIES}
)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
foreach(Dependency IN ITEMS ${PERCEPTION_DEPENDENCIES})
  find_package(${Dependency} REQUIRED)
endforeach()

# --------------- Pointcloud Files --------------- #
set(POINTCLOUD_SOURCE_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/pointcloud/pointcloud_processor.cpp
)

set(POINTCLOUD_HEADER_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_perception/pointcloud/pointcloud_processor.h
)

# --------------- Pointcloud Library --------------- #
add_library(${PROJECT_NAME} ${POINTCLOUD_SOURCE_FILES})
ament_target_dependencies(
  ${PROJECT_NAME}
  ${POINTCLOUD_DEPENDENCIES}
)

include_directories(include)

# --------------- Installing Libraries --------------- #
install(TARGETS ${PROJECT_NAME}
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(FILES ${POINTCLOUD_HEADER_FILES}
  DESTINATION include/micipsa_perception/pointcloud)

# --------------- Installing Executables --------------- #
add_executable(pointcloud_node ${CMAKE_CURRENT_SOURCE_DIR}/src/pointcloud/pointcloud_node.cpp)
ament_target_dependencies(pointcloud_node ${POINTCLOUD_DEPENDENCIES})

target_link_libraries(pointcloud_node
  ${PROJECT_NAME}
)

install(TARGETS
  pointcloud_node
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/apriltags/apriltag_poses.py
  DESTINATION lib/${PROJECT_NAME}
)

# --------------- Installing Config/Launch Folders --------------- #
install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}/
)

# --------------- Installing Utils Files --------------- #
ament_python_install_package(utils
  PACKAGE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../utils"
)

# --------------- Testing --------------- #
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME})
ament_export_dependencies(${PERCEPTION_DEPENDENCIES})
ament_package()
