cmake_minimum_required(VERSION 3.8)
project(amr)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# 1. Install Python package logic
ament_python_install_package(${PROJECT_NAME})

# 2. Install Python executables
# Path matches your 'ls' output: amr/nodes/motor_driver_node.py
install(PROGRAMS
  amr/nodes/motor_driver_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME motor_driver_node
)

install(PROGRAMS
  amr/nodes/motor_encoder_bridge.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME motor_encoder_bridge
)

# 3. Install resource directories (Launch, Config, Description)
# Destination: share/amr/
install(DIRECTORY
  launch
  config
  description
  DESTINATION share/${PROJECT_NAME}
)

ament_package()