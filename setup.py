from setuptools import setup
import os
from glob import glob

package_name = 'amr'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name, f'{package_name}.nodes'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Install launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Install URDF/Xacro files
        (os.path.join('share', package_name, 'description'), glob('description/*')),
        # Install Config files
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Deepak Kumar',
    description='Hardware bridge for L298N and ROS 2',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_driver = amr.nodes.motor_driver_node:main',
            'motor_encoder_bridge = amr.nodes.motor_encoder_bridge:main',
        ],
    },
)