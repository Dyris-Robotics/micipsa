cmake_minimum_required(VERSION 3.8)
project(micipsa_behavior)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# --------------- Dependencies --------------- #
set(BEHAVIOR_TREE_DEPENDENCIES
  behaviortree_cpp
  nav2_behavior_tree
)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
foreach(Dependency IN ITEMS ${BEHAVIOR_TREE_DEPENDENCIES})
  find_package(${Dependency} REQUIRED)
endforeach()


# --------------- Behavior Tree Files --------------- #
# Behavior Tree Behavior Files
set(BEHAVIOR_TREE_BEHAVIOR_SOURCE_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/default_mission.cpp
)

set(BEHAVIOR_TREE_BEHAVIOR_HEADER_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_behavior/default_mission.h
)

# Behavior Tree Action Files
set(BEHAVIOR_TREE_ACTION_SOURCE_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/action/dock.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/action/undock.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/action/spin.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/action/select_dock.cpp

)

set(BEHAVIOR_TREE_ACTION_HEADER_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_behavior/action/dock.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_behavior/action/undock.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_behavior/action/spin.h
    ${CMAKE_CURRENT_SOURCE_DIR}/include/micipsa_behavior/action/select_dock.h
)

include_directories(include)

# --------------- Installing Executables --------------- #
add_executable(behavior_node
${BEHAVIOR_TREE_BEHAVIOR_SOURCE_FILES}
${BEHAVIOR_TREE_ACTION_SOURCE_FILES}
)

ament_target_dependencies(behavior_node ${BEHAVIOR_TREE_DEPENDENCIES})

install (TARGETS
  behavior_node
	DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY include/
  DESTINATION include/
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
ament_export_dependencies(${BEHAVIOR_TREE_DEPENDENCIES})
ament_package()
