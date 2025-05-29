import json
from pathlib import Path

# 設定ファイルのデフォルトパス (このファイルの2階層上の lerobot/configs/so100_robot_settings.json を指す)
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "so100_robot_settings.json"

def load_robot_ports(robot_set_name: str, config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """
    指定されたロボットセットのアームポートと手首カメラポート設定をJSONファイルから読み込みます。

    Args:
        robot_set_name: ロボットセット名 ("white" または "black")。
        config_path: 設定ファイルのパス。

    Returns:
        指定されたロボットセットのポート情報 (例: {"leader_port": "...", "follower_port": "...", "leader_wrist_camera_port": "...", "follower_wrist_camera_port": "..."})。

    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合。
        KeyError: 指定されたロボットセット名が設定ファイルに存在しない場合。
        ValueError: 設定ファイルが期待される形式でない場合。
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Robot settings file not found: {config_path}")

    with open(config_path, "r") as f:
        try:
            all_settings = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {config_path}: {e}")

    if robot_set_name not in all_settings:
        raise KeyError(f"Robot set '{robot_set_name}' not found in settings file {config_path}. Available sets: {list(all_settings.keys())}")

    ports = all_settings[robot_set_name]
    if not (
        isinstance(ports, dict)
        and "leader_port" in ports
        and "follower_port" in ports
        and "leader_wrist_camera_port" in ports
        and "follower_wrist_camera_port" in ports
    ):
        raise ValueError(
            f"Settings for '{robot_set_name}' in {config_path} are not in the expected format "
            '(must be a dictionary with "leader_port", "follower_port", "leader_wrist_camera_port", and "follower_wrist_camera_port" keys).'
        )
    return ports

def load_common_camera_ports(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """
    共通のカメラポート設定 (俯瞰、横視点) をJSONファイルから読み込みます。

    Args:
        config_path: 設定ファイルのパス。

    Returns:
        共通カメラのポート情報 (例: {"overhead_camera_port": "...", "side_camera_port": "..."})。

    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合。
        KeyError: 必要な共通カメラキーが設定ファイルに存在しない場合。
        ValueError: 設定ファイルが期待される形式でない場合。
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Robot settings file not found: {config_path}")

    with open(config_path, "r") as f:
        try:
            all_settings = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {config_path}: {e}")

    required_keys = ["overhead_camera_port", "side_camera_port"]
    common_camera_ports = {}
    for key in required_keys:
        if key not in all_settings:
            raise KeyError(f"Common camera setting '{key}' not found in settings file {config_path}.")
        common_camera_ports[key] = all_settings[key]
    
    return common_camera_ports
