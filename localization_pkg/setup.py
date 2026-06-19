from setuptools import setup

package_name = 'localization_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/localization.launch.py']),
        ('share/' + package_name + '/config', ['config/ekf.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yasemin',
    maintainer_email='yasemin@todo.todo',
    description='Konumlandirma paketi',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts':[
            'chi2_validation = localization_pkg.chi2_validation:main',
            'ground_truth_compare = localization_pkg.ground_truth_compare:main',
            'lidar_odometry = localization_pkg.lidar_odometry:main',
            'gps_dropout = localization_pkg.gps_dropout:main',
        ],
    },
)
