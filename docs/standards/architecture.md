# Roulette Bot アーキテクチャ標準

## 目的と適用範囲

本書は、コードベース内で暗黙に共有されているアーキテクチャや設計方針を明文化し、`docs/references/module-overview.md` など既存リファレンスとともに開発判断の拠り所とすることを目的とします。【docs/references/module-overview.md†L1-L80】  
記述対象は Discord Bot 全体のレイヤー構造、依存関係、状態管理、永続化、および運用ポリシーです。

## レイヤー構造と依存関係

- **Presentation (Discord)**: `presentation/discord` パッケージが Discord クライアント、スラッシュコマンド、ビューを集約し、Bot から見た UI 層として機能します。`BotClient` は翻訳設定・セルフチェック・ユーザー初期化までを担い、`register_commands()` が各スラッシュコマンドでユースケースとフローを束ねます。【src/presentation/discord/client.py†L25-L95】【src/presentation/discord/commands/registry.py†L42-L200】
- **Application / Usecase**: `application.services` でテンプレート操作・履歴・フロー遷移のユースケースをカプセル化し、`DiscordCommandUseCases` を介してプレゼンテーション層へ注入します。これらはドメインの `TemplateRepository` プロトコルのみに依存し、データストア固有の実装を持ちません。【src/presentation/discord/services.py†L16-L64】【src/application/services/template_service.py†L19-L164】【src/application/services/history_service.py†L9-L67】【src/application/services/flow_service.py†L19-L94】
- **Domain**: エンティティや値オブジェクト (`Template`, `AssignmentHistory`, `ResultEmbedMode` など) と、永続化境界である `TemplateRepository` プロトコルを `src/domain` に集約しています。アプリケーション層はこの契約を通じてのみデータを扱います。【src/domain/entities/template.py†L1-L33】【src/domain/entities/history.py†L1-L36】【src/domain/value_objects.py†L1-L15】【src/domain/interfaces/repositories.py†L18-L125】
- **Infrastructure**: Firestore へのアクセスは `FirestoreTemplateRepository` と `FirestoreUnitOfWork` が担い、必須コレクションの整備、既定テンプレートの注入、埋め込み/抽選モード設定の保持を担当します。`DBManager` は従来 API を保ったままこれらをラップし、`services.app_context` からシングルトンとして取得されます。【src/infrastructure/firestore/template_repository.py†L150-L450】【src/infrastructure/firestore/unit_of_work.py†L24-L122】【src/db_manager.py†L17-L44】【src/services/app_context.py†L13-L27】

依存関係の流れは Presentation → Application → Domain → Infrastructure の一方向であり、下位レイヤーの詳細に触れる場合はプロトコルやサービスラッパーを介することを原則とします。

## 起動と依存性解決

1. `bootstrap_application()` がロギングを初期化し、`.env` から読み込んだ `AppConfig` を Injector にバインドした `ApplicationModule` を構成します。TemplateRepository の具象実装はファクトリ引数で差し替え可能です。【src/bootstrap/app.py†L19-L88】
2. `build_discord_application()` は Injector から `BotClient` と `AppConfig` を取得し、コマンド登録後にトークンとクライアントをまとめた `DiscordApplication` を返します。【src/app/container.py†L12-L30】
3. `AppConfig` は Discord トークンと Firebase 認証情報を厳密に検証し、不要な空白やフォーマット逸脱時は警告・例外を出します。【src/app/config.py†L14-L101】
4. `create_db_manager()` は環境変数/URL/ローカルファイルから Firebase 認証情報を解決し、グローバル `DBManager` を初期化します。URL 参照時はキャッシュを用いて I/O を抑制します。【src/services/app_context.py†L13-L27】【src/infrastructure/config/firebase_credentials.py†L1-L109】
5. `BotClient` は起動時にデフォルトテンプレートを確保し、`StartupSelfCheck` で Discord 認証・Firestore 接続・必須コレクションを検証してから運用開始します。【src/presentation/discord/client.py†L48-L68】【src/services/startup_check.py†L35-L182】

## Discord プレゼンテーションの方針

- Slash コマンドでは `CommandRuntimeServices.from_client()` で Repository/Usecase を束ね、`CommandContext` と `FlowController` に共有します。これによりビューやハンドラは実行時依存を明示的に受け取り、テストで差し替えやすくなります。【src/presentation/discord/commands/registry.py†L42-L200】【src/presentation/discord/services.py†L40-L64】
- `presentation/discord/views` 配下では `discord.ui.View` の派生クラスを 300 秒タイムアウトで定義し、`CommandContext` のスナップショットを使ってボタン/セレクトの状態を同期します。選択肢が不足する場合はボタンを自動的に無効化するなど、UI 一貫性のルールをコード化しています。【src/presentation/discord/views/view.py†L35-L125】
- ビュー向けの状態は dataclass で表現し、DTO からの変換ヘルパーを提供することで、UI ロジックからドメインモデルの直接操作を避けています。【src/presentation/discord/views/state.py†L1-L66】

## フロー制御と状態管理

- `FlowController` は現在の `AmidakujiState` ごとにハンドラを解決し、アクションを実行した結果で状態が変わらなくなるまでループします。再入可能な `dispatch()` を通じて View/コマンドから任意のステートにジャンプできる設計です。【src/data_interface.py†L20-L85】
- デフォルトのハンドラは `FlowHandlerRegistry` にマッピングされており、テストやカスタマイズ時は `register()` で特定ステートのみ差し替え可能です。ハンドラは遅延生成・キャッシュされるため、生成コストを抑えつつ DI に依存しない拡張ポイントになります。【src/flow/registry.py†L41-L109】
- `FlowAction` 群は Discord へのレスポンス (View送信、モーダル表示、メッセージ編集/削除) を抽象化し、Interaction の followup/response を適切に使い分ける責務を持ちます。【src/flow/actions.py†L13-L156】
- `CommandContext` では state/result/history/options を一元管理し、`TypeRegistry` を通じて各ステートに許容される型を検証します。これによりハンドラ間でのデータ受け渡しに型安全性を持たせています。【src/models/context_model.py†L11-L91】【src/data_types/context_result_types.py†L10-L107】
- `AmidakujiState` 列挙はモード選択からテンプレート管理、メンバー割り当て、キャンセルまでの遷移を網羅しており、新しい状態を追加する際は列挙体・型レジストリ・ハンドラの 3 点を同時に更新することが原則です。【src/models/state_model.py†L4-L38】
- ハンドラからユースケースサービスへアクセスする際は `resolve_template_service()` などのヘルパーを経由し、サービス名を決め打ちで参照します。新しいサービスを渡したい場合は `CommandRuntimeServices` を拡張してからヘルパーを追加する必要があります。【src/flow/handlers/base.py†L17-L88】

## ユースケースとデータアクセス

- `TemplateApplicationService` はユーザー別テンプレート一覧、共有テンプレートのコピー、CRUD、最近利用テンプレート管理などテンプレート操作を一括提供します。Repository が返す生データに対し、スコープやデフォルトテンプレートの結合ルールをここで吸収します。【src/application/services/template_service.py†L19-L164】
- `HistoryApplicationService` は抽選履歴の保存/取得や埋め込み・抽選モードの設定変更 API を集約し、ドメインの `SelectionMode` 正規化を保証します。【src/application/services/history_service.py†L9-L67】
- `AmidakujiFlowService` はテンプレート作成・削除・直近テンプレート利用といったフロー固有の遷移を司り、条件に応じて `FlowTransitionDTO` を返して次のステートへ誘導します。【src/application/services/flow_service.py†L19-L94】
- これらユースケースは `DiscordCommandUseCases` で束ねられ、BotClient から単一インスタンスとして共有されます。流用時に Repository を複数生成しないことが暗黙ルールです。【src/presentation/discord/services.py†L16-L64】

## 永続化と Firebase ポリシー

- `TemplateRepository` プロトコルはテンプレート/履歴/ユーザー/設定/共有テンプレート操作の境界を定義し、Firestore 実装以外にも差し替えられるようメソッド群が明示されています。【src/domain/interfaces/repositories.py†L18-L125】
- `FirestoreTemplateRepository` は埋め込みモード・抽選モードの自動初期化、既定テンプレート生成、ユーザー初期化時のデフォルト注入、履歴書き込み、共有テンプレートクエリなど永続化に関わる非機能要件を一手に担います。【src/infrastructure/firestore/template_repository.py†L150-L450】
- `FirestoreUnitOfWork` は Firebase App/Client のライフサイクル管理とコレクション初期化を担当し、センチネルドキュメントで必須コレクションの存在を保証します。異なる App/Client を後から差し替えると例外にすることで多重初期化を防いでいます。【src/infrastructure/firestore/unit_of_work.py†L24-L122】
- `resolve_firebase_credentials()` は環境変数・ファイル・HTTP(S) URL を横断的に扱い、HTTP の場合はローカルキャッシュへ落とす方針です。CD/ローカル双方で認証情報の参照方法を統一できます。【src/infrastructure/config/firebase_credentials.py†L1-L109】
- `DBManager` は `FirestoreTemplateRepository` を継承した互換ラッパーで、シングルトンインスタンスを提供します。既存コードが `DBManager.get_instance()` に依存していても、新アーキテクチャ側の Repository 実装を共有できます。【src/db_manager.py†L17-L44】

## 運用・品質ポリシー

- 起動時セルフチェックでは Discord 認証・Firestore 接続・必須コレクションの健全性を検査し、失敗時は Bot を停止させます。結果は INFO/WARN/ERROR で色分けログとして出力されるため、監視時はこのログを一次指標とします。【src/services/startup_check.py†L18-L182】【src/presentation/discord/client.py†L48-L68】
- Slash コマンド完了後にユーザードキュメントが存在しなければ自動初期化し、統計ログを出すことで操作状況を把握しやすくしています。【src/presentation/discord/client.py†L76-L95】
- 環境変数の検証では Discord トークンの空白自動除去とハッシュ出力を義務付け、運用時に不正な値が混入した際には例外で早期検知します。【src/app/config.py†L50-L100】
- テストでは `InMemoryTemplateRepository` と `create_test_application()` を利用し、DI コンテナ経由で `BotClient` とユースケースをまとめて生成するのが標準です。スラッシュコマンド登録や DI の配線を含めて検証する `test_application_bootstrap` がリファレンスになります。【src/bootstrap/testing.py†L15-L190】【tests/test_application_bootstrap.py†L3-L28】

## 後方互換レイヤーと移行方針

- `src/views/` や `src/bot/` 以下は旧パッケージ構成との互換目的で `presentation.discord` の実装を再エクスポートしています。新規コードは `presentation.discord.*` を直接参照し、互換パスの更新は最小限に留めてください。【src/views/__init__.py†L1-L14】【src/views/view.py†L1-L4】【src/bot/__init__.py†L1-L11】【src/bot/config.py†L1-L15】
- レガシー呼び出しを置き換える際は、本書と `module-overview` の両方を更新し、互換レイヤーを削除しても支障がないことを確認したうえで整理します。【docs/references/module-overview.md†L1-L80】

---
この標準は随時アップデートされます。新しいレイヤーやフローを導入する場合は、関連するステート列挙・型レジストリ・ユースケース・永続化契約を同時に更新し、本書に反映してください。
