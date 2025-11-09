# テンプレート管理ガイド

このガイドでは、あみだくじテンプレートを活用する際の典型的な操作手順と、`FlowController` から `TemplateApplicationService` / `FirestoreTemplateRepository` へ処理がどのように流れるかを整理します。カスタムテンプレートを扱う開発者・モデレーター向けの実務フローをまとめています。

## 利用モードの切り替え

- 既存テンプレートを使う場合は `UseExistingHandler` が発火し、プライベートスコープのテンプレートのみを選択肢に提示します。【src/flow/handlers.py†L115-L135】
- 共有テンプレートはギルド内限定で `UseSharedTemplatesHandler` がビューを表示します。ギルド外で実行された場合はエラーメッセージ付きのエフェメラル応答を返します。【src/flow/handlers.py†L159-L187】
- 公開テンプレートは `UsePublicTemplatesHandler` が TemplateService 経由で取得した情報を埋め込んだビューを提示し、テンプレートコピーへの導線を提供します。【src/flow/handlers.py†L189-L237】

## カスタムテンプレートの登録

1. `MemberSelectView` などから `AmidakujiState` を遷移させ、入力モーダルでテンプレート名・選択肢を集めます。【src/presentation/discord/views/view.py†L35-L160】
2. `FirestoreTemplateRepository.add_custom_template` は、ユーザー存在を検証しつつテンプレートをプライベートスコープで保存します。【src/infrastructure/firestore/template_repository.py†L467-L490】
3. テンプレート削除や上書きでは `delete_custom_template` がタイトル一致で除去し、再保存します。【src/infrastructure/firestore/template_repository.py†L499-L523】

## 共有テンプレートの運用

- サーバー全体で再利用するテンプレートは `create_shared_template` で公開・ギルドスコープに変換され、Firestore の共有コレクションに保存されます。【src/infrastructure/firestore/template_repository.py†L531-L542】
- 共有テンプレートを個人用にコピーする際はタイトルの重複回避ロジックを備えた `copy_shared_template_to_user` を経由します。【src/infrastructure/firestore/template_repository.py†L543-L565】
- 共有テンプレートの取得は `get_shared_templates_for_user` がギルド専用とパブリックの両方を返し、ビュー側で選択肢に整形されます。【src/infrastructure/firestore/template_repository.py†L266-L308】【src/flow/handlers.py†L172-L186】

## 抽選・履歴との連携

- 選択肢確定後は `data_process.create_pair_from_list` が選抜アルゴリズムを適用し、重み付き抽選もサポートします。【src/data_process.py†L32-L72】
- 結果表示は `create_embeds_from_pairs` がコンパクト／詳細モードの埋め込みを構築します。【src/data_process.py†L103-L117】
- 実行履歴は `FirestoreTemplateRepository.save_history` がギルド・テンプレート・抽選結果を Firestore に保存し、後続の参照に備えます。【src/infrastructure/firestore/template_repository.py†L310-L364】

## トラブルシューティング

- Firestore クライアントが初期化されていない場合は `FirestoreUnitOfWork.ensure_configured()` が例外を投げるため、起動時に `create_template_repository()` で資格情報を解決しておく必要があります。【src/services/app_context.py†L1-L36】【src/infrastructure/firestore/unit_of_work.py†L78-L118】
- テンプレート構造が不正な場合は `deserialize_template` が例外を発生させるため、`choices` が文字列リストであることなど基本要件を満たしているか確認しましょう。【src/db/serializers.py†L45-L110】
