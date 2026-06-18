import os
from glob import glob
from setuptools import setup

package_name = 'gps_loss_zone'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ahmet',
    maintainer_email='ahmet@example.com',
    description='Robotaksi GPS-kaybi (tunel) bolgesi simulasyonu',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gps_loss_simulator = gps_loss_zone.gps_loss_simulator:main',
        ],
    },
)
