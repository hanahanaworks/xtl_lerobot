import argparse
import time
from pathlib import Path

import torch
from tqdm import tqdm

from lerobot.common.robot_devices.cameras.configs import OpenCVCameraConfig
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig
from lerobot.common.robot_devices.robots.manipulator import ManipulatorRobot
from lerobot.common.robot_devices.robots.configs import So100RobotConfig
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.robot_config_utils import load_robot_ports, load_common_camera_ports

# Default configuration values
FPS = 60

def main(duration_s: int, robot_set: str, calibrate_follower_only: bool):
    # load_robot_ports を使用してポート情報を取得
    try:
        common_camera_ports = load_common_camera_ports()
        robot_specific_ports = load_robot_ports(robot_set)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Error loading robot/camera ports: {e}")
        return

    # カメラ設定を動的に生成
    camera_configs = {}
    if calibrate_follower_only:
        camera_configs = {
            "follower_wrist_camera": OpenCVCameraConfig(robot_specific_ports["follower_wrist_camera_port"], fps=30, width=640, height=480),
        }
    else:
        camera_configs = {
            "leader_wrist_camera": OpenCVCameraConfig(robot_specific_ports["leader_wrist_camera_port"], fps=30, width=640, height=480),
            "follower_wrist_camera": OpenCVCameraConfig(robot_specific_ports["follower_wrist_camera_port"], fps=30, width=640, height=480),
            "overhead_camera": OpenCVCameraConfig(common_camera_ports["overhead_camera_port"], fps=30, width=640, height=480),
            "side_camera": OpenCVCameraConfig(common_camera_ports["side_camera_port"], fps=30, width=640, height=480),
        }

    # リーダーアームの設定
    leader_arm_config_dict = {}
    if not calibrate_follower_only:
        leader_arm_config_dict = {
            "main": FeetechMotorsBusConfig(
                port=robot_specific_ports["leader_port"],
                motors={
                    "shoulder_pan": (1, "sts3215"),
                    "shoulder_lift": (2, "sts3215"),
                    "elbow_flex": (3, "sts3215"),
                    "wrist_flex": (4, "sts3215"),
                    "wrist_roll": (5, "sts3215"),
                    "gripper": (6, "sts3215"),
                },
            )
        }

    # フォロワーアームの設定
    follower_arm_config_dict = {
        "main": FeetechMotorsBusConfig(
            port=robot_specific_ports["follower_port"],
            motors={
                "shoulder_pan": (1, "sts3215"),
                "shoulder_lift": (2, "sts3215"),
                "elbow_flex": (3, "sts3215"),
                "wrist_flex": (4, "sts3215"),
                "wrist_roll": (5, "sts3215"),
                "gripper": (6, "sts3215"),
            },
        )
    }

    robot_config = So100RobotConfig(cameras=camera_configs, leader_arms=leader_arm_config_dict, follower_arms=follower_arm_config_dict)

    robot = ManipulatorRobot(robot_config)
    robot.connect()
    print(f"Robot ({robot_set}) connected.")

    # Activate calibration if files exist, otherwise run calibration
    # TODO(gaku): For follower only calibration, we might need to adjust how activate_calibration works
    # or ensure it can handle an empty leader_arms config.
    robot.activate_calibration()
    print("Calibration activated.")

    if calibrate_follower_only:
        print("Follower-only calibration process finished. Skipping dataset recording.")
        robot.disconnect()
        print(f"Robot ({robot_set}) disconnected (calibration mode).")
        return

    # Dataset Initialization
    dataset_name = f"so100_dataset_{robot_set}_{time.strftime('%Y%m%d_%H%M%S')}" # データセット名にロボットセット名を含める
    datasets_root_dir = Path("./lerobot_data")
    datasets_root_dir.mkdir(parents=True, exist_ok=True)
    repo_id = datasets_root_dir / dataset_name

    print(f"Initializing dataset at: {repo_id}")
    dataset = LeRobotDataset.create(
        repo_id=str(repo_id),
        fps=FPS,
        features=robot.features,
        robot=robot,
        use_videos=True, # Explicitly set use_videos to True as per documentation alignment
    )

    if any("observation.images" in key for key in robot.features):
        print("Starting image writer...")
        dataset.start_image_writer()

    print("Creating new episode buffer...")
    episode_idx = dataset.create_episode_buffer()
    print(f"Recording episode {episode_idx}...")

    start_time_recording = time.perf_counter()
    for _ in tqdm(range(int(duration_s * FPS))):
        loop_start_time = time.perf_counter()

        obs_dict, action_dict = robot.teleop_step(record_data=True)
        frame_data = {**obs_dict, **action_dict}
        frame_data["task"] = ""  # Change from [] to ""
        dataset.add_frame(frame_data)

        loop_elapsed_time = time.perf_counter() - loop_start_time
        sleep_time = (1.0 / FPS) - loop_elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

    end_time_recording = time.perf_counter()
    print(f"Finished recording. Total duration: {end_time_recording - start_time_recording:.2f}s")

    print(f"Saving episode {episode_idx} to {repo_id}...")
    dataset.save_episode()
    print(f"Episode {episode_idx} saved.")

    if any("observation.images" in key for key in robot.features):
        print("Stopping image writer...")
        dataset.stop_image_writer()
        dataset._wait_image_writer()
        print("Image writer stopped.")

    print(f"Dataset saved at: {dataset.meta.root}")

    robot.disconnect()
    print(f"Robot ({robot_set}) disconnected.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record a dataset from the So100 robot.")
    parser.add_argument("--duration", type=int, default=30, help="Duration of the recording in seconds.")
    parser.add_argument(
        "--robot_set",
        type=str,
        default="black", # デフォルトは "black"
        choices=["white", "black"], # ここは固定のままにするか、動的に設定ファイルから取得するか検討
        help="Specify the robot set to use ('white' or 'black')."
    )
    parser.add_argument(
        "--calibrate_follower_only",
        action="store_true",
        help="If set, only configures and connects the follower arm for calibration."
    )
    args = parser.parse_args()

    main(duration_s=args.duration, robot_set=args.robot_set, calibrate_follower_only=args.calibrate_follower_only)