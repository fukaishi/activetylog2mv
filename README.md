# Activity Log to Video (activetylog2mv)

GPX/TCX/FITファイルから動画を生成するWebアプリケーション

## 概要

このアプリケーションは、アクティビティログファイル(GPX、TCX、FIT)をアップロードすると、そのデータを可視化した動画(MP4)を自動生成します。

### 機能

- **ファイル対応形式**: GPX, TCX, FIT
- **認証**: Supabaseによるユーザー認証
- **動画生成**: アクティビティデータを表示した動画ファイル(MP4)を生成
- **表示データ**:
  - 経過時間
  - 速度(現在/平均/最大)
  - 距離(累積)
  - 標高
  - 心拍数(データがある場合)
  - GPS座標

## 技術スタック

### バックエンド
- Python 3.9+
- FastAPI
- MoviePy (動画生成)
- OpenCV
- GPX/TCX/FITパーサー

### フロントエンド
- React 18
- Vite
- Supabase Client

### データベース
- Supabase

## クイックスタート

### CLIツールで即座に変換（推奨）

```bash
# 1. リポジトリをクローン
git clone <repository_url>
cd activetylog2mv

# 2. アクティビティファイルを変換
./convert.sh your_activity.gpx
```

これだけで動画が生成されます！Webサーバーやデータベースの設定は不要です。

### Dockerで全機能を使用

```bash
# 1. 環境変数を設定してアプリを起動
make dev

# 2. Supabase認証情報を設定
# .env, backend/.env, frontend/.env を編集

# 3. 再起動
make restart

# 4. ブラウザでアクセス
# http://localhost:3000
```

## セットアップ

### オプション1: Docker Compose (推奨)

最も簡単な起動方法です。

#### 前提条件
- Docker
- Docker Compose

#### 起動手順

**方法A: Makefileを使用（簡単）**

1. **Supabaseプロジェクトの作成**
   - [Supabase](https://supabase.com)でプロジェクトを作成
   - プロジェクトのURL、anon key、service keyを取得

2. **セットアップと起動**
   ```bash
   # 環境変数ファイルの作成と起動を一括で実行
   make dev

   # 各.envファイルを編集してSupabaseの認証情報を設定してから再起動
   # - .env
   # - backend/.env
   # - frontend/.env
   make restart
   ```

3. **その他の便利なコマンド**
   ```bash
   make help           # 利用可能なコマンド一覧を表示
   make logs           # ログを表示
   make logs-backend   # バックエンドのログのみ表示
   make logs-frontend  # フロントエンドのログのみ表示
   make restart        # 再起動
   make down           # 停止
   make clean          # 完全削除
   ```

**方法B: docker-composeコマンドを直接使用**

1. **Supabaseプロジェクトの作成**
   - [Supabase](https://supabase.com)でプロジェクトを作成
   - プロジェクトのURL、anon key、service keyを取得

2. **環境変数の設定**
   ```bash
   # ルートディレクトリに.envファイルを作成
   cp .env.example .env

   # バックエンド用
   cp backend/.env.example backend/.env

   # フロントエンド用
   cp frontend/.env.example frontend/.env

   # 各.envファイルを編集してSupabaseの認証情報を設定
   ```

3. **アプリケーションの起動**
   ```bash
   docker-compose up -d
   ```

4. **アクセス**
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000
   - APIドキュメント: http://localhost:8000/docs

5. **ログの確認**
   ```bash
   # 全サービスのログを表示
   docker-compose logs -f

   # バックエンドのログのみ
   docker-compose logs -f backend

   # フロントエンドのログのみ
   docker-compose logs -f frontend
   ```

6. **停止**
   ```bash
   docker-compose down
   ```

7. **完全削除（ボリュームも含む）**
   ```bash
   docker-compose down -v
   ```

### オプション2: ローカル環境での起動

Docker を使わずにローカル環境で起動する場合。

### 1. Supabaseプロジェクトの作成

1. [Supabase](https://supabase.com)でプロジェクトを作成
2. プロジェクトのURL、anon key、service keyを取得

### 2. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してSupabaseの認証情報を設定

# サーバーの起動
python run.py
```

バックエンドは http://localhost:8000 で起動します。

### 3. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してSupabaseの認証情報とAPIのURLを設定

# 開発サーバーの起動
npm run dev
```

フロントエンドは http://localhost:3000 で起動します。

## 環境変数

### バックエンド (.env)

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### フロントエンド (.env)

```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

## 使い方

### オプション1: CLIツール（コマンドライン）

Webアプリケーションを起動せずに、コマンドラインで直接変換できます。

**基本的な使い方:**

```bash
# Linux/Mac
./convert.sh input.gpx

# Windows
convert.bat input.gpx
```

**出力ファイル名を指定:**

```bash
./convert.sh input.gpx -o output.mp4
```

**カスタム設定:**

```bash
# HD解像度、60FPS
./convert.sh input.gpx -o output.mp4 --width 1280 --height 720 --fps 60

# 詳細な出力を表示
./convert.sh input.gpx -v
```

**ヘルプを表示:**

```bash
./convert.sh --help
```

詳しい使い方は [CLI_USAGE.md](CLI_USAGE.md) を参照してください。

### オプション2: Webアプリケーション

1. アプリケーションにアクセス
2. メールアドレスとパスワードでサインアップ/ログイン
3. GPX/TCX/FITファイルをアップロード
4. 動画が自動生成されます
5. 生成された動画を再生・ダウンロード

## API エンドポイント

### POST /api/upload
アクティビティファイルをアップロードして動画を生成

**リクエスト**: `multipart/form-data`
- `file`: GPX/TCX/FITファイル

**レスポンス**:
```json
{
  "video_id": "uuid",
  "status": "completed",
  "message": "Video generated successfully",
  "video_url": "/api/videos/{video_id}"
}
```

### GET /api/videos/{video_id}/status
動画生成のステータスを取得

### GET /api/videos/{video_id}
生成された動画をダウンロード

### GET /api/health
ヘルスチェック

## Docker コマンド早見表

```bash
# コンテナの起動（バックグラウンド）
docker-compose up -d

# コンテナの起動（ログ表示）
docker-compose up

# コンテナの停止
docker-compose stop

# コンテナの停止と削除
docker-compose down

# コンテナの再起動
docker-compose restart

# 特定のサービスのみ再起動
docker-compose restart backend

# イメージの再ビルド
docker-compose build

# イメージ再ビルド後に起動
docker-compose up -d --build

# コンテナの状態確認
docker-compose ps

# リソースの完全削除（コンテナ、ネットワーク、ボリューム）
docker-compose down -v --rmi all

# バックエンドコンテナに入る
docker-compose exec backend bash

# フロントエンドコンテナに入る
docker-compose exec frontend sh
```

## トラブルシューティング

### ポートが既に使用されている

```bash
# 使用中のポートを確認
sudo lsof -i :8000  # バックエンド
sudo lsof -i :3000  # フロントエンド

# docker-compose.ymlのポートを変更
# 例: "8001:8000" や "3001:3000"
```

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs backend
docker-compose logs frontend

# コンテナの状態を確認
docker-compose ps

# 完全にクリーンアップして再起動
docker-compose down -v
docker-compose up -d --build
```

### 環境変数が反映されない

```bash
# .envファイルが正しく設定されているか確認
cat .env
cat backend/.env
cat frontend/.env

# コンテナを再作成
docker-compose down
docker-compose up -d
```

### 動画生成でエラーが発生する

バックエンドコンテナにffmpegやフォントがインストールされているか確認:

```bash
docker-compose exec backend bash
ffmpeg -version
ls /usr/share/fonts/truetype/dejavu/
```

## プロジェクト構成

```
activetylog2mv/
├── docker-compose.yml          # Docker Compose設定
├── Makefile                    # Docker操作用Makefile
├── .env.example                # 環境変数のサンプル
├── convert.sh                  # CLIツール実行スクリプト（Linux/Mac）
├── convert.bat                 # CLIツール実行スクリプト（Windows）
├── CLI_USAGE.md                # CLIツール詳細ガイド
├── backend/
│   ├── Dockerfile              # バックエンド用Dockerfile
│   ├── .dockerignore
│   ├── cli.py                  # CLIツール本体
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # APIエンドポイント
│   │   ├── core/
│   │   │   ├── config.py          # 設定
│   │   │   └── supabase_client.py # Supabaseクライアント
│   │   ├── models/
│   │   │   └── schemas.py         # Pydanticモデル
│   │   ├── parsers/
│   │   │   ├── gpx_parser.py      # GPXパーサー
│   │   │   ├── tcx_parser.py      # TCXパーサー
│   │   │   └── fit_parser.py      # FITパーサー
│   │   ├── services/
│   │   │   └── video_generator.py # 動画生成サービス
│   │   └── main.py                # FastAPIアプリケーション
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── Dockerfile              # フロントエンド用Dockerfile
│   ├── .dockerignore
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth.jsx           # 認証コンポーネント
│   │   │   └── FileUpload.jsx     # ファイルアップロード
│   │   ├── lib/
│   │   │   ├── supabase.js        # Supabaseクライアント
│   │   │   └── api.js             # APIクライアント
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 開発

### バックエンドの開発

```bash
cd backend
source venv/bin/activate
python run.py
```

APIドキュメント: http://localhost:8000/docs

### フロントエンドの開発

```bash
cd frontend
npm run dev
```

## ライセンス

MIT