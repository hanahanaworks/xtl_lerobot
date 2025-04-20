# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Logic to calibrate a myCobot 280 robot arm"""

import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from lerobot.common.robot_devices.motors.mycobot import MyCobotMotorsBus

# The following positions are provided in degree range used by myCobot 280
# For more info on these constants, see comments in the code where they get used.
ZERO_POSITION_DEGREE = 0
ROTATED_POSITION_DEGREE = 90

# Define joint limits for myCobot 280
# These are the physical limits in degrees for each joint
JOINT_LIMITS = {
    "joint1": (-170, 170),    # Base rotation
    "joint2": (-170, 170),    # Shoulder
    "joint3": (-170, 170),    # Elbow
    "joint4": (-170, 170),    # Wrist rotation
    "joint5": (-170, 170),    # Wrist bend
    "joint6": (-175, 175),    # End effector rotation
}

def run_arm_auto_calibration(arm: MyCobotMotorsBus, robot_type: str, arm_name: str, arm_type: str):
    """Run automatic calibration for myCobot 280 robot arm.
    
    This procedure will move each joint to its limits and calculate the center position.
    
    Args:
        arm: The myCobot motors bus
        robot_type: The type of robot (should be "mycobot")
        arm_name: The name of the arm
        arm_type: The type of arm (should be "280")
    
    Returns:
        A dictionary containing the calibration data for each motor
    """
    if robot_type != "mycobot" or arm_type != "280":
        raise NotImplementedError(f"Auto calibration only supports mycobot 280 arms, got {robot_type} {arm_type}")
    
    print(f"\nRunning calibration of {robot_type} {arm_name} {arm_type}...")
    
    # Get the list of motor names
    motor_names = list(arm._motors.keys())
    
    # Ensure the robot is powered on for calibration
    arm.write_torque_enable(True)
    print("\nRobot powered on for calibration")
    
    # Set LED to blue color to indicate calibration mode
    arm.write_led((0, 0, 255))
    
    # Dictionary to store calibration data
    calib = {}
    
    # Auto calibrate each joint one by one
    for motor_name in motor_names:
        if motor_name == "gripper":
            # Skip gripper if present, as it might have a different calibration process
            continue
            
        print(f"\nCalibrating joint: {motor_name}")
        
        # Get initial position
        initial_pos = arm.read_present_position([motor_name])[motor_name]
        
        # First find minimum position (move slowly to avoid damage)
        print(f"Finding minimum position for {motor_name}...")
        min_pos = find_joint_min_position(arm, motor_name)
        time.sleep(0.5)
        
        # Set LED to green to indicate progress
        arm.write_led((0, 255, 0))
        
        # Now find maximum position
        print(f"Finding maximum position for {motor_name}...")
        max_pos = find_joint_max_position(arm, motor_name)
        time.sleep(0.5)
        
        # Calculate center position
        center_pos = (min_pos + max_pos) / 2
        
        print(f"{motor_name} range: [{min_pos:.2f}, {max_pos:.2f}], center: {center_pos:.2f}")
        
        # Store calibration data
        calib[motor_name] = {
            "initial_pos": initial_pos,
            "min_pos": min_pos,
            "max_pos": max_pos,
            "center_pos": center_pos,
            "range": max_pos - min_pos
        }
        
        # Move joint to center position
        arm.write_goal_position({motor_name: center_pos})
        time.sleep(1)
    
    # Handle gripper calibration separately if it exists
    if "gripper" in motor_names:
        print("\nCalibrating gripper...")
        calib["gripper"] = calibrate_gripper(arm)
    
    # Move all joints to their center positions
    center_positions = {
        motor_name: data["center_pos"] 
        for motor_name, data in calib.items() 
        if motor_name != "gripper"
    }
    
    if center_positions:
        print("\nMoving all joints to center positions...")
        arm.write_goal_position(center_positions)
        time.sleep(2)
    
    # Set LED to green to indicate completion
    arm.write_led((0, 255, 0))
    print("\nCalibration completed successfully")
    
    return calib

def find_joint_min_position(arm: MyCobotMotorsBus, motor_name: str) -> float:
    """Find the minimum position for a joint by slowly moving until it reaches its limit.
    
    Args:
        arm: The myCobot motors bus
        motor_name: The name of the motor to calibrate
    
    Returns:
        The minimum position in degrees
    """
    joint_number = arm._motors[motor_name][0]  # Get the joint number (1-6)
    
    # Get the expected limits from our defined limits
    expected_limit = JOINT_LIMITS.get(f"joint{joint_number}", (-170, 170))[0]
    
    # Start from current position
    current_pos = arm.read_present_position([motor_name])[motor_name]
    
    # Move in small increments toward the minimum position
    # We'll go beyond the expected limit to ensure we find the true limit
    target_pos = expected_limit - 20
    step_size = 5  # degrees
    
    print(f"Moving {motor_name} from {current_pos:.2f}° toward min limit...")
    
    while current_pos > target_pos:
        # Move one step
        next_pos = max(current_pos - step_size, target_pos)
        arm.write_goal_position({motor_name: next_pos})
        
        # Wait for movement to complete
        time.sleep(0.5)
        
        # Get new position
        new_pos = arm.read_present_position([motor_name])[motor_name]
        
        # If position didn't change significantly, we've reached the limit
        if abs(new_pos - current_pos) < 0.5:
            print(f"Found minimum position at {new_pos:.2f}°")
            return new_pos
        
        current_pos = new_pos
    
    # If we reach here, we've hit our target position without finding a limit
    print(f"Reached target position {current_pos:.2f}° without finding a hard limit")
    return current_pos

def find_joint_max_position(arm: MyCobotMotorsBus, motor_name: str) -> float:
    """Find the maximum position for a joint by slowly moving until it reaches its limit.
    
    Args:
        arm: The myCobot motors bus
        motor_name: The name of the motor to calibrate
    
    Returns:
        The maximum position in degrees
    """
    joint_number = arm._motors[motor_name][0]  # Get the joint number (1-6)
    
    # Get the expected limits from our defined limits
    expected_limit = JOINT_LIMITS.get(f"joint{joint_number}", (-170, 170))[1]
    
    # Start from current position
    current_pos = arm.read_present_position([motor_name])[motor_name]
    
    # Move in small increments toward the maximum position
    # We'll go beyond the expected limit to ensure we find the true limit
    target_pos = expected_limit + 20
    step_size = 5  # degrees
    
    print(f"Moving {motor_name} from {current_pos:.2f}° toward max limit...")
    
    while current_pos < target_pos:
        # Move one step
        next_pos = min(current_pos + step_size, target_pos)
        arm.write_goal_position({motor_name: next_pos})
        
        # Wait for movement to complete
        time.sleep(0.5)
        
        # Get new position
        new_pos = arm.read_present_position([motor_name])[motor_name]
        
        # If position didn't change significantly, we've reached the limit
        if abs(new_pos - current_pos) < 0.5:
            print(f"Found maximum position at {new_pos:.2f}°")
            return new_pos
        
        current_pos = new_pos
    
    # If we reach here, we've hit our target position without finding a limit
    print(f"Reached target position {current_pos:.2f}° without finding a hard limit")
    return current_pos

def calibrate_gripper(arm: MyCobotMotorsBus) -> Dict:
    """Calibrate the gripper by testing open and closed positions.
    
    Args:
        arm: The myCobot motors bus
    
    Returns:
        A dictionary with gripper calibration data
    """
    print("Opening gripper...")
    arm.set_gripper(False)  # Open gripper
    time.sleep(2)
    
    print("Closing gripper...")
    arm.set_gripper(True)  # Close gripper
    time.sleep(2)
    
    print("Opening gripper again...")
    arm.set_gripper(False)  # Open gripper
    time.sleep(2)
    
    return {
        "calibrated": True
    }

def run_arm_manual_calibration(arm: MyCobotMotorsBus, robot_type: str, arm_name: str, arm_type: str):
    """Run manual calibration for myCobot 280 robot arm.
    
    This function ensures that a neural network trained on data collected on a given robot
    can work on another robot. The function guides the user to manually position the robot
    at specific positions and records the corresponding joint values.
    
    Args:
        arm: The myCobot motors bus
        robot_type: The type of robot (should be "mycobot")
        arm_name: The name of the arm
        arm_type: The type of arm (should be "280")
    
    Returns:
        A dictionary containing the calibration data for each motor
    """
    if robot_type != "mycobot" or arm_type != "280":
        raise NotImplementedError(f"Manual calibration only supports mycobot 280 arms, got {robot_type} {arm_type}")
    
    print(f"\nRunning manual calibration of {robot_type} {arm_name} {arm_type}...")
    
    # Ensure torque is disabled to allow manual positioning
    arm.write_torque_enable(False)
    print("Torque disabled. You can now manually move the robot.")
    
    # Get the list of motor names
    motor_names = list(arm._motors.keys())
    
    # Dictionary to store calibration data
    calib = {}
    
    # First, move to zero position
    print("\nPlease manually move the robot to the 'zero position' where all joints are at their nominal zero position.")
    input("Press Enter when the robot is in the zero position...")
    
    # Record positions at zero position
    zero_positions = arm.read_present_position()
    print(f"Zero positions recorded: {zero_positions}")
    
    # Now move to a rotated position
    print(f"\nPlease manually move the robot to the '{ROTATED_POSITION_DEGREE}° position' where:")
    for motor_name in motor_names:
        if motor_name != "gripper":
            print(f"  - {motor_name} is rotated to approximately {ROTATED_POSITION_DEGREE}° from the zero position")
    
    input("Press Enter when the robot is in the rotated position...")
    
    # Record positions at rotated position
    rotated_positions = arm.read_present_position()
    print(f"Rotated positions recorded: {rotated_positions}")
    
    # Calculate calibration data for each motor
    for motor_name in motor_names:
        if motor_name == "gripper":
            # Skip gripper in joint calculations
            continue
            
        zero_pos = zero_positions[motor_name]
        rotated_pos = rotated_positions[motor_name]
        
        # Determine direction consistency
        # If rotated_pos > zero_pos when we expect positive rotation, direction is consistent
        expected_direction = rotated_pos - zero_pos > 0
        
        calib[motor_name] = {
            "zero_pos": zero_pos,
            "rotated_pos": rotated_pos,
            "offset": zero_pos,  # Offset to apply to get to nominal zero
            "direction_inverted": not expected_direction
        }
    
    # Handle gripper calibration separately if it exists
    if "gripper" in motor_names:
        print("\nManual gripper calibration:")
        print("1. Please manually open the gripper completely")
        input("Press Enter when the gripper is fully open...")
        
        print("2. Please manually close the gripper completely")
        input("Press Enter when the gripper is fully closed...")
        
        calib["gripper"] = {
            "calibrated": True
        }
    
    # Enable torque again
    print("\nRe-enabling torque...")
    arm.write_torque_enable(True)
    
    # Set LED to green to indicate completion
    arm.write_led((0, 255, 0))
    print("\nManual calibration completed successfully")
    
    return calib

if __name__ == "__main__":
    import argparse
    import sys
    from lerobot.common.robot_devices.motors.configs import MyCobotMotorsBusConfig
    
    parser = argparse.ArgumentParser(description="Calibrate myCobot 280 robot arm")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port for myCobot connection")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate for serial connection")
    parser.add_argument("--method", type=str, choices=["auto", "manual"], default="manual", 
                        help="Calibration method (auto or manual)")
    parser.add_argument("--name", type=str, default="main", help="Arm name")
    
    args = parser.parse_args()
    
    try:
        # Create motors bus config
        config = MyCobotMotorsBusConfig(port=args.port, baud=args.baud)
        
        # Create motors bus
        arm = MyCobotMotorsBus(port=config.port, baud=config.baud, motors=config.motors)
        
        # Connect to the robot
        print(f"Connecting to myCobot on {config.port}...")
        arm.connect()
        
        # Run calibration
        if args.method == "auto":
            calibration_data = run_arm_auto_calibration(arm, "mycobot", args.name, "280")
        else:
            calibration_data = run_arm_manual_calibration(arm, "mycobot", args.name, "280")
        
        print("\nCalibration data:")
        for motor_name, data in calibration_data.items():
            print(f"{motor_name}: {data}")
        
        # Disconnect from the robot
        arm.disconnect()
        
    except Exception as e:
        print(f"Error during calibration: {e}")
        sys.exit(1)
