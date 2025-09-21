# Bot レイヤー再構成ガイド

このガイドでは、新しい起動フローと主要モジュールの責務分担をまとめます。2024 年のリファクタリングでアプリケーション層 (`src/app/`) を新設し、設定読み込み・依存解決・起動制御を一元化しました。

## ディレクトリ構成

```
src/
├── app/
│   ├── __init__.py          # 公開 API (load_config, build_discord_application など)
│   ├── config.py            # 環境変数から AppConfig を構築
│   ├── container.py         # BotClient と依存性を束ねるコンテナ
│   └── logging.py           # ロギング初期化ヘルパー
├── bot/
│   ├── client.py            # Discord クライアント具象クラス（DBManager を明示注入）
│   ├── commands.py          # スラッシュコマンド登録処理
│   └── config.py            # 互換用のトークン取得ヘルパー（app.config に委譲）
├── services/app_context.py  # Firebase 資格情報の解決と DBManager 初期化
├── db_manager.py            # Firestore 高水準アクセス（シングルトンを明示管理）
└── main.py                  # エントリーポイント
```

## 起動フロー

1. `main.py` が `configure_logging()` を呼び出してログ設定を初期化します。
2. `load_config()` が `.env`（存在すれば）を読み込み、`CLIENT_TOKEN` / `FIREBASE_CREDENTIALS` を検証します。
3. `build_discord_application()` が `AppConfig` を受け取り、
   - `services.app_context.create_db_manager()` で Firestore を初期化
   - `BotClient(db_manager=...)` を生成
   - `register_commands()` を適用
   - `DiscordApplication`（クライアントとトークンを保持する軽量コンテナ）を返します。
4. `DiscordApplication.run()` が `async with client: client.start(token)` を実行し、イベントループへ参加します。

## DBManager の管理

- `DBManager.get_instance()` は明示的なクラス変数 `_global_instance` を利用しており、`set_global_instance(None)` でテストから安全にリセットできます。
- `with_app(app)` / `with_client(client)` は共通の `_attach_client()` を経由し、リポジトリ生成と `ensure_required_collections()` を一度だけ実行します。
- Firestore 資格情報は `resolve_firebase_credentials()` で **パス or URL** のいずれにも対応。`create_db_manager(reference)` で再利用できます。

## ハンドラとフロー制御

- `flow/handlers/` はサブモジュール化され、責務ごとに分割されました。
  - `base.py`: 共通ヘルパー・`BaseStateHandler`
  - `templates.py`: テンプレート選択/作成系
  - `options.py`: 選択肢編集 UI
  - `members.py`: メンバー抽選ロジック
  - `lifecycle.py`: キャンセルなどの終端処理
- `FlowController` は従来通り `state -> handler` のマッピングを保持しますが、各ハンドラのインポート先が `flow.handlers` パッケージ経由に変更されています。

## テスト観点

- すべてのユニットテストは `poetry run pytest` で成功（リファクタリング直後に確認済み）。
- Firestore 周りのテストは `reset_manager()`（`DBManager.set_global_instance(None)` をラップ）を使うことで副作用を隔離しています。
- 新しい `app` レイヤーは純粋関数で構成されているため、設定値のダミー化や `SimpleNamespace(db=...)` の差し替えが容易です。

## 移行メモ

- 旧来の `load_client_token()` を利用しているコードはそのまま動作しますが、新規コードでは `app.load_config()` の利用を推奨します。
- Firestore 以外のデータソースを追加する場合は、`app.container.build_discord_application()` に新しい依存解決を組み込むことで拡張できます。

## 次のステップ

- Slash コマンドの追加・変更時は `flow/handlers` の分割構造を踏襲し、責務ごとにモジュールを追加してください。
- Web UI / API など別インターフェースとの共有を想定する場合は、`DiscordApplication` に類似したコンテナを新設し、共通のサービス層を再利用する方針が楽です。
