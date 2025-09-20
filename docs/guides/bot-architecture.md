# Bot レイヤー再構成ガイド

このガイドでは、Bot 起動ロジックをモジュール化したリファクタリングの意図と各コンポーネントの役割をまとめます。`src/main.py` に集中していた処理を `bot/` パッケージへ再配置したことで、起動フローの見通しとテスト可能性が向上しました。

## 全体像

```
src/
├── main.py           # エントリーポイント (asyncio.run)
└── bot/
    ├── client.py     # Discord クライアント具象クラス
    ├── commands.py   # スラッシュコマンド登録処理
    └── config.py     # 環境変数からの設定読み込み
```

### 主な改善点
- **責務分離**: クライアント実装とコマンド宣言を分離し、メインスクリプトは「生成→登録→起動」に集中しました。
- **依存関係の明示化**: `commands.py` に `require_db_manager()` を設け、インタラクションから DB 管理クラスを取得する流れを一元化しています。`src/bot/commands.py:29-33`
- **セルフチェックの強化**: `BotClient` が `StartupSelfCheck` を直接保持し、コレクション整備も含めた検証を実施します。`src/bot/client.py:46-53`

## 起動フロー

1. `main.py` が `load_client_token()` を呼び出し、トークン未設定時は即座に終了します。`src/main.py:14-18`
2. `BotClient` を生成して `register_commands()` を適用し、イベントループに参加させます。`src/main.py:20-26`
3. `BotClient.setup_hook()` で翻訳機構を登録・同期、`on_ready()` でテンプレート初期化とセルフチェックを実行します。`src/bot/client.py:41-60`

## Firestore との連携

- `services/app_context.create_db_manager()` が Firebase 資格情報を読み込み、`DBManager` を初期化します。`src/services/app_context.py:17-31`
- `DBManager` は `db/` パッケージのリポジトリ・シリアライザを利用して Firestore ドキュメントとの変換と保存を行います。`src/db_manager.py:46-517`
- 起動時セルフチェックではサンプルドキュメントをスキップしつつ必須コレクションを検証します。`src/services/startup_check.py:136-180`

## テスト観点

- 既存のユニットテストは `poetry run pytest` で全て成功することを確認済みです。
- 新しい構造でも `DBManager` のモック差し替えが可能なため、コマンド関連のテストは `SimpleNamespace(db=...)` を介して従来通り実装できます。

## 次のステップ

- `bot/commands.py` に新しい Slash コマンドを追加する際は、この構造に倣ってヘルパーや翻訳設定を再利用してください。
- Web UI / API など他インターフェースと連携する場合は、Bot レイヤーでの責務が肥大化しないよう別パッケージ化を検討してください。
