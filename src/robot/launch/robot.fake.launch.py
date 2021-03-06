import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

import xacro


def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, 'r') as file:
            return file.read()
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def generate_launch_description():

    # Get URDF via xacro
    robot_description_path = os.path.join(
        get_package_share_directory('inmoov_description'),
        'robots',
        'inmoov.urdf.xacro')

    # Have to use seperate descriptions for each controller,
    # because otherwise controllers would publish the default joint value for joints they do not control, causing joint state value conflicts
    robot_head_description_path = os.path.join(
        get_package_share_directory('inmoov_description'),
        'robots',
        'inmoov_head_control.urdf.xacro')

    robot_jaw_description_path = os.path.join(
        get_package_share_directory('inmoov_description'),
        'robots',
        'inmoov_jaw_control.urdf.xacro')
    
    robot_eyes_description_path = os.path.join(
        get_package_share_directory('inmoov_description'),
        'robots',
        'inmoov_eyes_control.urdf.xacro')

    robot_description_config = xacro.process_file(robot_description_path)
    robot_description = {'robot_description': robot_description_config.toxml()}

    robot_head_description_config = xacro.process_file(robot_head_description_path)
    robot_head_description = {'robot_description': robot_head_description_config.toxml()}

    robot_jaw_description_config = xacro.process_file(robot_jaw_description_path)
    robot_jaw_description = {'robot_description': robot_jaw_description_config.toxml()}

    robot_eyes_description_config = xacro.process_file(robot_eyes_description_path)
    robot_eyes_description = {'robot_description': robot_eyes_description_config.toxml()}

    robot_description_semantic_config = load_file(
        'inmoov_description', 'config/inmoov.srdf')
    robot_description_semantic = {
        'robot_description_semantic': robot_description_semantic_config}

    controller = os.path.join(
        get_package_share_directory('robot'),
        'controllers',
        'head.yaml'
    )

    # RViz
    rviz_config_file = os.path.join(get_package_share_directory('inmoov_description'), "config", "inmoov.rviz")
    rviz_node = Node(package='rviz2',
                     executable='rviz2',
                     name='rviz2',
                     output='log',
                     arguments=['-d', rviz_config_file],
                     parameters=[robot_description,
                                 robot_description_semantic])

    # Publish TF
    robot_state_publisher = Node(package='robot_state_publisher',
                                 executable='robot_state_publisher',
                                 name='robot_state_publisher',
                                 output='both',
                                 parameters=[robot_description])

    # Static TF (where the robot is in the world frame)
    static_tf = Node(package='tf2_ros',
                     executable='static_transform_publisher',
                     name='static_transform_publisher',
                     output='log',
                     arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'world', 'base_link'])

    # Fake joint driver (also launches controller_manager)
    head_fake_joint_driver_node = Node(package='fake_joint_driver',
                                  executable='fake_joint_driver_node',
                                  parameters=[{'controller_name': 'head_controller'},
                                              controller,
                                              os.path.join(get_package_share_directory(
                                                  "robot"), "controllers", "start_positions.yaml"),
                                              robot_head_description])
    
    jaw_fake_joint_driver_node = Node(package='fake_joint_driver',
                                  executable='fake_joint_driver_node',
                                  parameters=[{'controller_name': 'jaw_controller'},
                                              controller,
                                              os.path.join(get_package_share_directory(
                                                  "robot"), "controllers", "start_positions.yaml"),
                                              robot_jaw_description])

    eyes_fake_joint_driver_node = Node(package='fake_joint_driver',
                                  executable='fake_joint_driver_node',
                                  parameters=[{'controller_name': 'eyes_controller'},
                                              controller,
                                              os.path.join(get_package_share_directory(
                                                  "robot"), "controllers", "start_positions.yaml"),
                                              robot_eyes_description])

    return LaunchDescription([
        static_tf,
        robot_state_publisher,

        head_fake_joint_driver_node,
        jaw_fake_joint_driver_node,
        eyes_fake_joint_driver_node,

        rviz_node
    ])
