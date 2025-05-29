#!/bin/bash

# So100 フォロワーアーム キャリブレーションスクリプト

LEROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPLAY_DUAL_CALIB_DIR="$LEROOT_DIR/.cache/calibration/so100_dual_replay"
RECORD_DATASET_DEFAULT_CALIB_DIR="$LEROOT_DIR/.cache/calibration/so100"
BACKUP_DIR_BASE="$LEROOT_DIR/.cache/calibration_backup_replay_dual"
SETTINGS_FILE="$LEROOT_DIR/lerobot/configs/so100_robot_settings.json"

PYTHON_EXEC="python"
RECORD_SCRIPT_PATH="$LEROOT_DIR/lerobot/scripts/record_dataset.py"

# jq がインストールされているか確認 (簡易チェック)
if ! command -v jq &> /dev/null
then
    echo "エラー: jq コマンドが見つかりません。このスクリプトは jq を使用して設定ファイルを読み込みます。"
    echo "macOS の場合: brew install jq でインストールしてください。"
    exit 1
fi

# --- 1. 準備 --- 
echo "キャリブレーションの準備を開始します..."

# replay_dual_so100.py が使用するキャリブレーションディレクトリを準備 (既存の場合はバックアップ)
if [ -d "$REPLAY_DUAL_CALIB_DIR" ]; then
  BACKUP_REPLAY_DUAL_DIR="${BACKUP_DIR_BASE}/replay_dual_$(date +%Y%m%d_%H%M%S)"
  echo "既存の $REPLAY_DUAL_CALIB_DIR を $BACKUP_REPLAY_DUAL_DIR にバックアップします。"
  mkdir -p "$BACKUP_DIR_BASE"
  mv "$REPLAY_DUAL_CALIB_DIR" "$BACKUP_REPLAY_DUAL_DIR"
fi
mkdir -p "$REPLAY_DUAL_CALIB_DIR"
echo "replay_dual_so100.py 用のディレクトリ準備完了: $REPLAY_DUAL_CALIB_DIR"

# リーダーアーム用のダミーキャリブレーションファイルを配置
echo "{}" > "$REPLAY_DUAL_CALIB_DIR/left_leader.json"
echo "{}" > "$REPLAY_DUAL_CALIB_DIR/right_leader.json"
echo "リーダーアーム用ダミーファイル配置完了。"

# record_dataset.py が使用するデフォルトのキャリブレーションディレクトリをクリア
if [ -d "$RECORD_DATASET_DEFAULT_CALIB_DIR" ]; then
    echo "既存の $RECORD_DATASET_DEFAULT_CALIB_DIR をクリアします。"
    rm -rf "${RECORD_DATASET_DEFAULT_CALIB_DIR:?}/"*
else
    mkdir -p "$RECORD_DATASET_DEFAULT_CALIB_DIR"
fi
echo "record_dataset.py 用のデフォルトキャリブレーションディレクトリ準備完了: $RECORD_DATASET_DEFAULT_CALIB_DIR"
echo "準備完了。"
echo ""

# --- 2. 左フォロワーアーム (white set) のキャリブレーション --- 
echo "--- 左フォロワーアーム (white set) のキャリブレーション ---"

WHITE_FOLLOWER_PORT=$(jq -r '.white.follower_port' "$SETTINGS_FILE")
if [ "$WHITE_FOLLOWER_PORT" == "null" ] || [ -z "$WHITE_FOLLOWER_PORT" ]; then
    echo "警告: $SETTINGS_FILE から white set の follower_port を読み取れませんでした。ファイルを確認してください。"
    WHITE_FOLLOWER_PORT_PROMPT="('white' set の follower_port)"
else
    WHITE_FOLLOWER_PORT_PROMPT="(ポート: $WHITE_FOLLOWER_PORT)"
fi

echo "物理的に左フォロワーアーム $WHITE_FOLLOWER_PORT_PROMPT のみを接続してください。"
read -p "接続後、Enterを押してください..."

echo "record_dataset.py を実行します。画面の指示に従ってキャリブレーションを行ってください。"
echo "キャリブレーションファイルはデフォルトで $RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json に保存されます。"
"$PYTHON_EXEC" "$RECORD_SCRIPT_PATH" --robot_set white --calibrate_follower_only

echo "キャリブレーションが完了したら、Enterを押してファイルをコピーします..."
read -p "Enterを押してください..."

if [ -f "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json" ]; then
  cp "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json" "$REPLAY_DUAL_CALIB_DIR/left_follower.json"
  echo "左フォロワーアームのキャリブレーションファイルがコピーされました: $REPLAY_DUAL_CALIB_DIR/left_follower.json"
  # 次のキャリブレーションのために、生成されたファイルをリネームしてバックアップ
  mv "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json" "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower_white_calibrated_$(date +%Y%m%d_%H%M%S).json"
  echo "一時的なキャリブレーションファイル ($RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json) はリネームされました。"
else
  echo "エラー: $RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json が見つかりませんでした。キャリブレーションが正常に完了したか確認してください。"
fi
echo "-------------------------------------------------"
echo ""

# --- 3. 右フォロワーアーム (black set) のキャリブレーション --- 
echo "--- 右フォロワーアーム (black set) のキャリブレーション ---"

BLACK_FOLLOWER_PORT=$(jq -r '.black.follower_port' "$SETTINGS_FILE")
if [ "$BLACK_FOLLOWER_PORT" == "null" ] || [ -z "$BLACK_FOLLOWER_PORT" ]; then
    echo "警告: $SETTINGS_FILE から black set の follower_port を読み取れませんでした。ファイルを確認してください。"
    BLACK_FOLLOWER_PORT_PROMPT="('black' set の follower_port)"
else
    BLACK_FOLLOWER_PORT_PROMPT="(ポート: $BLACK_FOLLOWER_PORT)"
fi

echo "物理的に右フォロワーアーム $BLACK_FOLLOWER_PORT_PROMPT のみを接続してください。"
read -p "接続後、Enterを押してください..."

echo "record_dataset.py を実行します。画面の指示に従ってキャリブレーションを行ってください。"
echo "キャリブレーションファイルはデフォルトで $RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json に保存されます。"
"$PYTHON_EXEC" "$RECORD_SCRIPT_PATH" --robot_set black --calibrate_follower_only

echo "キャリブレーションが完了したら、Enterを押してファイルをコピーします..."
read -p "Enterを押してください..."

if [ -f "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json" ]; then
  cp "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json" "$REPLAY_DUAL_CALIB_DIR/right_follower.json"
  echo "右フォロワーアームのキャリブレーションファイルがコピーされました: $REPLAY_DUAL_CALIB_DIR/right_follower.json"
  # (オプション) 生成されたファイルをリネームしてバックアップ
  mv "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json" "$RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower_black_calibrated_$(date +%Y%m%d_%H%M%S).json"
  echo "一時的なキャリブレーションファイル ($RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json) はリネームされました。"
else
  echo "エラー: $RECORD_DATASET_DEFAULT_CALIB_DIR/main_follower.json が見つかりませんでした。キャリブレーションが正常に完了したか確認してください。"
fi
echo "-------------------------------------------------"
echo ""
echo "全てのフォロワーアームのキャリブレーションが完了しました。"
echo "この後、replay_dual_so100.py を実行して動作を確認してください。"
