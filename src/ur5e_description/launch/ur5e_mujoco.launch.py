#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
UR5e MuJoCo Demo

Launches a UR5e arm in MuJoCo via mujoco_ros2_control. The MJCF model must
be generated offline first by running scripts/generate_mjcf.sh.

Usage:
    ros2 launch ur5e_description ur5e_mujoco.launch.py
    ros2 launch ur5e_description ur5e_mujoco.launch.py headless:=true

Control the arm (position in radians for all 6 joints):
    ros2 topic pub /arm_controller/commands std_msgs/msg/Float64MultiArray \
      "data: [0.0, -1.57, 1.0, -1.57, 0.0, 0.0]"
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, Shutdown
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue, ParameterFile
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    pkg_share = FindPackageShare("ur5e_description")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([pkg_share, "urdf", "ur5e_mujoco.urdf.xacro"]),
            " headless:=",
            LaunchConfiguration("headless"),
        ]
    )

    robot_description_str = robot_description_content.perform(context)
    robot_description = {
        "robot_description": ParameterValue(value=robot_description_str, value_type=str)
    }

    parameters_file = PathJoinSubstitution([pkg_share, "config", "ur5e_controllers.yaml"])
    mujoco_plugins_file = PathJoinSubstitution(
        [pkg_share, "config", "mujoco_ros2_control_plugins.yaml"]
    )

    nodes = []

    # Robot state publisher
    nodes.append(
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="both",
            parameters=[robot_description, {"use_sim_time": True}],
        )
    )

    # ros2_control node backed by MuJoCo (loads MJCF from mujoco_model param in URDF)
    nodes.append(
        Node(
            package="mujoco_ros2_control",
            executable="ros2_control_node",
            emulate_tty=True,
            output="both",
            parameters=[
                {"use_sim_time": True},
                ParameterFile(parameters_file),
                ParameterFile(mujoco_plugins_file),
            ],
            remappings=(
                [("/motion_control_handle/target_frame", "/cartesian_compliance_controller/target_frame")]
            ),
            on_exit=Shutdown(),
        )
    )

    # Controller spawners
    for controller in ["joint_state_broadcaster", "force_torque_sensor_broadcaster", "cartesian_compliance_controller", "motion_control_handle"]:
        nodes.append(
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[controller, "--param-file", parameters_file.perform(context)],
                output="both",
            )
        )

    return nodes


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "headless",
                default_value="false",
                description="Run simulation without visualization window",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
