# LeRobot - Individual Arm Control Edition

白アームと黒アームを個別制御できる機能を追加したLeRobotプロジェクトです。

## 🚀 主な機能

### 個別アーム制御
- **白アーム（white set）** または **黒アーム（black set）** を個別に選択
- 各アームで独立したキャリブレーション、テレオペレーション、データ記録が可能
- 動的なポート設定とカメラ設定
- **公式のLeRobot control_robot.pyと完全互換**

### サポートする操作
- **キャリブレーション**: アームの初期設定とモーター調整
- **テレオペレーション**: リーダーアームを使ったリアルタイム制御
- **データ記録**: テレオペレーションデータの記録とデータセット作成

## 📁 プロジェクト構造

```
xtl_lerobot/
├── README.md                          # このファイル
├── README_ORIGINAL.md                  # 元のLeRobotのREADME
├── control_single_arm.py              # 🆕 個別アーム制御スクリプト（公式互換）
├── calibrate_so100_followers.sh       # デュアルアーム用キャリブレーション
├── lerobot/
│   ├── configs/
│   │   └── so100_robot_settings.json  # 🆕 ロボット設定ファイル
│   ├── common/
│   │   └── robot_config_utils.py      # 🆕 設定読み込みユーティリティ
│   └── scripts/
│       └── record_dataset.py          # robot_set対応記録スクリプト
└── .cache/
    └── calibration/
        ├── so100_dual_replay/          # デュアルアーム用キャリブレーションデータ
        ├── so100_white/               # 白アーム用キャリブレーションデータ
        └── so100_black/               # 黒アーム用キャリブレーションデータ
```

## ⚙️ 設定ファイル

### ロボット設定 (`lerobot/configs/so100_robot_settings.json`)
```json
{
  "overhead_camera_port": 1,
  "side_camera_port": 5,
  "white": {
    "leader_port": "/dev/tty.usbmodem59700732621",
    "follower_port": "/dev/tty.usbmodem58FA0928461",
    "leader_wrist_camera_port": 999,
    "follower_wrist_camera_port": 2
  },
  "black": {
    "leader_port": "/dev/tty.usbmodem5A460832451",
    "follower_port": "/dev/tty.usbmodem5A460853111",
    "leader_wrist_camera_port": 999,
    "follower_wrist_camera_port": 0
  },
  "experimental": {
    "leader_port": "/dev/tty.usbmodem1234567890",
    "follower_port": "/dev/tty.usbmodem0987654321",
    "leader_wrist_camera_port": 999,
    "follower_wrist_camera_port": 3
  }
}
```

## 🎯 使用方法（公式互換モード）

### ⚡ クイックスタート（推奨）

**環境変数を使った簡単実行（推奨）**

```bash
# 白アームのキャリブレーション（動作確認済み）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate

# 黒アームのキャリブレーション（動作確認済み）
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=calibrate

# 白アームのテレオペレーション（動作確認済み）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate

# 黒アームのテレオペレーション（動作確認済み）
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=teleoperate

# カメラなし高速モード（動作確認済み）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=calibrate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=teleoperate

# データ記録（白アーム、30秒間）
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Pick and place task" \
    --control.repo_id=test/white_arm_data \
    --control.episode_time_s=30 \
    --control.num_episodes=1
```

### 1. 個別アームキャリブレーション

**基本的なキャリブレーション**
```bash
# 白アーム（動作確認済み）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate

# 黒アーム（動作確認済み）
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=calibrate

# カメラなしキャリブレーション（高速・軽量）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=calibrate
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=calibrate

# コマンドライン引数での指定も可能
python control_single_arm.py --robot.type=so100 --robot_set=white --control.type=calibrate
python control_single_arm.py --robot.type=so100 --robot_set=black --control.type=calibrate
```

**キャリブレーション時の重要な注意点:**
- ✅ **指定したアームセットのUSBケーブルを接続してください**
- ✅ **リーダーとフォロワーの両方のアームを接続**
- ✅ **画面の指示に従ってアームを手動で動かしてください**
- ✅ キャリブレーションデータは `.cache/calibration/so100_{robot_set}/` に保存されます
- 💡 **カメラなしモード**: `--robot.cameras='{}'`で高速キャリブレーション

### 2. テレオペレーション

**基本的なテレオペレーション**
```bash
# 白アーム（動作確認済み）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate

# 黒アーム（動作確認済み）  
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=teleoperate

# カメラなしテレオペレーション（高速・軽量、動作確認済み）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=teleoperate
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=teleoperate

# FPS制限あり（推奨）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate --control.fps=30
```

**テレオペレーション時の注意点:**
- ✅ **リーダーアームとフォロワーアームの両方を接続**
- ✅ **事前にキャリブレーションを完了させてください**
- ✅ `Ctrl+C` で安全に終了します
- 💡 **カメラなしモード**: `--robot.cameras='{}'`で高速・軽量な制御

### 3. データ記録

**基本的なデータ記録**
```bash
# 白アームで30秒間のデータ記録（動作確認済み）
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Pick and place task" \
    --control.repo_id=test/white_arm_data \
    --control.episode_time_s=30 \
    --control.num_episodes=1 \
    --control.fps=30

# 黒アームで60秒間のデータ記録
ROBOT_SET=black python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Another task" \
    --control.repo_id=test/black_arm_data \
    --control.episode_time_s=60 \
    --control.num_episodes=1 \
    --control.fps=30

# 高速データ記録（高FPS、短時間）
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Test task" \
    --control.repo_id=test/white_fast \
    --control.episode_time_s=15 \
    --control.num_episodes=1 \
    --control.fps=60

# カメラなしデータ記録（関節データのみ、超高速）
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --robot.cameras='{}' \
    --control.type=record \
    --control.single_task="Joints only task" \
    --control.repo_id=test/joints_only \
    --control.episode_time_s=15 \
    --control.num_episodes=1 \
    --control.fps=120
```

**記録されるデータ:**
- ✅ ロボットアームの関節位置と動作
- ✅ カメラ画像データ（指定FPS）
- ✅ タスク記述とメタデータ
- ✅ データセットは指定された`--control.repo_id`ディレクトリに保存

### 4. デュアルアームキャリブレーション（従来機能）

```bash
# 左右両方のフォロワーアームを順次キャリブレーション
./calibrate_so100_followers.sh
```

### 💡 実用的なワークフロー例

**典型的な作業の流れ**

```bash
# 1. 白アームのキャリブレーション
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate

# 2. 操作の練習
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate

# 3. データ記録（複数エピソード）
for i in {1..5}; do
    echo "Recording episode $i..."
    ROBOT_SET=white python control_single_arm.py \
        --robot.type=so100 \
        --control.type=record \
        --control.single_task="Training episode $i" \
        --control.repo_id=dataset/white_training \
        --control.episode_time_s=30 \
        --control.num_episodes=1 \
        --control.fps=30
    echo "Episode $i completed. Reset environment for next episode."
    read -p "Press Enter to continue..."
done
```

**高速テスト用ワークフロー**

```bash
# ハードウェア動作確認（短時間）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate --control.fps=60
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=record --control.single_task="Quick test" --control.repo_id=test/quick --control.episode_time_s=10 --control.num_episodes=1 --control.fps=60

# 超高速テスト（カメラなし）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=calibrate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=teleoperate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --robot.cameras='{}' --control.type=record --control.single_task="No camera test" --control.repo_id=test/no_camera --control.episode_time_s=10 --control.num_episodes=1 --control.fps=120
```

### 🔄 アーム切り替えの方法

```bash
# 白アームから黒アームに切り替える場合
# 1. 白アームのUSBケーブルを外す
# 2. 黒アームのUSBケーブルを接続
# 3. 黒アーム用のキャリブレーション実行
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=calibrate

# 4. 黒アームでテレオペレーション開始
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=teleoperate
```

### 🛠️ 高度な設定例

```bash
# FPS制限とデータ表示を有効にしたテレオペレーション
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=teleoperate \
    --control.fps=30 \
    --control.display_data=true

# 高度なデータ記録設定
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Advanced manipulation task" \
    --control.repo_id=my_dataset/white_advanced \
    --control.fps=30 \
    --control.warmup_time_s=5 \
    --control.episode_time_s=45 \
    --control.reset_time_s=15 \
    --control.num_episodes=10 \
    --control.video=true \
    --control.display_data=true \
    --control.play_sounds=true

# 特定のアームのみキャリブレーション
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=calibrate \
    --control.arms='["main_follower"]'
```

## 🔧 セットアップ

### 前提条件
- Python 3.10+ (conda環境推奨)
- jq (設定ファイル読み込み用)
  ```bash
  # macOS
  brew install jq
  
  # Ubuntu/Debian
  sudo apt-get install jq
  ```

### インストール
```bash
# リポジトリをクローン
git clone <repository-url> xtl_lerobot
cd xtl_lerobot

# conda環境をアクティベート（重要！）
conda activate lerobot

# 依存関係をインストール
pip install -e .
```

### ⚠️ 重要：実行前の準備
スクリプトを実行する前に、**必ず**conda環境をアクティベートしてください：

```bash
conda activate lerobot
```

### ハードウェア接続
1. **USBポートの確認**: `so100_robot_settings.json` でポート設定を確認
2. **アーム接続**: 使用するアームセット（white/black）のリーダーとフォロワーを接続
3. **カメラ接続**: 必要に応じてカメラを接続

## 📊 データ形式

### 記録されるデータセット構造
```
{control.repo_id}/
├── meta.json                    # データセットメタデータ
├── data/                       
│   └── train.parquet           # 関節データ・アクションデータ
└── videos/
    ├── episode_000000/         # エピソードごとの動画
    │   ├── leader_wrist_camera.mp4
    │   ├── follower_wrist_camera.mp4
    │   ├── overhead_camera.mp4
    │   └── side_camera.mp4
    └── ...
```

### データフィールド
- **observation.state**: フォロワーアームの関節位置
- **action**: リーダーアームの関節位置（制御指令）
- **observation.images.{camera_name}**: 各カメラからの画像データ
- **task**: タスク記述（`--control.single_task`で指定）

## 🛠️ 公式機能との互換性

### 全ての公式パラメータサポート

```bash
# 標準的な使用方法（推奨）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=record --control.single_task="Task" --control.repo_id=test/data

# 高度な設定例
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Advanced task" \
    --control.repo_id=my_dataset/white_arm \
    --control.fps=30 \
    --control.episode_time_s=45 \
    --control.num_episodes=10 \
    --control.video=true \
    --control.display_data=true \
    --control.play_sounds=true
```

### 元のLeRobotスクリプトとの併用

```bash
# 元のcontrol_robot.pyスクリプト（デュアルアーム）
python lerobot/scripts/control_robot.py --robot.type=so100 --control.type=calibrate

# 新しい個別制御スクリプト（単一アーム）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate
```

## 💡 実用例

### 基本的な学習データ収集

```bash
# 1. キャリブレーション
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate

# 2. 操作練習
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate

# 3. 学習データ収集
ROBOT_SET=white python control_single_arm.py \
    --robot.type=so100 \
    --control.type=record \
    --control.single_task="Pick and place cups" \
    --control.repo_id=datasets/cup_picking \
    --control.episode_time_s=30 \
    --control.num_episodes=50 \
    --control.fps=30
```

### 研究・開発用の高速プロトタイピング

```bash
# 機能テスト（短時間設定）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=teleoperate --control.fps=60
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=record --control.single_task="Prototype test" --control.repo_id=test/prototype --control.episode_time_s=10 --control.num_episodes=5 --control.fps=60
```

### アーム間の比較実験

```bash
# 白アームでのデータ収集
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=record --control.single_task="Task A" --control.repo_id=experiment/white_data --control.episode_time_s=30 --control.num_episodes=20

# 黒アームでのデータ収集
ROBOT_SET=black python control_single_arm.py --robot.type=so100 --control.type=record --control.single_task="Task A" --control.repo_id=experiment/black_data --control.episode_time_s=30 --control.num_episodes=20
```

## 🚨 トラブルシューティング

### よくある問題と解決方法

**1. Python環境エラー**
```
TypeError: 'type' object is not subscriptable
```
→ conda環境が正しくアクティベートされていない：
```bash
conda activate lerobot
python --version  # Python 3.10.13が表示されることを確認
```

**2. シリアルポート接続エラー**
```
SerialException: could not open port /dev/tty.usbmodem...
```
→ アームのUSB接続とポート設定を確認：
```bash
# ポート設定の確認
cat lerobot/configs/so100_robot_settings.json

# 接続可能なポートの確認
ls /dev/tty.usbmodem*

# ポート自動検出
python lerobot/scripts/find_motors_bus_port.py
```

**3. キャリブレーションファイルが見つからない**
```
Calibration file not found '.cache/calibration/so100_white/...'
```
→ 正常な動作です。初回キャリブレーション時に自動作成されます

**4. 設定ファイルが見つからない**
```
Error loading robot/camera ports: Robot set 'white' not found
```
→ 設定ファイルの確認：
```bash
# 設定ファイルの存在確認
ls -la lerobot/configs/so100_robot_settings.json

# 設定内容の確認
cat lerobot/configs/so100_robot_settings.json
```

### デバッグ用コマンド

```bash
# Python環境の確認
conda activate lerobot
python --version
which python

# 設定読み込みテスト
python -c "from lerobot.common.robot_config_utils import load_robot_ports; print(load_robot_ports('white'))"

# キャリブレーション状態確認
ls -la .cache/calibration/so100_white/

# 利用可能なUSBポート確認
ls /dev/tty.usbmodem*
```

### 推奨される解決手順

1. **環境変数を使用した実行**（推奨）
   ```bash
   ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate
   ```

2. **ハードウェア接続の確認**
   - USBケーブルの接続
   - アーム電源の確認
   - 正しいロボットセット（white/black）のアームが接続されているか

3. **設定ファイルの確認**
   ```bash
   cat lerobot/configs/so100_robot_settings.json
   ```

## 📝 更新履歴

### v2.2 - Production Ready
- ✅ **動作確認済み**: 環境変数`ROBOT_SET`での個別アーム制御
- ✅ **READMEの大幅改善**: 実用的で分かりやすい使用例とワークフロー
- ✅ **エラーハンドリング改善**: 詳細なトラブルシューティングガイド
- 🛠️ **デバッグ情報削除**: プロダクション用のクリーンなコード

### v2.1 - Argument Parsing Fixed
- 🔧 `--robot_set`引数パースエラーを修正
- 🆕 環境変数`ROBOT_SET`による実行サポート
- 📖 使用方法とトラブルシューティングの改善

### v2.0 - Official Compatibility Edition
- 🆕 公式LeRobot control_robot.pyとの完全互換性
- 🆕 Hydra設定システム対応
- 🆕 `@safe_disconnect`デコレーター使用
- 🆕 公式の`control_loop()`、`record()`、`calibrate()`関数使用
- 🆕 全ての公式パラメータサポート
- 📁 設定ファイル読み込み機能強化

### v1.0 - Individual Arm Control Edition
- 🆕 個別アーム制御機能の追加
- 🆕 動的設定読み込み機能
- 🆕 アームセット別キャリブレーション
- 🆕 統合制御スクリプト `control_single_arm.py`
- 📁 元のLeRobotからのデータ移行完了

## 📞 サポート

### 推奨実行方法

```bash
# 環境変数を使用した実行（最も確実）
ROBOT_SET=white python control_single_arm.py --robot.type=so100 --control.type=calibrate
```

### 問題が発生した場合の確認項目

1. **conda環境**: `conda activate lerobot`でPython 3.10.13を使用
2. **設定ファイル**: `lerobot/configs/so100_robot_settings.json`の存在と内容
3. **ハードウェア**: USBケーブル接続、アーム電源、正しいロボットセット
4. **キャリブレーション**: キャリブレーションファイルの存在確認
5. **ポート確認**: `ls /dev/tty.usbmodem*`で利用可能ポート確認

---

**元のLeRobotドキュメント**: `README_ORIGINAL.md` を参照してください。 