# FlowController 利用ガイド

このガイドでは、`FlowController` を用いて状態遷移と Discord への応答を駆動するための実践的な手順をまとめます。状態列挙 `AmidakujiState` と `CommandContext` を組み合わせることで、複雑な UI フローを安全に実装できます。

## 基本構成

1. `CommandContext` を初期化して、実行中のインタラクション・現在の状態・利用サービスを束ねます。【src/models/context_model.py†L12-L52】
2. `FlowController` にコンテキストとサービス束を渡し、状態ごとのハンドラーを登録します。【src/data_interface.py†L31-L83】
3. ビューやボタンのコールバックで `dispatch` を呼び出し、遷移後に返却された `FlowAction` 群を実行します。【src/data_interface.py†L85-L121】【src/views/view.py†L82-L138】

```python
# 代表的な利用例
context = CommandContext(
    interaction=interaction,
    state=AmidakujiState.MODE_CREATE_NEW,
    services=None,
)
flow = FlowController(context, services_bundle)
await flow.dispatch(
    state=AmidakujiState.MODE_CREATE_NEW,
    result=None,
    interaction=interaction,
)
```

## アクションの使い分け

- `SendMessageAction` は埋め込み・ビュー付きのメッセージを送る汎用アクションです。`followup` を `True` にするとフォローアップ送信になります。【src/flow/actions.py†L59-L95】
- `SendViewAction` と `ShowModalAction` はインタラクションに応じた UI コンポーネントを表示したい場合に使用します。【src/flow/actions.py†L25-L57】【src/flow/actions.py†L45-L57】
- `DeferResponseAction` は長時間処理の前にレスポンスをディファーするためのものです。レスポンス済みかは自動判定されます。【src/flow/actions.py†L97-L108】

## ハンドラー実装のポイント

- `BaseStateHandler` を継承したクラスの `handle` は、`CommandContext` を更新しつつ必要なアクションを返します。【src/flow/handlers.py†L18-L52】
- 選択肢の状態同期など繰り返し利用する処理は `CommandContext` の `set_option_snapshot` で統一できます。【src/models/context_model.py†L54-L79】
- 連続した状態遷移が必要な場合は `context.state` を更新し、追加の `FlowAction` を返すことで制御します。【src/flow/handlers.py†L200-L280】

## ビューからの呼び出し

`ModeSelectionView` や各 UI コンポーネントのコールバックでは、インタラクションを `CommandContext` に設定してから `FlowController.dispatch` を呼び出します。これにより、同一コンテキストで結果履歴が記録され、後続のハンドラーが値を参照できます。【src/views/view.py†L60-L140】

## エラーハンドリング

- `dispatch` は登録されていない状態を検出すると `ValueError` を送出します。ハンドラー追加時には `FlowController._handlers` を更新することを忘れないでください。【src/data_interface.py†L101-L109】
- ハンドラー内で発生した例外は呼び出し元に伝播するため、必要に応じて `try`/`except` でログを出力してください。

## テスト戦略のヒント

- `CommandContext` 単体のテストでは `TypeRegistry` に登録された型と一致する結果がセットされるかを確認します。【src/models/context_model.py†L30-L52】
- ハンドラーのテストでは `FlowAction` モックを使い、正しい順序で返却されることを検証します。

---
状態駆動の設計に従うことで、Discord UI の変更にも柔軟に追従できます。他機能を追加するときも、ここで紹介したパターンを再利用してください。
