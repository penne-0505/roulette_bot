# モジュール別リファレンス概要

この文書は`src/`配下の主要モジュールの責務と連携関係をまとめたものです。変更後の構成を前提に、どこにどのロジックが存在するのかを素早く把握できるようにしています。

## エントリーポイント

### `src/main.py`
- `main()` で `asyncio.run()` を呼び出し、Bot 用クライアントの生成とスラッシュコマンド登録をまとめて実行します。`src/main.py:13` `src/main.py:20` `src/main.py:21`
- 起動前にトークンを読み込み、取りこぼしがあればエラーログを出して終了するシンプルなフローに整理されています。`src/main.py:14-18`

## Bot レイヤー

### `src/bot/client.py`
- Discord クライアントの具象クラス `BotClient` を定義し、翻訳機能のセットアップや `StartupSelfCheck` を起動時に実行します。`src/bot/client.py:26-80`
- Firestore 初期化後に既定テンプレートを整備し、セルフチェックの失敗を検知したら安全にシャットダウンします。`src/bot/client.py:46-53`

### `src/bot/commands.py`
- `register_commands()` で全てのスラッシュコマンドを `CommandTree` に登録し、DB 依存性の取得処理を `require_db_manager()` に集約しています。`src/bot/commands.py:24-34`
- `/ping` やあみだくじ系のコマンドをモジュール内にまとめ、レスポンス組み立て・フロー連携を明示しました。`src/bot/commands.py:35-200`

### `src/bot/config.py`
- `.env` または環境変数から Discord Bot トークンを読み込み、フォーマット検査とサマリーログ出力を行います。`src/bot/config.py:14-51`

## フロー制御層

### `src/data_interface.py`
- 状態遷移の中心である `FlowController` を定義し、`AmidakujiState` に応じてハンドラーをディスパッチします。`src/data_interface.py:12-74`
- ハンドラーが返すアクションを逐次実行し、コンテキスト状態が変化しなくなるまでループを継続します。`src/data_interface.py:76-121`

## モデル層

### `src/models/context_model.py`
- コマンド処理全体で共有する `CommandContext` を定義し、状態・結果・一時データを一元管理します。`src/models/context_model.py:7-79`

### `src/models/model.py`
- テンプレート・ユーザー情報・抽選履歴など Firestore と連携するデータモデル、および `SelectionMode` 等の列挙体を提供します。`src/models/model.py:12-107`

### `src/models/state_model.py`
- あみだくじ機能で利用する状態列挙 `AmidakujiState` と補助的な判定ロジックを定義します。`src/models/state_model.py:8-160`

## ビュー / UI コンポーネント層

### `src/views/view.py`
- コマンド起動時に提示する `ModeSelectionView` などのビューを定義し、ユーザー操作に応じて `FlowController` を呼び出します。`src/views/view.py:7-160`

### `src/components/`
- `button.py`、`select.py`、`modal.py` に UI コンポーネントを分割し、バリデーションや入力保持をカプセル化しています。`src/components/button.py:5-200` `src/components/select.py:5-180` `src/components/modal.py:5-140`

## サービス層

### `src/services/app_context.py`
- Firebase 認証情報のロードと `DBManager` の初期化を担うユーティリティ関数を提供します。`src/services/app_context.py:9-31`

### `src/services/startup_check.py`
- 起動時セルフチェック `StartupSelfCheck` を実装し、Discord 認証・Firestore 接続・必須コレクションの整備状況を検証します。`src/services/startup_check.py:35-181`

## データアクセス層

### `src/db_manager.py`
- Firestore アプリ・リポジトリのシングルトン管理、テンプレートや履歴に関する高水準 API をまとめています。`src/db_manager.py:46-517`

### `src/db/repositories.py`
- Firestore の各コレクション (`users` / `info` / `shared_templates` / `history`) を操作するリポジトリを提供します。`src/db/repositories.py:17-139`

### `src/db/serializers.py`
- Firestore ドキュメントとドメインモデル間の変換処理やテンプレート正規化を担います。`src/db/serializers.py:17-134`

### `src/db/constants.py`
- Firestore コレクションで共有する定数（必須コレクション一覧やセンチネル ID）を集約します。`src/db/constants.py:3-11`

## データ処理ユーティリティ

### `src/data_process.py`
- ペアリングアルゴリズムや抽選結果の埋め込み生成ロジックを実装します。`src/data_process.py:7-152`

## 共通ユーティリティ

### `src/utils.py`
- シングルトンメタクラス、コマンド翻訳、ロギングスタイル関数などプロジェクト共通のヘルパーを集約します。`src/utils.py:5-79`

---
詳細な運用手順は `docs/guides/`、開発方針や規約は `docs/standards/` を参照してください。
