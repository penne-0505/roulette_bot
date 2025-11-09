# モジュール別リファレンス概要

この文書は`src/`配下の主要モジュールの責務と連携関係をまとめたものです。変更後の構成を前提に、どこにどのロジックが存在するのかを素早く把握できるようにしています。

## エントリーポイント

### `src/main.py`
- `main()` で `asyncio.run()` を呼び出し、Bot 用クライアントの生成とスラッシュコマンド登録をまとめて実行します。`src/main.py:13` `src/main.py:20` `src/main.py:21`
- 起動前にトークンを読み込み、取りこぼしがあればエラーログを出して終了するシンプルなフローに整理されています。`src/main.py:14-18`

## Bot レイヤー

### `src/presentation/discord/client.py`
- Discord クライアントの具象クラス `BotClient` を定義し、翻訳設定やスラッシュコマンド同期、`StartupSelfCheck` の実行までを担います。`src/presentation/discord/client.py:25-95`
- Firestore テンプレートリポジトリを受け取り、既定テンプレート整備やユーザー初期化を起動時/コマンド完了時に処理します。`src/presentation/discord/client.py:42-95`

### `src/presentation/discord/commands/registry.py`
- `register_commands()` で `/ping` や あみだくじ関連コマンドを `CommandTree` に登録し、`CommandRuntimeServices` を介してユースケースやリポジトリを解決します。`src/presentation/discord/commands/registry.py:1-383`
- 各コマンドはビューやフローを生成して `interaction.followup.send` へ統一し、エフェメラル応答やエラーハンドリングの方針を揃えています。`src/presentation/discord/commands/registry.py:64-383`

### `src/app/config.py`
- `.env` または環境変数から Discord トークンや Firebase 認証参照を読み込み、バリデーション・整形・サマリーログ出力を行います。`src/app/config.py:14-101`
- `AppConfig` を通じて設定値を型安全に参照できるようにし、DI モジュールで共有します。`src/app/config.py:34-101`

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

### `src/presentation/discord/views/view.py`
- コマンド起動時に提示する `ModeSelectionView` などのビューを定義し、ユーザー操作に応じて `FlowController` を呼び出します。`src/presentation/discord/views/view.py:35-160`

### `src/components/`
- `button.py`、`select.py`、`modal.py` に UI コンポーネントを分割し、バリデーションや入力保持をカプセル化しています。`src/components/button.py:5-200` `src/components/select.py:5-180` `src/components/modal.py:5-140`

## サービス層

### `src/services/app_context.py`
- Firebase 認証情報のロードと `FirestoreTemplateRepository` の初期化を担うユーティリティ関数を提供します。`src/services/app_context.py:1-46`

### `src/services/startup_check.py`
- 起動時セルフチェック `StartupSelfCheck` を実装し、Discord 認証・Firestore 接続・必須コレクションの整備状況を検証します。`src/services/startup_check.py:35-181`

## データアクセス層

### `src/infrastructure/firestore/template_repository.py`
- Firestore クライアントと各種リポジトリを束ね、テンプレート/履歴/ユーザー/設定の高水準 API を提供します。`src/infrastructure/firestore/template_repository.py:1-580`
- 既定テンプレートの注入、埋め込み・抽選モードの永続化、共有テンプレート検索、履歴保存など永続化ロジックを集約しています。`src/infrastructure/firestore/template_repository.py:209-580`

### `src/infrastructure/firestore/repositories.py`
- Firestore の各コレクション (`users` / `info` / `shared_templates` / `history`) を操作するリポジトリクラスを提供します。`src/infrastructure/firestore/repositories.py:8-182`
- センチネルドキュメントのスキップやページングをハンドルし、TemplateRepository からの呼び出しを単純化します。`src/infrastructure/firestore/repositories.py:96-168`

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
