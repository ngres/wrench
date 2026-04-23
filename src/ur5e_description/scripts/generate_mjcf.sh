#!/bin/bash
# Generates the MuJoCo model (MJCF) for the UR5e offline.
# Run once after setup or whenever the URDF or config files change.
# Prerequisites: ROS 2 workspace sourced, mujoco_ros2_control built.

set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$PKG_DIR/config/mjcf"

echo "Generating MJCF → $OUTPUT_DIR"

URDF=$(xacro "$PKG_DIR/urdf/ur5e_mujoco.urdf.xacro")

ros2 run mujoco_ros2_control robot_description_to_mjcf.sh \
  --robot_description "$URDF" \
  -m "$PKG_DIR/config/ur5e_mujoco_inputs.xml" \
  --scene "$PKG_DIR/config/ur5e_scene.xml" \
  --save_only \
  --output "$OUTPUT_DIR"

echo "Done. MJCF at $OUTPUT_DIR/mujoco_description_formatted.xml"
