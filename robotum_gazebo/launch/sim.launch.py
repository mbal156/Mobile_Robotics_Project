import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    desc_pkg = get_package_share_directory('robotum_description')
    gz_pkg = get_package_share_directory('robotum_gazebo')
    ros_gz_sim_pkg = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(desc_pkg, 'urdf', 'robotum.urdf.xacro')
    world_file = os.path.join(gz_pkg, 'worlds', 'engelli_dunya.sdf')
    bridge_file = os.path.join(gz_pkg, 'config', 'bridge.yaml')
    rviz_file = os.path.join(gz_pkg, 'rviz', 'sim.rviz')

    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # 1) Gazebo: dunyayi ac, -r ile simulasyonu hemen baslat
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_sim_pkg, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r {world_file}', 'on_exit_shutdown': 'true'}.items(),
    )

    # 2) Xacro'yu /robot_description olarak yayinla, TF'leri hesapla
    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
    )

    # 3) /robot_description'dan robotu Gazebo'ya spawn et
    #    base_link govde merkezi, yerden 0.1 m yukarida -> z = 0.1 + 0.01 pay
    spawn = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'robotum', '-z', '0.11'],
    )

    # 4) Gazebo <-> ROS 2 topic koprusu
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        parameters=[{'config_file': bridge_file, 'use_sim_time': True}],
    )

    # 5) RViz: sim.rviz varsa onunla ac
    rviz_args = ['-d', rviz_file] if os.path.exists(rviz_file) else []
    rviz = Node(
        package='rviz2', executable='rviz2', arguments=rviz_args,
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([gazebo, robot_state_publisher, spawn, bridge, rviz])
