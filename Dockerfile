# ベースイメージを指定
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# Poetryのインストール
RUN pip install --no-cache-dir poetry

# 依存関係ファイルをコピー
COPY pyproject.toml poetry.lock ./

# 依存関係をインストール (開発用依存関係は除外)
# --no-root オプションは維持
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-interaction --no-ansi --no-root

# ソースコードをコピー
COPY src/ ./src/

# 環境変数PORTを設定 (Cloud Runが設定するが、ローカルテスト用にデフォルトを設定)
ENV PORT=8080

# アプリケーションの実行コマンド
# main.py が Bot と FastAPI サーバーを起動する
CMD ["python", "src/main.py"]
