import os
from glob import glob
from setuptools import setup

package_name = 'my_autonomous_car'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='emin',
    maintainer_email='emin@todo.todo',
    description='Otonom Arac Paketi',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'autonomous_controller = my_autonomous_car.autonomous_controller:main',
            'perception_node = my_autonomous_car.perception_node:main',
        ],
    },
)


