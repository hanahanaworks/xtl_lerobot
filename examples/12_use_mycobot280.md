# Using Elephant Robotics myCobot 280 with LeRobot

This guide explains how to set up and use the Elephant Robotics myCobot 280 with the LeRobot platform.

## What's been added

We've integrated the myCobot 280 into the LeRobot platform with the following components:

1. **MyCobotMotorsBus** - A new motor controller implementation that interfaces with the myCobot 280 via the pymycobot library
2. **MyCobotMotorsBusConfig** - Configuration class for myCobot motor buses
3. **MyCobotRobotConfig** - Robot configuration for myCobot 280
4. **Updated motor utilities** - The motor utility functions have been updated to recognize and support myCobot motors

## Requirements

- Elephant Robotics myCobot 280
- pymycobot library
- USB connection to the robot

## Installation

1. Install the pymycobot library:

```bash
pip install pymycobot
```

2. Identify your myCobot's serial port:
   - Linux: typically `/dev/ttyUSB0` or `/dev/ttyACM0`
   - macOS: typically `/dev/tty.usbserial-*`
   - Windows: typically `COM*`

## Using myCobot 280 with LeRobot

### Basic usage

Here's a simple example of how to use the myCobot 280:

```python
from lerobot.common.robot_devices.robots.configs import MyCobotRobotConfig
from lerobot.common.robot_devices.robots.manipulator import ManipulatorRobot

# Create a robot configuration (customize the port for your setup)
config = MyCobotRobotConfig(
    leader_arms={
        "main": MyCobotMotorsBusConfig(
            port="/dev/ttyUSB0",  # Update with your actual port
            baud=115200,
            motors={
                "joint1": [1, "mycobot"],  # Base rotation
                "joint2": [2, "mycobot"],  # Shoulder
                "joint3": [3, "mycobot"],  # Elbow
                "joint4": [4, "mycobot"],  # Wrist rotation
                "joint5": [5, "mycobot"],  # Wrist flex
                "joint6": [6, "mycobot"],  # Gripper rotation
            },
        ),
    }
)

# Create and connect to the robot
robot = ManipulatorRobot(config)
robot.connect()

# Use teleoperation
try:
    while True:
        robot.teleop_step()
except KeyboardInterrupt:
    # Disconnect when done
    robot.disconnect()
```

### Teleoperating the robot

For teleoperation, run:

```bash
python -m lerobot.scripts.control_robot --config-file path/to/your/config.yaml
```

Create a config YAML file with your myCobot settings:

```yaml
# mycobot_config.yaml
robot:
  type: mycobot
  leader_arms:
    main:
      type: mycobot
      port: /dev/ttyUSB0  # Update with your actual port
      baud: 115200
      motors:
        joint1: [1, "mycobot"]
        joint2: [2, "mycobot"]
        joint3: [3, "mycobot"]
        joint4: [4, "mycobot"]
        joint5: [5, "mycobot"]
        joint6: [6, "mycobot"]
  # Optional camera configuration
  cameras:
    laptop:
      type: opencv
      camera_index: 0
      fps: 30
      width: 640
      height: 480
```

### Safety Considerations

The default configuration includes a `max_relative_target` value of 5 degrees, which limits how much the robot can move in a single step. This is a safety feature to prevent large, sudden movements. When you're comfortable with the robot's operation, you can increase this value or set it to `null` to remove the limit.

## Controlling Individual Joints

You can control individual joints by sending actions to the robot:

```python
import time
import torch
from lerobot.common.robot_devices.robots.configs import MyCobotRobotConfig
from lerobot.common.robot_devices.robots.manipulator import ManipulatorRobot

# Create robot instance
config = MyCobotRobotConfig()
robot = ManipulatorRobot(config)
robot.connect()

try:
    # Create an action tensor (all zeros initially)
    action = torch.zeros(6)
    
    # Set joint1 (base) to 30 degrees
    action[0] = 30.0
    
    # Send action to robot
    robot.send_action(action)
    
    # Wait for movement to complete
    time.sleep(2)
    
    # Return to zero position
    robot.send_action(torch.zeros(6))
    
finally:
    # Always disconnect when done
    robot.disconnect()
```

## Troubleshooting

### Communication Issues

If you're having trouble connecting to the robot:

1. Check that the port is correct and the robot is powered on
2. Verify that you have the correct permissions to access the port
3. Try using `mock=True` in your configuration for testing without a physical robot
4. Ensure you have the latest version of pymycobot

### Robot Not Moving

If the robot isn't responding to commands:

1. Check that the robot is powered on and the motors are enabled
2. Verify that your action values are within the robot's range of motion
3. Increase the `max_relative_target` value if movements are too small

## Calibration

For advanced usage, you may need to calibrate your myCobot. The platform expects calibration files in the `.cache/calibration/mycobot` directory. If you need to create custom calibrations, refer to the LeRobot documentation on robot calibration.

## Advanced Features

### Controlling the Gripper

The myCobot implementation includes a method to control the gripper:

```python
# Access the underlying motor bus
motors_bus = robot.follower_arms["main"]

# Close the gripper (True = close, False = open)
motors_bus.set_gripper(True)

# Open the gripper
motors_bus.set_gripper(False)
```

### Setting LED Color

You can control the LED color on the myCobot:

```python
# RGB values (0-255)
motors_bus.write_led((255, 0, 0))  # Red
motors_bus.write_led((0, 255, 0))  # Green
motors_bus.write_led((0, 0, 255))  # Blue
```

## Next Steps

1. Explore LeRobot's dataset creation capabilities with your myCobot
2. Train policies for autonomous operation
3. Integrate with computer vision for object detection and manipulation
