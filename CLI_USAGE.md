# CLI 使用ガイド

アクティビティファイル（GPX/TCX/FIT）を動画に変換するコマンドラインツールの使用方法です。

## インストール

### 方法1: ラッパースクリプトを使用（推奨）

**Linux/Mac:**
```bash
# 実行権限を付与（初回のみ）
chmod +x convert.sh

# 使用
./convert.sh input.gpx
```

**Windows:**
```cmd
convert.bat input.gpx
```

ラッパースクリプトは自動的に仮想環境を作成し、必要なパッケージをインストールします。

### 方法2: 直接Pythonで実行

```bash
cd backend

# 仮想環境の作成（初回のみ）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール（初回のみ）
pip install -r requirements.txt

# CLIツールの実行
python cli.py input.gpx
```

## 基本的な使い方

### 最もシンプルな変換

```bash
# GPXファイルを同名のMP4ファイルに変換
./convert.sh activity.gpx
# → activity.mp4 が生成されます

# TCXファイル
./convert.sh workout.tcx
# → workout.mp4 が生成されます

# FITファイル
./convert.sh ride.fit
# → ride.mp4 が生成されます
```

### 出力ファイル名を指定

```bash
./convert.sh input.gpx -o output.mp4

# または
./convert.sh input.gpx --output /path/to/output.mp4
```

### 動画設定のカスタマイズ

```bash
# HD解像度 (1280x720) 60FPS
./convert.sh input.gpx -o output.mp4 --width 1280 --height 720 --fps 60

# 4K解像度 (3840x2160) 30FPS
./convert.sh input.gpx -o output.mp4 --width 3840 --height 2160 --fps 30
```

### 詳細な出力を表示

```bash
./convert.sh input.gpx -v

# または
./convert.sh input.gpx --verbose
```

## オプション一覧

```
使用法: cli.py [-h] [-o OUTPUT] [--width WIDTH] [--height HEIGHT] [--fps FPS] [-v] input

位置引数:
  input                 入力アクティビティファイル (GPX/TCX/FIT)

オプション引数:
  -h, --help           ヘルプメッセージを表示
  -o OUTPUT, --output OUTPUT
                       出力動画ファイルパス (デフォルト: <入力ファイル名>.mp4)
  --width WIDTH        動画の幅（ピクセル）(デフォルト: 1920)
  --height HEIGHT      動画の高さ（ピクセル）(デフォルト: 1080)
  --fps FPS            動画のフレームレート (デフォルト: 30)
  -v, --verbose        詳細な出力を表示
```

## 使用例

### 例1: 基本的な変換

```bash
./convert.sh morning_run.gpx
```

出力:
```
Video generated: morning_run.mp4
```

### 例2: 詳細モードで変換

```bash
./convert.sh morning_run.gpx -v
```

出力:
```
============================================================
Activity Video Generator
============================================================
Parsing .gpx file: morning_run.gpx
✓ Parsed successfully
  Points: 1234
  Duration: 1823.50 seconds
  Distance: 5.42 km
  Max Speed: 12.34 km/h

Generating video...
  Output: morning_run.mp4
  Resolution: 1920x1080
  FPS: 30
✓ Video generated successfully: morning_run.mp4
  File size: 45.67 MB
============================================================
Done!
============================================================
```

### 例3: カスタム設定での変換

```bash
./convert.sh cycling.fit -o videos/cycling_hd.mp4 --width 1280 --height 720 --fps 60 -v
```

### 例4: 複数ファイルの一括変換（バッチ処理）

**Linux/Mac:**
```bash
# すべてのGPXファイルを変換
for file in *.gpx; do
    ./convert.sh "$file" -v
done

# 特定のディレクトリ内のファイルを変換
for file in activities/*.{gpx,tcx,fit}; do
    if [ -f "$file" ]; then
        ./convert.sh "$file" -o "videos/$(basename "$file" | sed 's/\.[^.]*$/.mp4/')"
    fi
done
```

**Windows (PowerShell):**
```powershell
# すべてのGPXファイルを変換
Get-ChildItem *.gpx | ForEach-Object {
    .\convert.bat $_.FullName -v
}

# 特定のディレクトリ内のファイルを変換
Get-ChildItem activities\* -Include *.gpx,*.tcx,*.fit | ForEach-Object {
    $output = "videos\" + $_.BaseName + ".mp4"
    .\convert.bat $_.FullName -o $output
}
```

## 生成される動画の内容

動画には以下の情報が表示されます:

- **上部中央**: 経過時間 (HH:MM:SS形式)
- **右上**: 現在の速度 (km/h)
- **左上**: 累積距離 (km)
- **左下**: 標高 (m)
- **右下**: 心拍数 (データがある場合)
- **中央**: GPS座標 (緯度・経度)
- **下部中央**: 平均速度・最高速度

## トラブルシューティング

### エラー: 入力ファイルが見つからない

```bash
Error: Input file not found: activity.gpx
```

→ ファイルパスが正しいか確認してください。

### エラー: サポートされていないファイル形式

```bash
Error: Unsupported file type: .txt. Supported types: .gpx, .tcx, .fit
```

→ GPX、TCX、FITファイルのみサポートされています。

### エラー: メモリ不足

長時間のアクティビティで動画生成中にメモリ不足になる場合:

```bash
# FPSを下げる
./convert.sh input.gpx --fps 15

# 解像度を下げる
./convert.sh input.gpx --width 1280 --height 720
```

### エラー: ffmpegが見つからない

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html からダウンロードしてインストール
```

### エラー: フォントが見つからない

```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu-core

# macOS（通常は不要）
# システムフォントが使用されます

# Windows（通常は不要）
# システムフォントが使用されます
```

## パフォーマンスに関する注意

- **長時間のアクティビティ**: 数時間のアクティビティは大きな動画ファイルになります
- **高解像度・高FPS**: 処理時間とファイルサイズが増加します
- **推奨設定**:
  - 短いアクティビティ（<30分）: 1920x1080 @ 30fps
  - 中程度のアクティビティ（30分-2時間）: 1280x720 @ 30fps
  - 長いアクティビティ（>2時間）: 1280x720 @ 15fps

## Docker環境での使用

Dockerコンテナ内でCLIツールを使用する場合:

```bash
# コンテナに入る
docker-compose exec backend bash

# CLIツールを実行
python cli.py /path/to/input.gpx -o /app/outputs/output.mp4

# または、ホストからファイルをマウントして実行
docker-compose run --rm -v $(pwd)/activities:/data backend python cli.py /data/activity.gpx -o /data/output.mp4
```

## ヘルプの表示

詳しいオプションは以下のコマンドで確認できます:

```bash
./convert.sh --help

# または
cd backend
python cli.py --help
```
