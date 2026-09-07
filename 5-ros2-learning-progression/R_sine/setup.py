from setuptools import find_packages, setup

package_name = 'R_sine'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='myCobot Sinusoidal wave movement package using velocity propagation IK',
    license='Apache-2.0',
    tests_require=['tests'],
    entry_points={
        'console_scripts': [
            'sine_motion = R_sine.sine_motion_node:main',
            'path_tracer = R_sine.path_tracer:main',
            'sine_wave_ik = R_sine.sine_wave_ik:main',
        ],
    },
)
