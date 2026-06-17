from setuptools import setup

package_name = 'atlas_planning'

setup(
    name=package_name,
    version='0.1.0',
    packages=[
        package_name,
        package_name + '.states',
        package_name + '.tests',
    ],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Atlas Takim',
    maintainer_email='atlas@todo.todo',
    description='Atlas Takimi Planlama Katmani',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fsm_node = atlas_planning.fsm_node:main',
            'mission_manager_node = atlas_planning.mission_manager_node:main',
            'velocity_planner_node = atlas_planning.velocity_planner_node:main',
            'behavior_monitor_node = atlas_planning.behavior_monitor_node:main',
            'test_tur1 = atlas_planning.tests.test_tur1:main',
            'local_planner_node = atlas_planning.local_planner_node:main',
        ],
    },
)
