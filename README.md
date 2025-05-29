# LeRobot - Individual Arm Control Edition

白アームと黒アームを個別制御できる機能を追加したLeRobotプロジェクトです。

## 🚀 主な機能

### 個別アーム制御
- **白アーム（white set）** または **黒アーム（black set）** を個別に選択
- 各アームで独立したキャリブレーション、テレオペレーション、データ記録が可能
- 動的なポート設定とカメラ設定

### サポートする操作
- **キャリブレーション**: アームの初期設定とモーター調整
- **テレオペレーション**: リーダーアームを使ったリアルタイム制御
- **データ記録**: テレオペレーションデータの記録とデータセット作成

## 📁 プロジェクト構造

```
xtl_lerobot/
├── README.md                          # このファイル
├── README_ORIGINAL.md                  # 元のLeRobotのREADME
├── control_single_arm.py              # 🆕 個別アーム制御スクリプト
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

## 🎯 使用方法

### 1. 個別アームキャリブレーション

```bash
# 白アームのキャリブレーション
python control_single_arm.py --robot_set white --control_type calibrate

# 黒アームのキャリブレーション
python control_single_arm.py --robot_set black --control_type calibrate

# カメラなしのキャリブレーション（軽量・高速）
python control_single_arm.py --robot_set white --control_type calibrate --no-cameras
python control_single_arm.py --robot_set black --control_type calibrate --no-cameras
```

**キャリブレーション時の注意点:**
- 指定したアームセットのフォロワーアームのみを物理的に接続してください
- キャリブレーション中は画面の指示に従ってアームを手動で動かしてください
- 通常モード: フォロワー手首カメラを使用（視覚的な確認が可能）
- カメラなしモード（`--no-cameras`）: カメラを使わず、より高速で軽量な処理
- キャリブレーションデータは `.cache/calibration/so100_{robot_set}/` に保存されます

### 2. テレオペレーション

```bash
# 白アームのテレオペレーション
python control_single_arm.py --robot_set white --control_type teleoperate

# 黒アームのテレオペレーション  
python control_single_arm.py --robot_set black --control_type teleoperate

# カメラなしのテレオペレーション（高速・軽量）
python control_single_arm.py --robot_set white --control_type teleoperate --no-cameras
python control_single_arm.py --robot_set black --control_type teleoperate --no-cameras
```

**テレオペレーション時の注意点:**
- リーダーアームとフォロワーアームの両方を接続してください
- 通常モード: 全カメラ（リーダー手首、フォロワー手首、俯瞰、横視点）が使用されます
- カメラなしモード（`--no-cameras`）: カメラを使わず、より高速で軽量な制御が可能
- `Ctrl+C` で終了します

### 3. データ記録

```bash
# 白アームで30秒間のデータ記録
python control_single_arm.py --robot_set white --control_type record --duration 30

# 黒アームで60秒間のデータ記録
python control_single_arm.py --robot_set black --control_type record --duration 60

# カメラなしでのデータ記録（関節データのみ）
python control_single_arm.py --robot_set white --control_type record --duration 30 --no-cameras
python control_single_arm.py --robot_set black --control_type record --duration 60 --no-cameras
```

**記録されるデータ:**
- ロボットアームの関節位置と動作
- 通常モード: 全カメラからの画像データ（30 FPS）
- カメラなしモード（`--no-cameras`）: 関節データのみ（画像なし、軽量・高速）
- データセットは `./lerobot_data/` ディレクトリに保存

### 4. デュアルアームキャリブレーション（従来機能）

```bash
# 左右両方のフォロワーアームを順次キャリブレーション
./calibrate_so100_followers.sh
```

### 高速・軽量ワークフロー（カメラなし）

```bash
# 1. 白アームのキャリブレーション（カメラなし、高速）
python control_single_arm.py --robot_set white --control_type calibrate --no-cameras

# 2. カメラなしテレオペレーション（高速動作確認）
python control_single_arm.py --robot_set white --control_type teleoperate --no-cameras

# 3. カメラなしデータ記録（関節データのみ、高速）
for i in {1..20}; do
    echo "Recording episode $i (no cameras)..."
    python control_single_arm.py --robot_set white --control_type record --duration 15 --no-cameras
    echo "Episode $i completed. Reset environment for next episode."
    read -p "Press Enter to continue..."
done
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
lerobot_data/
└── so100_dataset_{robot_set}_{timestamp}/
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
- **task**: タスク記述（空文字列）

## 🛠️ 開発・カスタマイズ

### 新しいロボットセットの追加
1. `so100_robot_settings.json` に新しいセットを追加
2. USBポートとカメラポートを適切に設定
3. 必要に応じてキャリブレーションディレクトリを作成

**設定ファイルのカスタマイズ例:**
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

### カメラ設定の変更
`create_robot_config()` 関数内の `camera_configs` を編集して、解像度やFPSを調整できます。

### FPSの調整
- **テレオペレーション**: ~100Hz（`time.sleep(0.01)`）
- **データ記録**: 60Hz（設定可能）
- **カメラなしモード**: より高いFPSと低い遅延を実現可能

### カメラなしモードのメリット
- **高速処理**: カメラ処理のオーバーヘッドなし
- **低遅延**: リアルタイム制御の応答性向上
- **軽量**: メモリとCPU使用量の削減
- **シンプルデバッグ**: 関節データのみに集中

## 🚨 トラブルシューティング

### 一般的な問題

**1. Python環境エラー**
```
TypeError: 'type' object is not subscriptable
```
→ conda環境がアクティベートされていない可能性があります：
```bash
conda activate lerobot
python --version  # Python 3.10.13が表示されることを確認
```

**2. ポート接続エラー**
```
Error loading robot/camera ports: Robot set 'white' not found in settings file
```
→ `so100_robot_settings.json` の設定を確認してください

**3. カメラ接続エラー**
```
Camera connection failed
```
→ カメラポート番号とデバイス接続を確認してください

**4. モーター接続エラー**
```
Motor connection failed
```
→ USBポートとアーム電源を確認してください

### デバッグ方法
```bash
# Python環境の確認
conda activate lerobot
python --version
which python

# ポート設定の確認
python -c "from lerobot.common.robot_config_utils import load_robot_ports; print(load_robot_ports('white'))"

# 利用可能なカメラの確認
ls /dev/video*
```

## 🔗 従来機能との互換性

### 元のLeRobotスクリプトも使用可能

```bash
# 元のrecord_dataset.pyスクリプト（robot_set対応）
python lerobot/scripts/record_dataset.py --robot_set white --duration 30

# 元のcontrol_robot.pyスクリプト
python lerobot/scripts/control_robot.py --robot.type=so100 --control.type=calibrate
```

### 移行されたファイル一覧

#### 🆕 新規作成
- `control_single_arm.py` - 統合個別アーム制御スクリプト
- `lerobot/common/robot_config_utils.py` - 設定読み込みユーティリティ

#### 📋 コピー・移行されたファイル
- `lerobot/configs/so100_robot_settings.json` - ポート設定（~/lerobotから移行）
- `lerobot/scripts/record_dataset.py` - robot_set対応記録スクリプト（~/lerobotから移行）
- `calibrate_so100_followers.sh` - デュアルアーム用キャリブレーション（~/lerobotから移行）
- `.cache/calibration/so100_dual_replay/` - キャリブレーションデータ（~/lerobotから移行）

## 💡 実用例

### 典型的なワークフロー

```bash
# 1. 白アームのキャリブレーション
python control_single_arm.py --robot_set white --control_type calibrate

# 2. 白アームでテレオペレーションの練習
python control_single_arm.py --robot_set white --control_type teleoperate

# 3. データ記録（複数エピソード）
for i in {1..10}; do
    echo "Recording episode $i..."
    python control_single_arm.py --robot_set white --control_type record --duration 30
    echo "Episode $i completed. Reset environment for next episode."
    read -p "Press Enter to continue..."
done
```

### 高速・軽量ワークフロー（カメラなし）

```bash
# 1. 白アームのキャリブレーション（カメラなし、高速）
python control_single_arm.py --robot_set white --control_type calibrate --no-cameras

# 2. カメラなしテレオペレーション（高速動作確認）
python control_single_arm.py --robot_set white --control_type teleoperate --no-cameras

# 3. カメラなしデータ記録（関節データのみ、高速）
for i in {1..20}; do
    echo "Recording episode $i (no cameras)..."
    python control_single_arm.py --robot_set white --control_type record --duration 15 --no-cameras
    echo "Episode $i completed. Reset environment for next episode."
    read -p "Press Enter to continue..."
done
```

### カメラありとなしの使い分け

| **操作** | **カメラあり** | **カメラなし** |
|---------|-------------|-------------|
| **キャリブレーション** | 視覚的確認が可能、正確性重視 | 高速処理、軽量、デバッグ時 |
| **テレオペレーション** | 画像フィードバック、精密作業 | 高速応答、軽量、動作テスト |
| **データ記録** | 完全なデータセット（画像+関節） | 関節データのみ、高速収集 |

## 📝 更新履歴

### v1.0 - Individual Arm Control Edition
- 🆕 個別アーム制御機能の追加
- 🆕 動的設定読み込み機能
- 🆕 アームセット別キャリブレーション
- 🆕 統合制御スクリプト `control_single_arm.py`
- 📁 元のLeRobotからのデータ移行完了

## 📞 サポート

問題が発生した場合は、以下を確認してください：
1. ハードウェア接続（USB、電源、カメラ）
2. 設定ファイルの内容
3. キャリブレーションファイルの存在
4. ログ出力の詳細

---

**元のLeRobotドキュメント**: `README_ORIGINAL.md` を参照してください。 