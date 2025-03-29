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

"""Logic to communicate with the Elephant Robotics mycobot.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from lerobot.common.robot_devices.motors.utils import MotorsBus
from lerobot.common.robot_devices.utils import RobotDeviceAlreadyConnectedError, RobotDeviceNotConnectedError

try:
    from pymycobot.mycobot280 import MyCobot280
    MYCOBOT_AVAILABLE = True
except ImportError:
    MYCOBOT_AVAILABLE = False


class MyCobotMotorsBus(MotorsBus):
    """Implementation of MotorsBus for mycobot.

    Args:
        port: The port to connect to the mycobot.
        baud: The baud rate for the serial connection.
        motors: Dictionary mapping motor names to their indices (1-indexed) and models.
        mock: Whether to use a mock implementation.
    """

    def __init__(
        self,
        port: str,
        baud: int,
        motors: Dict[str, Tuple[int, str]],
        mock: bool = False,
    ):
        """Initialize the mycobot motors bus."""
        super().__init__()

        self._port = port
        self._baud = baud
        self._motors = motors
        self._mock = mock
        self._mycobot = None
        self._connected = False
        
        # Validate motor indices
        for motor_name, (motor_id, _) in self._motors.items():
            if motor_id < 1 or motor_id > 6:
                raise ValueError(
                    f"Invalid motor ID {motor_id} for motor {motor_name}. mycobot only supports 6 motors with IDs 1-6."
                )

    def connect(self) -> None:
        """Connect to the mycobot."""
        if self._connected:
            raise RobotDeviceAlreadyConnectedError("mycobot motors are already connected")
        
        if self._mock:
            logging.info("Using mock mycobot implementation")
            self._connected = True
            return

        if not MYCOBOT_AVAILABLE:
            raise ImportError(
                "pymycobot is not installed. Please install it with: pip install pymycobot"
            )

        try:
            self._mycobot = MyCobot280(self._port, self._baud)
            self._mycobot.power_on()
            time.sleep(0.5)  # Give time for the robot to power on
            self._connected = True
            logging.info(f"Connected to mycobot on {self._port}")
        except Exception as e:
            logging.error(f"Failed to connect to mycobot: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from the mycobot."""
        if not self._connected:
            raise RobotDeviceNotConnectedError("mycobot motors are not connected")
        
        if self._mock:
            self._connected = False
            return

        try:
            self._mycobot.power_off()
            self._connected = False
            self._mycobot = None
            logging.info("Disconnected from mycobot")
        except Exception as e:
            logging.error(f"Failed to disconnect from mycobot: {e}")
            raise

    def _ensure_connected(self) -> None:
        """Ensure the motors are connected."""
        if not self._connected:
            raise RobotDeviceNotConnectedError("mycobot motors are not connected")

    def read_present_position(
        self, 
        motor_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Read the current positions of the motors in degrees.

        Args:
            motor_names: Optional list of motor names to read. If None, read all motors.

        Returns:
            Dictionary mapping motor names to their positions in degrees.
        """
        self._ensure_connected()
        
        motor_names = motor_names or list(self._motors.keys())
        positions = {}

        if self._mock:
            # Return mock positions
            for motor_name in motor_names:
                positions[motor_name] = 0.0
            return positions

        try:
            # Read all angles at once for better performance
            all_angles = self._mycobot.get_angles()
            
            for motor_name in motor_names:
                motor_id, _ = self._motors[motor_name]
                # mycobot indices are 1-based but the angles list is 0-based
                positions[motor_name] = all_angles[motor_id - 1]
            
            return positions
        except Exception as e:
            logging.error(f"Failed to read positions from mycobot: {e}")
            raise

    def read_present_velocity(
        self, 
        motor_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Read the current velocities of the motors in degrees/s.
        
        Note: mycobot doesn't provide direct velocity readings, so this is not implemented.

        Args:
            motor_names: Optional list of motor names to read. If None, read all motors.

        Returns:
            Dictionary mapping motor names to their velocities (all zeros for mycobot).
        """
        self._ensure_connected()
        
        motor_names = motor_names or list(self._motors.keys())
        velocities = {}

        # mycobot doesn't provide velocity readings, so return zeros
        for motor_name in motor_names:
            velocities[motor_name] = 0.0
        
        return velocities

    def read_present_current(
        self, 
        motor_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Read the current draw of the motors in milliamperes.
        
        Note: mycobot doesn't provide current readings, so this is not implemented.

        Args:
            motor_names: Optional list of motor names to read. If None, read all motors.

        Returns:
            Dictionary mapping motor names to their current draw (all zeros for mycobot).
        """
        self._ensure_connected()
        
        motor_names = motor_names or list(self._motors.keys())
        currents = {}

        # mycobot doesn't provide current readings, so return zeros
        for motor_name in motor_names:
            currents[motor_name] = 0.0
        
        return currents

    def write_goal_position(
        self, 
        positions: Dict[str, float]
    ) -> None:
        """Write desired positions to the motors in degrees.

        Args:
            positions: Dictionary mapping motor names to their desired positions in degrees.
        """
        self._ensure_connected()
        
        if self._mock:
            return

        try:
            # Create a complete angles array
            current_angles = self._mycobot.get_angles()
            new_angles = current_angles.copy()
            
            # Update the angles that were provided
            for motor_name, position in positions.items():
                motor_id, _ = self._motors[motor_name]
                # mycobot indices are 1-based but the angles list is 0-based
                new_angles[motor_id - 1] = position
            
            # Send all angles at once
            self._mycobot.send_angles(new_angles, 50)  # 50% speed
        except Exception as e:
            logging.error(f"Failed to write positions to mycobot: {e}")
            raise

    def write_torque_enable(
        self, 
        enable: bool, 
        motor_names: Optional[List[str]] = None
    ) -> None:
        """Enable/disable torque for the specified motors.

        Args:
            enable: Whether to enable (True) or disable (False) torque.
            motor_names: Optional list of motor names to configure. If None, configure all motors.
        """
        self._ensure_connected()
        
        if self._mock:
            return

        try:
            if enable:
                self._mycobot.power_on()
            else:
                self._mycobot.power_off()
        except Exception as e:
            logging.error(f"Failed to {'enable' if enable else 'disable'} torque for mycobot: {e}")
            raise

    def write_led(
        self, 
        color: Tuple[int, int, int]
    ) -> None:
        """Set the LED color on the mycobot.

        Args:
            color: RGB color tuple with values from 0-255.
        """
        self._ensure_connected()
        
        if self._mock:
            return

        try:
            r, g, b = color
            self._mycobot.set_color(r, g, b)
        except Exception as e:
            logging.error(f"Failed to set LED color on mycobot: {e}")
            raise

    def set_gripper(
        self, 
        enable: bool
    ) -> None:
        """Control the gripper on the mycobot.

        Args:
            enable: True to close the gripper, False to open it.
        """
        self._ensure_connected()
        
        if self._mock:
            return

        try:
            if enable:
                self._mycobot.set_gripper_value(0, 50)  # Close gripper at 50% speed
            else:
                self._mycobot.set_gripper_value(255, 50)  # Open gripper at 50% speed
        except Exception as e:
            logging.error(f"Failed to control gripper on mycobot: {e}")
            raise
