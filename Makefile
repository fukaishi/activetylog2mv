.PHONY: help up down restart logs build clean ps

help: ## ヘルプを表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## アプリケーションを起動（バックグラウンド）
	docker-compose up -d

down: ## アプリケーションを停止
	docker-compose down

restart: ## アプリケーションを再起動
	docker-compose restart

logs: ## 全サービスのログを表示
	docker-compose logs -f

logs-backend: ## バックエンドのログを表示
	docker-compose logs -f backend

logs-frontend: ## フロントエンドのログを表示
	docker-compose logs -f frontend

build: ## イメージを再ビルド
	docker-compose build

rebuild: ## イメージを再ビルドして起動
	docker-compose up -d --build

ps: ## コンテナの状態を確認
	docker-compose ps

clean: ## 全てのコンテナとボリュームを削除
	docker-compose down -v

clean-all: ## 全てのリソースを削除（イメージも含む）
	docker-compose down -v --rmi all

shell-backend: ## バックエンドコンテナに入る
	docker-compose exec backend bash

shell-frontend: ## フロントエンドコンテナに入る
	docker-compose exec frontend sh

setup: ## 初回セットアップ（.envファイルの作成）
	@echo "環境変数ファイルを作成しています..."
	@if [ ! -f .env ]; then cp .env.example .env; echo ".env を作成しました"; fi
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "backend/.env を作成しました"; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; echo "frontend/.env を作成しました"; fi
	@echo "セットアップ完了！各.envファイルにSupabaseの認証情報を設定してください。"

dev: setup up ## 開発環境のセットアップと起動
	@echo "アプリケーションを起動しました"
	@echo "フロントエンド: http://localhost:3000"
	@echo "バックエンドAPI: http://localhost:8000"
	@echo "APIドキュメント: http://localhost:8000/docs"
