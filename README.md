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

## セットアップ

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

## プロジェクト構成

```
activetylog2mv/
├── backend/
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