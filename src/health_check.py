import os

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health_check():
    """
    Cloud Runのヘルスチェック用エンドポイント。
    ステータスコード200で "OK" を返す。
    """
    return {"status": "OK"}


async def run_server():
    """
    FastAPIサーバーをuvicornで実行する。
    ポートは環境変数 PORT またはデフォルトの 8080 を使用する。
    """
    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
