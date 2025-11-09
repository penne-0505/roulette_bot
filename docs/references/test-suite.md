# テストスイートリファレンス

このリファレンスは `tests/` 配下のユニットテストが担う責務と、想定しているシナリオを一覧化したものです。機能追加時にどのテストを更新・追加すべきか判断するための手がかりとして利用してください。

## コンテキストと状態管理

- `test_command_context.py` は `CommandContext` の履歴更新、結果型バリデーション、スナップショット管理を検証し、状態遷移時のデータ整合性を保証します。【tests/test_command_context.py†L17-L70】
- `test_flow_controller.py` は `FlowController` のディスパッチ処理、アクションシーケンス実行、未知状態の例外処理を網羅します。【tests/test_flow_controller.py†L38-L141】

## アクション実行と UI 操作

- `test_flow_actions.py` はメッセージ送信・ビュー表示・モーダル表示・応答ディファーなど各 `FlowAction` の分岐を網羅し、初回応答とフォローアップの切り替えを検証します。【tests/test_flow_actions.py†L49-L184】
- `test_member_select.py` は UI コンポーネントで利用する `remove_bots` ヘルパーが bot アカウントを除外することを確認します。【tests/test_member_select.py†L1-L13】

## テンプレートおよび履歴機能

- `test_flow_handlers.py` はテンプレート選択ビュー、オプション編集、共有テンプレートコピーなどハンドラーごとの返却アクションを検証し、UI と状態の整合性を担保します。【tests/test_flow_handlers.py†L62-L200】
- `test_firestore_template_repository.py` は Firestore リポジトリとの連携をモックし、初期化時のドキュメント生成、テンプレート・履歴の読み書きを確認します。【tests/test_firestore_template_repository.py†L1-L220】

## 抽選ロジック

- `test_data_process.py` は重み付きペアリングと埋め込み生成を検証し、アバター URL の選択やバイアス低減モードの挙動を保証します。【tests/test_data_process.py†L29-L95】

---
テストを拡張する際は上記の責務を参考に、影響範囲に応じて既存ケースの修正と新規ケースの追加を行ってください。
