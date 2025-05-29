#!/usr/bin/env python3
"""
個別アーム制御スクリプト

白アームまたは黒アームを個別に指定してキャリブレーション、テレオペレーション、
データ記録ができるようにします。

使用例:
# 白アームのキャリブレーション
python control_single_arm.py --robot_set white --control_type calibrate

# 白アームのキャリブレーション（カメラなし）
python control_single_arm.py --robot_set white --control_type calibrate --no-cameras

# 黒アームのテレオペレーション
python control_single_arm.py --robot_set black --control_type teleoperate

# 黒アームのテレオペレーション（カメラなし）
python control_single_arm.py --robot_set black --control_type teleoperate --no-cameras

# 白アームでデータ記録
python control_single_arm.py --robot_set white --control_type record --duration 30

# 白アームでデータ記録（カメラなし）
python control_single_arm.py --robot_set white --control_type record --duration 30 --no-cameras
"""

import argparse
import time
from pathlib import Path

from lerobot.common.robot_devices.cameras.configs import OpenCVCameraConfig
from lerobot.common.robot_devices.motors.configs import FeetechMotorsBusConfig
from lerobot.common.robot_devices.robots.manipulator import ManipulatorRobot
from lerobot.common.robot_devices.robots.configs import So100RobotConfig
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.robot_config_utils import load_robot_ports, load_common_camera_ports


def create_robot_config(robot_set: str, control_type: str, use_cameras: bool = True):
    """指定されたロボットセットに基づいてロボット設定を作成"""
    
    try:
        common_camera_ports = load_common_camera_ports()
        robot_specific_ports = load_robot_ports(robot_set)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Error loading robot/camera ports: {e}")
        return None

    # カメラ設定を動的に生成
    camera_configs = {}
    if use_cameras:
        if control_type == "calibrate":
            # キャリブレーション時はフォロワーアームの手首カメラのみ
            camera_configs = {
                "follower_wrist_camera": OpenCVCameraConfig(
                    robot_specific_ports["follower_wrist_camera_port"], 
                    fps=30, width=640, height=480
                ),
            }
        else:
            # テレオペレーションや記録時は全カメラ
            camera_configs = {
                "leader_wrist_camera": OpenCVCameraConfig(
                    robot_specific_ports["leader_wrist_camera_port"], 
                    fps=30, width=640, height=480
                ),
                "follower_wrist_camera": OpenCVCameraConfig(
                    robot_specific_ports["follower_wrist_camera_port"], 
                    fps=30, width=640, height=480
                ),
                "overhead_camera": OpenCVCameraConfig(
                    common_camera_ports["overhead_camera_port"], 
                    fps=30, width=640, height=480
                ),
                "side_camera": OpenCVCameraConfig(
                    common_camera_ports["side_camera_port"], 
                    fps=30, width=640, height=480
                ),
            }
    # use_cameras=Falseの場合、camera_configs={}のまま（カメラなし）

    # リーダーアームの設定
    leader_arm_config_dict = {}
    if control_type != "calibrate":
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

    # So100ロボット設定にキャリブレーションディレクトリを個別アーム用に設定
    calibration_dir = f".cache/calibration/so100_{robot_set}"
    
    robot_config = So100RobotConfig(
        cameras=camera_configs, 
        leader_arms=leader_arm_config_dict, 
        follower_arms=follower_arm_config_dict,
        calibration_dir=calibration_dir
    )
    
    return robot_config


def calibrate_single_arm(robot_set: str, use_cameras: bool = True):
    """個別アームのキャリブレーション"""
    camera_status = "カメラあり" if use_cameras else "カメラなし"
    print(f"--- {robot_set}アームのキャリブレーション開始 ({camera_status}) ---")
    
    robot_config = create_robot_config(robot_set, "calibrate", use_cameras=use_cameras)
    if robot_config is None:
        return
    
    robot = ManipulatorRobot(robot_config)
    robot.connect()
    print(f"Robot ({robot_set}) connected.")

    # キャリブレーション実行
    robot.activate_calibration()
    print("キャリブレーション完了!")

    robot.disconnect()
    print(f"Robot ({robot_set}) disconnected.")


def teleoperate_single_arm(robot_set: str, use_cameras: bool = True):
    """個別アームのテレオペレーション"""
    camera_status = "カメラあり" if use_cameras else "カメラなし"
    print(f"--- {robot_set}アームのテレオペレーション開始 ({camera_status}) ---")
    print("Ctrl+Cで終了します")
    
    robot_config = create_robot_config(robot_set, "teleoperate", use_cameras=use_cameras)
    if robot_config is None:
        return
    
    robot = ManipulatorRobot(robot_config)
    robot.connect()
    print(f"Robot ({robot_set}) connected.")

    # キャリブレーションを適用
    robot.activate_calibration()
    print("キャリブレーション適用完了. テレオペレーション開始!")

    try:
        while True:
            result = robot.teleop_step(record_data=False)
            # record_data=Falseの場合、teleop_stepはNoneを返すので何もしない
            time.sleep(0.01)  # 約100Hz
    except KeyboardInterrupt:
        print("\nテレオペレーション終了")

    robot.disconnect()
    print(f"Robot ({robot_set}) disconnected.")


def record_single_arm(robot_set: str, duration_s: int, use_cameras: bool = True):
    """個別アームでのデータ記録"""
    camera_status = "カメラあり" if use_cameras else "カメラなし"
    print(f"--- {robot_set}アームのデータ記録開始 ({duration_s}秒間, {camera_status}) ---")
    
    robot_config = create_robot_config(robot_set, "record", use_cameras=use_cameras)
    if robot_config is None:
        return
    
    robot = ManipulatorRobot(robot_config)
    robot.connect()
    print(f"Robot ({robot_set}) connected.")

    # キャリブレーションを適用
    robot.activate_calibration()
    print("キャリブレーション適用完了.")

    # データセット初期化
    dataset_name = f"so100_dataset_{robot_set}_{time.strftime('%Y%m%d_%H%M%S')}"
    datasets_root_dir = Path("./lerobot_data")
    datasets_root_dir.mkdir(parents=True, exist_ok=True)
    repo_id = datasets_root_dir / dataset_name

    print(f"Initializing dataset at: {repo_id}")
    dataset = LeRobotDataset.create(
        repo_id=str(repo_id),
        fps=60,
        features=robot.features,
        robot=robot,
        use_videos=True,
    )

    if any("observation.images" in key for key in robot.features):
        print("Starting image writer...")
        dataset.start_image_writer()

    print("Creating new episode buffer...")
    episode_idx = dataset.create_episode_buffer()
    print(f"Recording episode {episode_idx}...")

    start_time_recording = time.perf_counter()
    for i in range(int(duration_s * 60)):  # 60 FPS
        loop_start_time = time.perf_counter()

        obs_dict, action_dict = robot.teleop_step(record_data=True)
        frame_data = {**obs_dict, **action_dict}
        frame_data["task"] = ""
        dataset.add_frame(frame_data)

        loop_elapsed_time = time.perf_counter() - loop_start_time
        sleep_time = (1.0 / 60) - loop_elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

        # 進捗表示
        if i % 60 == 0:  # 1秒ごとに表示
            elapsed = time.perf_counter() - start_time_recording
            print(f"Recording... {elapsed:.1f}s / {duration_s}s")

    end_time_recording = time.perf_counter()
    print(f"Recording finished. Total duration: {end_time_recording - start_time_recording:.2f}s")

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


def main():
    parser = argparse.ArgumentParser(description="個別アーム制御スクリプト")
    parser.add_argument(
        "--robot_set",
        type=str,
        required=True,
        choices=["white", "black"],
        help="制御するロボットセット ('white' または 'black')"
    )
    parser.add_argument(
        "--control_type",
        type=str,
        required=True,
        choices=["calibrate", "teleoperate", "record"],
        help="実行する制御タイプ"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="記録時間（秒、recordモードのみ）"
    )
    parser.add_argument(
        "--no-cameras",
        action="store_true",
        help="カメラを使用しない（全ての操作で使用可能、高速・軽量動作）"
    )
    
    args = parser.parse_args()

    # カメラ使用フラグを設定
    use_cameras = not args.no_cameras

    if args.control_type == "calibrate":
        calibrate_single_arm(args.robot_set, use_cameras=use_cameras)
    elif args.control_type == "teleoperate":
        teleoperate_single_arm(args.robot_set, use_cameras=use_cameras)
    elif args.control_type == "record":
        record_single_arm(args.robot_set, args.duration, use_cameras=use_cameras)


if __name__ == "__main__":
    main() 