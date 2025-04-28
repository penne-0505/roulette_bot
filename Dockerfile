# ベースイメージを指定
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# Poetryのインストール
# --no-cache-dir オプションを追加してキャッシュを使用しないようにする
# poetryのバージョンを固定することも検討
RUN pip install --no-cache-dir poetry

# 依存関係ファイルをコピー
COPY pyproject.toml poetry.lock ./

# 依存関係をインストール (--no-devで開発用依存関係を除外)
# poetry config virtualenvs.create false でプロジェクト内に仮想環境を作成しないように設定
# --no-interaction --no-ansi オプションを追加して非対話的に実行
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# ソースコードをコピー
# cred/ ディレクトリのコピーは削除
COPY src/ ./src/

# アプリケーションの実行コマンド
# poetry run を使用してpoetryが管理する環境で実行
CMD ["poetry", "run", "python", "src/main.py"]
