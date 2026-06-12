from setuptools import setup
import os
from glob import glob

package_name = 'robotaxi_sim'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
        (os.path.join('share', package_name, 'models/robotaxi'), glob('models/robotaxi/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Robotaxi simulation',
    license='MIT',
    entry_points={
        'console_scripts': ['estop = robotaxi_sim.estop:main', 'imu_from_odom = robotaxi_sim.imu_from_odom:main'],
    },
)
