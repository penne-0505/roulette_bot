# Roulette DS Bot ユーザー体験要件

## ドキュメントの目的
Roulette DS Bot の現行コードから読み取れるユーザー体験要件を整理し、リアーキテクチャ後も同等の振る舞いを維持できているかを検証するための基準として利用します。ボットはあみだくじ形式の割り当てを支援し、テンプレートの作成・共有・履歴参照といったワークフローを備えています。【F:README.md†L1-L12】

## 実行環境と構成
- Python 3.12 以降と Poetry 1.8 以降を利用し、Discord ボットトークン (`CLIENT_TOKEN`) と Firebase 認証情報 (`FIREBASE_CREDENTIALS`) が必須です。【F:README.md†L14-L19】
- `python src/main.py` を実行するとロギングを初期化した上で設定を読み込み、Discord クライアントを起動します。【F:src/main.py†L6-L26】
- 構成読み込み後は Firebase の資格情報から `FirestoreTemplateRepository` を初期化し、コマンドを登録した `BotClient` をトークンと共に起動します。【F:src/bootstrap/app.py†L19-L88】【F:src/app/container.py†L5-L28】

## 起動シーケンスと自己診断
- クライアントは起動時にスラッシュコマンドを同期し、既定テンプレートを確保した後にセルフチェックを実行します。【F:src/presentation/discord/client.py†L35-L86】
- セルフチェックは Discord 認証、Firestore 接続、必須コレクションの有無を診断し、致命的エラーがあればクライアントを終了させます。【F:src/services/startup_check.py†L35-L182】

## データ永続化と既定値
- Firestore へは `FirestoreTemplateRepository` 経由でアクセスし、既定テンプレートや共有テンプレート、履歴、埋め込み表示モード、抽選モードなどを管理します。【F:src/infrastructure/firestore/template_repository.py†L150-L580】
- 既定テンプレートとして「League of Legends」「Valorant」が初期化され、全ユーザーが利用できます。【F:src/infrastructure/firestore/template_repository.py†L209-L308】
- ユーザー初期化時には既定テンプレートが個人テンプレートとして複製されます。【F:src/infrastructure/firestore/template_repository.py†L365-L432】
- 抽選結果の履歴保存には、テンプレート名・選択肢・抽選モード・参加者割り当てが記録され、履歴照会で利用されます。【F:src/infrastructure/firestore/template_repository.py†L310-L364】

## スラッシュコマンド別の期待体験
### `/ping`
- 実行すると接続遅延やプロセス資源、稼働時間を含む埋め込みを返します。最初は「測定中...」を表示し、完了後に結果へ更新します。【F:src/presentation/discord/commands/registry.py†L64-L137】
- 埋め込みはタイトルに「🏓 Pong!」を掲げ、緑色テーマで接続・ステータス・システム情報をコードブロック形式で 3 段構成表示し、稼働時間を秒と人間向けフォーマットで併記します。【F:src/presentation/discord/commands/registry.py†L82-L124】

### `/amidakuji`
- 実行者専用のエフェメラル応答としてモード選択ビューを表示し、既存テンプレート利用、新規作成、履歴利用、共有テンプレート利用を誘導します。【F:src/presentation/discord/commands/registry.py†L138-L159】【F:src/presentation/discord/views/view.py†L120-L126】
- フロー制御は `FlowController` が担当し、状態ごとにハンドラを切り替えて処理します。【F:src/data_interface.py†L36-L104】【F:src/models/state_model.py†L4-L40】
- モード選択ビューは既存・共有・公開テンプレート向けのプライマリボタンと履歴参照用セカンダリボタンで構成され、押下後はビュー全体が無効化されて誤操作を防ぎます。【F:src/components/button.py†L137-L206】

### `/amidakuji_template_create`
- 新規テンプレート作成フローを即時実行し、タイトル入力や選択肢追加のモーダル、テンプレート保存アクションへ遷移します。【F:src/presentation/discord/commands/registry.py†L160-L181】【F:src/components/button.py†L1-L44】
- 選択肢編集ビューはプライマリの追加ボタン、セカンダリの上下移動ボタン、危険色の削除ボタン、保存用プライマリボタンを行単位で配置し、候補が 2 件未満の場合は保存を無効化します。【F:src/presentation/discord/views/view.py†L79-L118】【F:src/components/button.py†L17-L125】

### `/amidakuji_template_manage`
- 個人テンプレートが存在しない場合は注意埋め込みを返し、存在する場合は編集ビューをエフェメラル表示します。【F:src/presentation/discord/commands/registry.py†L182-L215】
- 編集ビューではテンプレート選択、候補追加・並べ替え・削除、保存・破棄、テンプレート削除までを一貫して操作できます。【F:src/presentation/discord/views/template_management.py†L86-L200】
- 編集用埋め込みはブランディングカラーで候補一覧を段番号付きで表示し、選択中候補を太字で強調、フッターで変更有無を通知します。【F:src/presentation/discord/views/template_management.py†L155-L178】
- 補助通知は同色の簡易埋め込みでエフェメラル表示され、テンプレート選択肢の説明には最大 3 件の候補プレビューが付与されます。【F:src/presentation/discord/views/template_management.py†L12-L139】【F:src/presentation/discord/views/template_management.py†L183-L199】

### `/toggle_embed_mode`
- 埋め込み表示形式（コンパクト／詳細）を切り替えるビューを表示し、実行者のみが操作できます。確定・キャンセル時は状態を示す埋め込みへ更新します。【F:src/presentation/discord/commands/registry.py†L217-L241】【F:src/presentation/discord/views/embed_mode.py†L17-L120】
- 初期表示は blurple、変更後は緑、キャンセル時は灰色の埋め込みカラーを使い分け、フッターで操作方法を案内します。ボタンはプライマリ「変更する」とセカンダリ「キャンセル」の二択です。【F:src/presentation/discord/views/embed_mode.py†L17-L120】

### `/amidakuji_template_list`
- 個人／サーバー共有／公開テンプレートをカテゴリ切り替えや検索付きで閲覧できるビューを表示します。対象がない場合はその旨を表示します。【F:src/presentation/discord/commands/registry.py†L243-L268】【F:src/presentation/discord/views/template_list.py†L24-L208】
- 埋め込みはカテゴリ説明または検索条件を冒頭に明示し、各テンプレートを太字タイトルと候補プレビュー・スコープ注記の組み合わせで列挙、フッターで件数とページ位置を表示します。【F:src/presentation/discord/views/template_list.py†L150-L208】
- ビューはカテゴリタブ、ページング、検索開始・解除、閉じる（赤色）ボタンを整列させ、検索モード中はカテゴリタブを灰色に固定してフィルタ状態を示します。【F:src/presentation/discord/views/template_list.py†L48-L209】【F:src/presentation/discord/views/template_list.py†L283-L361】

### `/amidakuji_selection_mode`
- 抽選モード（完全ランダム／偏り軽減）を確認・変更するビューを表示し、操作は実行者に限定されます。変更時はモードが永続化されます。【F:src/presentation/discord/commands/registry.py†L270-L294】【F:src/presentation/discord/views/selection_mode.py†L17-L124】
- 埋め込みは現在・変更後・キャンセルで色を切り替え（blurple／緑／灰）、プライマリとセカンダリの 2 ボタンで意思決定を促します。【F:src/presentation/discord/views/selection_mode.py†L17-L124】

### `/amidakuji_history`
- ギルド内の直近履歴をページング表示し、テンプレート名による検索やページサイズ変更、再読み込み、閉じる操作を提供します。【F:src/presentation/discord/commands/registry.py†L297-L320】【F:src/presentation/discord/views/history_list.py†L14-L200】
- 履歴埋め込みは青基調で最新時刻をタイムスタンプに設定し、各履歴をテンプレート名＋実行時刻＋抽選モードのヘッダーと「ユーザー → 選択肢」の本文で表示、長文は 1024 文字に収めます。【F:src/presentation/discord/views/history_list.py†L24-L244】
- ビューは前後ページ、再読み込み、テンプレートセレクト、ページサイズ切り替え、検索モーダル、リセット、閉じる（危険色）などを複数行に整列し、条件に応じて無効化します。【F:src/presentation/discord/views/history_list.py†L32-L334】

### `/amidakuji_template_share`
- 個人テンプレートのサーバー共有・グローバル公開、および既存共有の解除を行うビューを表示します。共有済みが存在しない場合は注意埋め込みのみを返します。【F:src/presentation/discord/commands/registry.py†L323-L383】【F:src/presentation/discord/views/template_sharing.py†L12-L324】
- 共有ビューの埋め込みは blurple カラーで、選択状況に応じた説明と保有数を 3 つのフィールドに整理して表示します。【F:src/presentation/discord/views/template_sharing.py†L91-L121】
- ボタンは共有（プライマリ）、共有解除（セカンダリ）、テンプレートセレクト、閉じる（危険色）で構成され、スコープに応じて自動的に有効・無効が切り替わります。【F:src/presentation/discord/views/template_sharing.py†L43-L70】【F:src/presentation/discord/views/template_sharing.py†L152-L200】

## インタラクティブビュー仕様
- 各ビューは操作を実行したユーザーのみが操作可能で、トグルや保存後はボタンが無効化されます。特に埋め込み／抽選モードビューでは `interaction_check` でユーザーを検証します。【F:src/presentation/discord/views/embed_mode.py†L72-L88】【F:src/presentation/discord/views/selection_mode.py†L66-L82】
- テンプレート一覧ビューはカテゴリ切り替えと検索モーダル、ページングボタンを持ち、検索モード時はカテゴリボタンを無効化します。【F:src/presentation/discord/views/template_list.py†L78-L208】
- 履歴ビューはテンプレート候補のサジェスト、絞り込み解除、ページサイズ変更、モーダル入力など複合 UI を持ち、タイムアウト時はコンポーネントを無効化します。【F:src/presentation/discord/views/history_list.py†L46-L214】
- テンプレート共有ビューはテンプレートの現在スコープに応じて操作ボタンを自動的に有効／無効化し、タイトル重複時には自動リネームを行います。【F:src/presentation/discord/views/template_sharing.py†L59-L264】
- ボタンは操作内容に応じて Discord 標準スタイル（プライマリ=青、セカンダリ=灰、サクセス=緑、デンジャー=赤）を使い分け、破壊的操作や肯定操作を視覚的に区別します。【F:src/components/button.py†L17-L289】【F:src/presentation/discord/views/template_list.py†L283-L361】
- 選択コンポーネントは候補の有無に応じて説明テキストやプレースホルダーを切り替え、利用できない場合は自動で無効化します。【F:src/presentation/discord/views/template_management.py†L127-L153】【F:src/presentation/discord/views/history_list.py†L262-L303】

## 抽選結果生成と表示モード
- 抽選ロジックは選択モード（完全ランダム／偏り軽減）に応じてペアリングを生成し、結果埋め込みはモードに応じてコンパクト版または詳細版を作成します。【F:src/data_process.py†L21-L78】【F:src/data_process.py†L104-L140】
- コンパクト表示は著者欄に参加者のアバターと選択肢名のみを表示し、詳細表示はタイトルに「> 選択肢」を掲げた上で著者欄に参加者名とアバターを並べます。【F:src/data_process.py†L82-L101】
- 抽選履歴に保存される選択モードは結果一覧のヘッダーでも表示され、ユーザーが過去の設定を把握できるようになっています。【F:src/presentation/discord/views/history_list.py†L214-L248】

## 受け入れ観点チェックリスト
- [ ] 全スラッシュコマンドが応答し、想定したビューまたは埋め込みを表示する。
- [ ] 各ビューの操作が実行者以外にブロックされ、操作完了後は適切にボタンが無効化される。
- [ ] テンプレートの作成・編集・共有・削除、および履歴閲覧が Firestore を通じて永続化・参照できる。
- [ ] 埋め込み表示モードと抽選モードの切り替えが永続化され、抽選結果生成に反映される。
- [ ] 起動時セルフチェックが成功し、失敗時はクライアントが安全に停止する。
