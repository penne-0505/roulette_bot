# テンプレート管理ガイド

このガイドでは、あみだくじテンプレートを活用する際の典型的な操作手順と、`FlowController` から `DBManager` へ処理がどのように流れるかを整理します。カスタムテンプレートを扱う開発者・モデレーター向けの実務フローをまとめています。

## 利用モードの切り替え

- 既存テンプレートを使う場合は `UseExistingHandler` が発火し、プライベートスコープのテンプレートのみを選択肢に提示します。【src/flow/handlers.py†L115-L135】
- 共有テンプレートはギルド内限定で `UseSharedTemplatesHandler` がビューを表示します。ギルド外で実行された場合はエラーメッセージ付きのエフェメラル応答を返します。【src/flow/handlers.py†L159-L187】
- 公開テンプレートは `UsePublicTemplatesHandler` が `DBManager` から取得した情報を埋め込んだビューを提示し、テンプレートコピーへの導線を提供します。【src/flow/handlers.py†L189-L237】

## カスタムテンプレートの登録

1. `MemberSelectView` などから `AmidakujiState` を遷移させ、入力モーダルでテンプレート名・選択肢を集めます。【src/views/view.py†L34-L160】
2. `DBManager.add_custom_template` は、ユーザーが存在することを検証しつつテンプレートをプライベートスコープで保存します。【src/db_manager.py†L646-L661】
3. テンプレート削除や上書きでは `delete_custom_template` がタイトル一致での除去を行い、再保存します。【src/db_manager.py†L664-L676】

## 共有テンプレートの運用

- サーバー全体で再利用するテンプレートは `create_shared_template` で公開・ギルドスコープに変換され、Firestore の共有コレクションに保存されます。【src/db_manager.py†L690-L700】
- 共有テンプレートを個人用にコピーする際はタイトルの重複回避ロジックを備えた `copy_shared_template_to_user` を経由します。【src/db_manager.py†L702-L723】
- 共有テンプレートの取得は `get_shared_templates_for_user` がギルド専用とパブリックの両方を返し、ビュー側で選択肢に整形されます。【src/db_manager.py†L379-L388】【src/flow/handlers.py†L172-L186】

## 抽選・履歴との連携

- 選択肢確定後は `data_process.create_pair_from_list` が選抜アルゴリズムを適用し、重み付き抽選もサポートします。【src/data_process.py†L32-L72】
- 結果表示は `create_embeds_from_pairs` がコンパクト／詳細モードの埋め込みを構築します。【src/data_process.py†L103-L117】
- 実行履歴は `DBManager.save_history` がギルド・テンプレート・抽選結果を Firestore に保存し、後続の参照に備えます。【src/db_manager.py†L448-L483】

## トラブルシューティング

- DB 接続が初期化されていない場合は `resolve_db_manager` が例外を投げるため、サービス初期化コードで `DBManager.with_app` を必ず呼び出してください。【src/flow/handlers.py†L46-L57】【src/db_manager.py†L179-L191】
- テンプレート構造が不正な場合は `_validate_template` が失敗して例外を発生させます。`choices` の配列が文字列であることなど基本要件を満たしているか確認しましょう。【src/db_manager.py†L238-L274】
