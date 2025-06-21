# Autonomous Mobile Robot (AMR) – ROS 2 Humble (Gazebo Classic 11)

This project demonstrates an **Autonomous Mobile Robot (AMR)** developed using **ROS 2 Humble** on **Ubuntu 22.04**, with simulation in **Gazebo Classic 11**. The robot performs **mapping, localization, and navigation** in a simulated 2D environment using **LiDAR and camera sensors**.

---

## Features

- SLAM Mapping  
  Generate a 2D occupancy grid map using **SLAM Toolbox** with LiDAR input.

- Localization  
  Estimate the robot’s pose on the map using **AMCL** (Adaptive Monte Carlo Localization).

- Autonomous Navigation  
  Navigate to user-defined goals with global and local path planning using **Nav2** stack.

- Simulation  
  Simulate robot behavior in **Gazebo Classic 11**, configured with a differential-drive model.

- Visualization  
  Visualize maps, robot pose, sensors, and environment in **RViz2**.

- Camera Monitoring  
  Stream live camera feed using `rqt_image_view`.

- TF Inspection  
  Inspect the full robot transform tree using `tf2_tools` and `view_frames`.

---

## Directory Structure

```
amr/
├── __init__.py
├── config/
│   ├── diff_drive_controller.yaml
│   ├── display_robot.rviz
│   ├── gazebo_params.yaml
│   ├── mapper_params_online_async.yaml
│   ├── my_controllers.yaml
│   ├── nav2_params.yaml
│   └── twist_mux.yaml
├── description/
│   ├── camera.xacro
│   ├── gazebo_control.xacro
│   ├── inertial_macros.xacro
│   ├── lidar.xacro
│   ├── material.xacro
│   ├── robot.urdf.xacro
│   ├── robot_core.xacro
│   └── ros2_control.xacro
├── launch/
│   ├── launch_sim.launch.py
│   ├── navigation_launch.py
│   ├── online_async_launch.py
│   ├── rplidar.launch.py
│   └── rsp.launch.py
├── world/
│   └── model.sdf
├── my_map_save.pgm
├── my_map_save.yaml
├── my_map_serial.data
├── my_map_serial.posegraph
├── CMakeLists.txt
├── LICENSE
├── package.xml
└── setup.cfg
```

---

## System Requirements

- OS: Ubuntu 22.04 LTS  
- ROS 2: Humble  
- Gazebo: Classic 11

---

## Required ROS 2 Packages

Install the required packages:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-gazebo-ros \
  ros-humble-rqt-image-view \
  ros-humble-tf2-tools \
  ros-humble-teleop-twist-keyboard \
  gazebo11 \
  ros-humble-gazebo-plugins
```

---

---

## Demo Video

Watch the demo video of the AMR in action:  
[▶️ Watch on Google Drive](https://drive.google.com/file/d/1Y_d6AQfHRYneliP6IGAeHicNg2dIlrHr/view?usp=sharing)
