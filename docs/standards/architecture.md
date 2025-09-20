# アーキテクチャ標準

この文書は Roulette Bot の実装における基本方針とコーディング標準をまとめたものです。新規機能を追加する際は、ここで示す原則に従ってください。

## レイヤー構造の維持

- **プレゼンテーション層**: `views/` と `components/` は Discord UI との接点です。イベントハンドラーではロジックを極力書かず、`FlowController` に処理を委譲します。【src/views/view.py†L60-L140】
- **フロー制御層**: `flow/` と `data_interface.py` は状態遷移を集約します。状態追加時は必ず列挙体・ハンドラー・ビューのいずれも更新してください。【src/data_interface.py†L31-L121】【src/models/state_model.py†L1-L120】
- **サービス層**: `services/` と `db_manager.py` は外部サービスとの接続を抽象化します。外部 API との通信処理はここにまとめ、UI 側で直接扱わないようにします。【src/services/app_context.py†L12-L34】【src/db_manager.py†L1-L154】

## 状態駆動設計

- すべてのユーザー操作は `AmidakujiState` を経由して処理します。状態を直接指定せず、既存のハンドラーを再利用することで副作用を可視化します。【src/models/state_model.py†L1-L120】
- `CommandContext` の `history` によって処理履歴が自動記録されるため、手動で辞書を書き換えないよう注意してください。【src/models/context_model.py†L24-L52】

## データアクセスの原則

- Firestore へのアクセスは `DBManager` 経由で行い、個別のコレクション操作を直接呼び出さないこと。新しいコレクションが必要な場合はリポジトリクラスを追加します。【src/db_manager.py†L26-L154】
- 認証情報の扱いは `load_firebase_credentials` を通じて統一し、環境変数やリモート JSON の差異を吸収します。【src/services/app_context.py†L12-L27】

## ロギングと翻訳

- ログは `utils.py` の定数・装飾関数を利用して色分けを行い、運用時の視認性を確保してください。【src/utils.py†L24-L78】
- コマンド名称のローカライズは `CommandsTranslator` に追加し、ハードコードされた文字列を散在させないようにします。【src/utils.py†L12-L38】

## テストとセルフチェック

- 起動時セルフチェックを破壊する変更（コレクション名の変更など）を行う場合は、`StartupSelfCheck.REQUIRED_COLLECTIONS` を更新し、ログ文を合わせて調整します。【src/services/startup_check.py†L24-L76】
- ペアリングアルゴリズムを変更する場合は、`data_process.py` の重み正規化ロジックに対してユニットテストを整備してください。【src/data_process.py†L17-L90】

## コーディングスタイル

- タイプヒントは可能な限り記述し、Discord API の戻り値は `discord` モジュールの型を用います。
- 例外メッセージはユーザー向けと開発者向けを切り分け、ユーザー向けエラーには日本語メッセージを付与します。

---
この標準は継続的に更新される可能性があります。プロジェクトに変更を加える前に最新の内容を確認してください。
