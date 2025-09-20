# 外部サービス設定ガイド

## 概要
このドキュメントでは、Roulette DS Bot を運用するためにコード以外で準備が必要な外部サービスや設定項目をまとめます。Discord 側の設定、Firebase（Firestore）側の設定、そしてアプリケーションが参照する環境変数の扱いについて、実施手順を詳しく説明します。

## Discord 側の準備
### 1. アプリケーションと Bot の作成
1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセスし、「New Application」からアプリケーションを作成します。
2. 作成したアプリケーションの **Bot** タブで「Add Bot」を選択し、Bot を生成します。
3. Bot のユーザー名やアイコンを任意で設定します。

### 2. 必要な Privileged Intents の有効化
このアプリケーションは `discord.Intents.all()` を使用しているため、全ての Intent を有効にする必要があります。特に以下の Privileged Intent を忘れずに有効化してください。
- Presence Intent
- Server Members Intent
- Message Content Intent

> Bot タブの「Privileged Gateway Intents」セクションで各スイッチをオンにします。`discord.Intents.all()` を有効にして Bot を初期化している実装はコードに記載されています。【F:src/main.py†L33-L48】

### 3. Bot トークンの取得と管理
1. Bot タブの「Reset Token」を押して Bot トークンを発行します。
2. 発行されたトークンは **一度しか表示されない** ため、すぐに安全な場所に保存してください。
3. アプリケーションは環境変数 `CLIENT_TOKEN` からトークンを読み込みます。`.env` ファイルが存在すればそこから読み込まれ、存在しない場合は OS の環境変数を参照します。【F:src/main.py†L339-L384】
4. 運用環境では `.env` ファイルをリポジトリにコミットしないよう注意し、ホスティング先のシークレット管理機構（例: Docker/Compose の `environment`、GitHub Actions の Secrets など）を利用してください。

### 4. Bot の招待
1. Developer Portal の **OAuth2 > URL Generator** を開きます。
2. Scopes で `bot` と `applications.commands` を選択し、Bot Permissions で必要な権限（少なくとも Send Messages, Embed Links, Read Message History など）を付与します。
3. 生成された URL から Bot をサーバーに招待します。
4. 招待後、Bot がオンラインになっていること、スラッシュコマンドが自動的に同期されていることを確認してください（アプリケーションは起動時に `tree.sync()` を実行してコマンドを同期します）。【F:src/main.py†L62-L67】

## Firebase / Firestore 側の準備
### 1. Firebase プロジェクトの作成
1. [Firebase コンソール](https://console.firebase.google.com/) にアクセスし、新規プロジェクトを作成します。
2. プロジェクトに Google Analytics は必須ではありませんので、必要に応じて無効化しても問題ありません。

### 2. Firestore（Native モード）の有効化
1. Firebase コンソール内で「Firestore Database」を選択し、「データベースの作成」をクリックします。
2. モードは **Native モード** を選択してください。
3. 初期セキュリティルールは開発段階ではテストモードでも構いませんが、本番運用では適切なアクセス制御ルールに更新してください。

### 3. サービスアカウントキーの発行
1. Firebase コンソールの「プロジェクトの設定 > サービスアカウント」タブを開きます。
2. 「新しい秘密鍵を生成」から Admin SDK 用のサービスアカウントキー（JSON）をダウンロードします。
3. ダウンロードした JSON ファイルは安全なストレージに保管し、アプリケーションサーバーへ安全に配布できるようにします。

### 4. 認証情報の提供方法
アプリケーションは環境変数 `FIREBASE_CREDENTIALS` で指定された場所から認証情報を読み込みます。【F:src/services/app_context.py†L13-L37】

- `FIREBASE_CREDENTIALS` に **JSON ファイルのパス**（例: `/run/secrets/firebase.json` や `config/firebase.json`）を設定すると、そのファイルを直接読み込みます。
- もし環境によって直接ファイルを配置できない場合は、HTTPS でアクセスできる URL を `FIREBASE_CREDENTIALS` に指定できます。アプリケーションはその URL に GET リクエストを送り、レスポンスの JSON を資格情報として使用します。
- 認証情報が取得できない場合、アプリケーションは起動時に例外を発生させます。【F:src/services/app_context.py†L13-L37】

### 5. Firestore データ構造の確認
アプリケーションは Firestore 内で以下のコレクションを使用します。【F:src/db_manager.py†L35-L189】
- `users`: コマンドを実行した Discord ユーザーを記録します。
- `info`: 初期テンプレートや表示設定（例: `default_templates`, `embed_mode`）を保存します。Bot 起動時に `_init_default_templates()` が呼ばれ、パブリックテンプレートが自動的に書き込まれます。【F:src/main.py†L48-L55】【F:src/db_manager.py†L300-L342】
- `shared_templates`: 共有テンプレートの保存に使用します。
- `history`: 抽選結果の履歴を保存します。

Firestore のセキュリティルールでは、上記コレクションへの読み書きが Bot のサービスアカウントから許可されていることを確認してください。必要に応じてテスト用のデータを事前に投入することも可能ですが、Bot 自身が初回起動時に初期データを作成します。

## 環境変数とシークレットの設定
### `.env` ファイルを用いたローカル開発
- リポジトリ直下に `.env` ファイルを作成し、以下のように設定します。
  ```env
  CLIENT_TOKEN=discord_bot_token
  FIREBASE_CREDENTIALS=/absolute/path/to/firebase-service-account.json
  ```
- `.env` ファイルはバージョン管理対象から除外し、共有ストレージに保存しないでください。アプリケーションは `.env` が存在しない場合に警告を出しながらも OS 環境変数にフォールバックします。【F:src/main.py†L339-L359】

### コンテナ / 本番環境での設定
- Docker を利用する場合、`docker run` あるいは `docker-compose` の環境変数として `CLIENT_TOKEN` と `FIREBASE_CREDENTIALS` を渡してください。README でも同じ環境変数が必要であると案内されています。【F:README.md†L5-L26】
- 運用環境では、インフラ側のシークレット管理機能（Docker Secrets、Kubernetes Secret、CI/CD の暗号化シークレットなど）を使用し、トークンやサービスアカウントキーを平文で保存しない運用ルールを確立してください。

## チェックリスト
- [ ] Discord Developer Portal で Bot を作成し、必要な Privileged Intent を有効化した。
- [ ] Bot トークンを `CLIENT_TOKEN` として安全に供給できるようにした。
- [ ] Firebase プロジェクトを作成し、Firestore（Native モード）を有効化した。
- [ ] サービスアカウントキーをダウンロードし、安全に配布できるよう管理した。
- [ ] `FIREBASE_CREDENTIALS` 環境変数でキーを参照できるようにした。
- [ ] 本番運用向けのシークレット管理と Firestore セキュリティルールを整備した。

これらの手順を完了すれば、Roulette DS Bot を外部サービスと連携させて安全に稼働させる準備が整います。
