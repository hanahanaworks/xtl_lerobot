#!/usr/bin/env python3
"""
Individual Arm Control Script - Based on LeRobot's control_robot.py

This script extends the official LeRobot control_robot.py to support individual arm control
for white and black robot sets.

Examples:
# Calibrate white arm
python control_single_arm.py --robot.type=so100 --robot_set=white --control.type=calibrate

# Calibrate white arm without cameras (fast mode)
python control_single_arm.py --robot.type=so100 --robot_set=white --control.type=calibrate --robot.cameras='{}'

# Teleoperate black arm
python control_single_arm.py --robot.type=so100 --robot_set=black --control.type=teleoperate

# Record with white arm for 30 seconds
python control_single_arm.py --robot.type=so100 --robot_set=white --control.type=record --control.single_task="Pick and place task" --control.repo_id=test/white_arm_data --control.episode_time_s=30 --control.num_episodes=1
"""

import logging
import sys
import os
from dataclasses import asdict
from pprint import pformat

from lerobot.common.robot_devices.cameras.configs import OpenCVCameraConfig
from lerobot.common.robot_devices.control_configs import (
    CalibrateControlConfig,
    ControlPipelineConfig,
    RecordControlConfig,
    TeleoperateControlConfig,
)
from lerobot.common.robot_devices.control_utils import control_loop, record_episode, warmup_record, reset_environment, stop_recording, init_keyboard_listener
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig
from lerobot.common.robot_devices.robots.configs import So100RobotConfig
from lerobot.common.robot_devices.robots.utils import make_robot_from_config
from lerobot.common.robot_devices.utils import safe_disconnect
from lerobot.common.utils.utils import init_logging, log_say, has_method
from lerobot.common.robot_config_utils import load_robot_ports, load_common_camera_ports
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.policies.factory import make_policy
from lerobot.configs import parser


def customize_robot_config_for_single_arm(robot_config: So100RobotConfig, robot_set: str):
    """Customize robot config for single arm control based on robot_set"""
    try:
        common_camera_ports = load_common_camera_ports()
        robot_specific_ports = load_robot_ports(robot_set)
    except (FileNotFoundError, KeyError, ValueError) as e:
        raise ValueError(f"Error loading robot/camera ports for set '{robot_set}': {e}")
    
    # Update calibration directory to be robot_set specific
    robot_config.calibration_dir = f".cache/calibration/so100_{robot_set}"
    
    # Update camera configurations with dynamic ports
    if robot_config.cameras:
        # Only include cameras that are specified in the config
        new_cameras = {}
        for camera_name, camera_config in robot_config.cameras.items():
            if camera_name == "leader_wrist_camera":
                new_cameras[camera_name] = OpenCVCameraConfig(
                    camera_index=robot_specific_ports["leader_wrist_camera_port"],
                    fps=camera_config.fps,
                    width=camera_config.width,
                    height=camera_config.height,
                )
            elif camera_name == "follower_wrist_camera":
                new_cameras[camera_name] = OpenCVCameraConfig(
                    camera_index=robot_specific_ports["follower_wrist_camera_port"],
                    fps=camera_config.fps,
                    width=camera_config.width,
                    height=camera_config.height,
                )
            elif camera_name == "overhead_camera":
                new_cameras[camera_name] = OpenCVCameraConfig(
                    camera_index=common_camera_ports["overhead_camera_port"],
                    fps=camera_config.fps,
                    width=camera_config.width,
                    height=camera_config.height,
                )
            elif camera_name == "side_camera":
                new_cameras[camera_name] = OpenCVCameraConfig(
                    camera_index=common_camera_ports["side_camera_port"],
                    fps=camera_config.fps,
                    width=camera_config.width,
                    height=camera_config.height,
                )
            else:
                # Keep other cameras as-is
                new_cameras[camera_name] = camera_config
        robot_config.cameras = new_cameras
        
    # Update motor configurations with dynamic ports
    if robot_config.leader_arms:
        for arm_name, arm_config in robot_config.leader_arms.items():
            if isinstance(arm_config, FeetechMotorsBusConfig):
                arm_config.port = robot_specific_ports["leader_port"]
                
    if robot_config.follower_arms:
        for arm_name, arm_config in robot_config.follower_arms.items():
            if isinstance(arm_config, FeetechMotorsBusConfig):
                arm_config.port = robot_specific_ports["follower_port"]
    
    return robot_config


def parse_and_remove_robot_set():
    """Parse --robot_set from sys.argv and environment variable ROBOT_SET"""
    robot_set = None
    new_argv = []
    
    # First check environment variable
    env_robot_set = os.environ.get('ROBOT_SET')
    if env_robot_set:
        robot_set = env_robot_set
    
    # Then check command line arguments (takes precedence over environment variable)
    i = 0
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith('--robot_set='):
            # Handle --robot_set=value format
            robot_set = arg.split('=', 1)[1]
        elif arg == '--robot_set' and i + 1 < len(sys.argv):
            # Handle --robot_set value format
            robot_set = sys.argv[i + 1]
            i += 1  # Skip the next argument (the value)
        else:
            new_argv.append(arg)
        i += 1
    
    # Update sys.argv to remove robot_set arguments
    sys.argv = new_argv
    
    # Validate robot_set if provided
    if robot_set and robot_set not in ['white', 'black', 'experimental']:
        raise ValueError(f"Invalid robot_set '{robot_set}'. Must be one of: white, black, experimental")
    
    return robot_set


# Parse robot_set before Hydra processes sys.argv
ROBOT_SET = parse_and_remove_robot_set()


########################################################################################
# Control modes (based on official control_robot.py)
########################################################################################

@safe_disconnect
def calibrate(robot, cfg: CalibrateControlConfig):
    """Calibrate robot arms - based on official implementation"""
    arms = robot.available_arms if cfg.arms is None else cfg.arms
    unknown_arms = [arm_id for arm_id in arms if arm_id not in robot.available_arms]
    available_arms_str = " ".join(robot.available_arms)
    unknown_arms_str = " ".join(unknown_arms)

    if arms is None or len(arms) == 0:
        raise ValueError(
            "No arm provided. Use `--control.arms` as argument with one or more available arms.\n"
            f"For instance, to recalibrate all arms add: `--control.arms='[{available_arms_str}]'`"
        )

    if len(unknown_arms) > 0:
        raise ValueError(
            f"Unknown arms provided ('{unknown_arms_str}'). Available arms are `{available_arms_str}`."
        )

    for arm_id in arms:
        arm_calib_path = robot.calibration_dir / f"{arm_id}.json"
        if arm_calib_path.exists():
            print(f"Removing '{arm_calib_path}'")
            arm_calib_path.unlink()
        else:
            print(f"Calibration file not found '{arm_calib_path}'")

    if robot.is_connected:
        robot.disconnect()

    # Calling `connect` automatically runs calibration when the calibration file is missing
    robot.connect()
    robot.disconnect()
    print("Calibration is done! You can now teleoperate and record datasets!")


@safe_disconnect
def teleoperate(robot, cfg: TeleoperateControlConfig):
    """Teleoperate robot - based on official implementation"""
    control_loop(
        robot,
        control_time_s=cfg.teleop_time_s,
        fps=cfg.fps,
        teleoperate=True,
        display_data=cfg.display_data,
    )


@safe_disconnect
def record(robot, cfg: RecordControlConfig):
    """Record episodes - based on official implementation"""
    if cfg.resume:
        dataset = LeRobotDataset(cfg.repo_id, root=cfg.root)
        if len(robot.cameras) > 0:
            dataset.start_image_writer(
                num_processes=cfg.num_image_writer_processes,
                num_threads=cfg.num_image_writer_threads_per_camera * len(robot.cameras),
            )
    else:
        # Create empty dataset or load existing saved episodes
        dataset = LeRobotDataset.create(
            cfg.repo_id,
            cfg.fps,
            root=cfg.root,
            robot=robot,
            use_videos=cfg.video,
            image_writer_processes=cfg.num_image_writer_processes,
            image_writer_threads=cfg.num_image_writer_threads_per_camera * len(robot.cameras),
        )

    # Load pretrained policy
    policy = None if cfg.policy is None else make_policy(cfg.policy, ds_meta=dataset.meta)

    if not robot.is_connected:
        robot.connect()

    listener, events = init_keyboard_listener()

    # Execute a few seconds without recording to:
    # 1. teleoperate the robot to move it in starting position if no policy provided,
    # 2. give times to the robot devices to connect and start synchronizing,
    # 3. place the cameras windows on screen
    enable_teleoperation = policy is None
    log_say("Warmup record", cfg.play_sounds)
    warmup_record(robot, events, enable_teleoperation, cfg.warmup_time_s, cfg.display_data, cfg.fps)

    if has_method(robot, "teleop_safety_stop"):
        robot.teleop_safety_stop()

    recorded_episodes = 0
    while True:
        if recorded_episodes >= cfg.num_episodes:
            break

        log_say(f"Recording episode {dataset.num_episodes}", cfg.play_sounds)
        record_episode(
            robot=robot,
            dataset=dataset,
            events=events,
            episode_time_s=cfg.episode_time_s,
            display_data=cfg.display_data,
            policy=policy,
            fps=cfg.fps,
            single_task=cfg.single_task,
        )

        # Execute a few seconds without recording to give time to manually reset the environment
        # Skip reset for the last episode to be recorded
        if not events["stop_recording"] and (
            (recorded_episodes < cfg.num_episodes - 1) or events["rerecord_episode"]
        ):
            log_say("Reset the environment", cfg.play_sounds)
            reset_environment(robot, events, cfg.reset_time_s, cfg.fps)

        if events["rerecord_episode"]:
            log_say("Re-record episode", cfg.play_sounds)
            events["rerecord_episode"] = False
            events["exit_early"] = False
            dataset.clear_episode_buffer()
            continue

        dataset.save_episode()
        recorded_episodes += 1

        if events["stop_recording"]:
            break

    log_say("Stop recording", cfg.play_sounds, blocking=True)
    stop_recording(robot, listener, cfg.display_data)

    if cfg.push_to_hub:
        dataset.push_to_hub(tags=cfg.tags, private=cfg.private)

    log_say("Exiting", cfg.play_sounds)
    return dataset


@parser.wrap()
def control_single_arm(cfg: ControlPipelineConfig):
    """Main control function - based on official control_robot.py"""
    init_logging()
    
    # Apply single arm customization if robot_set was specified
    if ROBOT_SET:
        if not isinstance(cfg.robot, So100RobotConfig):
            raise ValueError("--robot_set parameter is only supported for so100 robot type")
        
        print(f"Customizing robot configuration for {ROBOT_SET} arm set...")
        
        try:
            cfg.robot = customize_robot_config_for_single_arm(cfg.robot, ROBOT_SET)
        except Exception as e:
            print(f"ERROR: Failed to customize robot config for {ROBOT_SET}: {e}")
            print(f"ERROR: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    logging.info(pformat(asdict(cfg)))

    robot = make_robot_from_config(cfg.robot)

    if isinstance(cfg.control, CalibrateControlConfig):
        calibrate(robot, cfg.control)
    elif isinstance(cfg.control, TeleoperateControlConfig):
        teleoperate(robot, cfg.control)
    elif isinstance(cfg.control, RecordControlConfig):
        record(robot, cfg.control)
    else:
        raise ValueError(f"Unsupported control type: {type(cfg.control)}")

    if robot.is_connected:
        # Disconnect manually to avoid a "Core dump" during process
        # termination due to camera threads not properly exiting.
        robot.disconnect()


if __name__ == "__main__":
    control_single_arm() 