from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_path = get_package_share_directory('amr')
    xacro_file = os.path.join(pkg_path, 'description', 'robot.urdf.xacro')

    robot_description = Command(['xacro ', xacro_file])

    return LaunchDescription([

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            output='screen'
        )
    ])
