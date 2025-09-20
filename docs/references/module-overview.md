# モジュール別リファレンス概要

この文書は`src/`配下の主要なモジュールごとの責務と関連機能を整理したリファレンスです。実装ファイルを横断して、どこにどのロジックが存在するのかを素早く把握できることを目的としています。

## エントリーポイント

### `main.py`
- Discord クライアントのサブクラス `Client` を定義し、起動時のセルフチェックやコマンド同期を実施します。【src/main.py†L34-L117】
- `/ping` などのアプリケーションコマンドを宣言し、レスポンス計測や埋め込みの構築を担当します。【src/main.py†L119-L208】

## フロー制御層

### `data_interface.py`
- 状態機械の中心にあたる `FlowController` が定義されており、`AmidakujiState` ごとに適切なハンドラーをディスパッチします。【src/data_interface.py†L1-L86】
- ハンドラーが返す `FlowAction` を逐次実行し、インタラクションの応答送信やビュー表示を統一的に扱います。【src/data_interface.py†L88-L121】

### `flow/actions.py`
- Discord 応答（メッセージ送信、モーダル表示、ビュー表示など）をオブジェクトとして表現する `FlowAction` 実装群を提供します。【src/flow/actions.py†L1-L118】
- それぞれのアクションは `CommandContext` を受け取り、フォローアップ送信やディファー判定などの共通処理を内包します。【src/flow/actions.py†L20-L117】

### `flow/handlers.py`
- 各状態で実行されるハンドラー群がまとまっており、選択肢追加やテンプレート管理などユーザー操作に応じた遷移ロジックをカプセル化します。【src/flow/handlers.py†L1-L400】
- ハンドラーは `CommandContext` を介して履歴や入力内容を更新し、必要な `FlowAction` を返却します。【src/flow/handlers.py†L30-L120】

## モデル層

### `models/context_model.py`
- コマンド処理全体で共有する `CommandContext` を定義し、状態遷移に付随する結果や履歴を保持します。【src/models/context_model.py†L1-L79】
- 選択肢スナップショットの管理や型検証を行い、ハンドラー間で一貫したデータアクセスを提供します。【src/models/context_model.py†L53-L79】

### `models/model.py`
- テンプレートやユーザー情報、割り当て履歴など Firestore とやり取りするデータモデルを列挙・定義します。【src/models/model.py†L1-L120】
- 抽選結果表示形式を切り替える `ResultEmbedMode`、選抜アルゴリズムを示す `SelectionMode` などの列挙体を提供します。【src/models/model.py†L64-L88】

### `models/state_model.py`
- あみだくじ機能で利用する状態列挙 `AmidakujiState` と補助的な状態判定ロジックを定義します。【src/models/state_model.py†L1-L180】
- ビューやモーダルで発火するイベントごとに状態を網羅的に整理し、フロー制御の基礎を提供します。【src/models/state_model.py†L10-L120】

## ビュー・UI コンポーネント層

### `views/view.py`
- コマンド起動時にユーザーへ提示する `ModeSelectionView` などの UI 集約を行います。【src/views/view.py†L1-L160】
- 各ボタン・セレクトのコールバックで `FlowController` を呼び出し、状態遷移のトリガーを発生させます。【src/views/view.py†L60-L140】

### `components/`
- `button.py`、`select.py`、`modal.py` で Discord UI コンポーネントを実装し、ビューから再利用できる形で提供します。【src/components/button.py†L1-L200】【src/components/select.py†L1-L180】【src/components/modal.py†L1-L140】
- バリデーションや入力値保持などのコンポーネント固有ロジックをカプセル化します。【src/components/modal.py†L40-L110】

## サービス層

### `services/app_context.py`
- Firebase 認証情報の読み込みと `DBManager` の初期化を行うファクトリー関数を提供します。【src/services/app_context.py†L1-L34】
- `.env` からの読み込みやリモート JSON のフェッチなど、デプロイ環境差分を吸収します。【src/services/app_context.py†L12-L27】

### `services/startup_check.py`
- 起動時セルフチェック `StartupSelfCheck` を提供し、Discord 認証・Firestore 接続・必須コレクションの存在を確認します。【src/services/startup_check.py†L1-L114】
- 実行結果は `CheckResult` として集約され、ログ出力ポリシーが統一されています。【src/services/startup_check.py†L14-L76】

## データアクセス層

### `db_manager.py`
- Firestore クライアントのシングルトン管理や、ユーザー・テンプレート・履歴用リポジトリの生成を担当します。【src/db_manager.py†L1-L154】
- Firestore のクエリヘルパーや初期化ルーチンを提供し、上位層からは `DBManager` 経由でデータ操作を行います。【src/db_manager.py†L156-L260】

## データ処理ユーティリティ

### `data_process.py`
- ペアリングアルゴリズムや抽選結果の埋め込み生成関数を実装します。【src/data_process.py†L1-L94】【src/data_process.py†L96-L152】
- 重み付き選択やモード正規化など、抽選ロジックの切り替えを担います。【src/data_process.py†L17-L90】

## 共通ユーティリティ

### `utils.py`
- シングルトンメタクラス、Discord コマンド翻訳、ロギング用スタイル関数などを提供します。【src/utils.py†L1-L79】
- CLI や他モジュールから色付き文字列を生成できるヘルパーがまとまっています。【src/utils.py†L41-L78】

---
このリファレンスは、実装ファイルを横断的に把握する入口として活用してください。詳細な利用手順については `docs/guides/` を、運用ルールについては `docs/standards/` を参照してください。
