# Googleカレンダー同期ガイド

## 概要

PRISMシステムはGoogleカレンダーとNotionDBの"Task"と"ToDo"データベースを双方向で同期する機能を提供します。これにより、カレンダーアプリとタスク管理を統合して効率的に作業を管理できます。

## 機能

### 双方向同期
- **NotionDB → Googleカレンダー**: Task/ToDoの期日・実施日をカレンダーイベントとして作成
- **Googleカレンダー → NotionDB**: カレンダーイベントをTask/ToDoとして作成

### 同期対象
- **Taskデータベース**: 期日が設定されたタスク
- **ToDoデータベース**: 実施日が設定されたToDo
- **Googleカレンダー**: プライマリカレンダーのイベント

## セットアップ

### 1. Google Cloud Console設定

#### 1.1 プロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. プロジェクト名: "PRISM Calendar Sync"

#### 1.2 Google Calendar API有効化
1. 左側メニューから「APIとサービス」→「ライブラリ」を選択
2. "Google Calendar API"を検索
3. 「有効にする」をクリック

#### 1.3 OAuth2認証情報作成
1. 「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「OAuth クライアント ID」を選択
3. アプリケーションの種類: 「デスクトップアプリケーション」
4. 名前: "PRISM Calendar Sync"
5. 「作成」をクリック

#### 1.4 認証情報ファイルダウンロード
1. 作成されたOAuth2クライアントIDをクリック
2. 「JSONをダウンロード」をクリック
3. ダウンロードしたファイルを`credentials.json`として保存
4. `credentials.json`をPRISMプロジェクトのルートディレクトリに配置

### 2. 環境変数設定

`.env`ファイルに以下の設定を追加:

```bash
# Googleカレンダー同期設定
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_SYNC_INTERVAL=300
TASK_DATABASE_ID=your-task-database-id
TODO_DATABASE_ID=your-todo-database-id
```

#### 設定項目説明

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `GOOGLE_CALENDAR_ENABLED` | Googleカレンダー同期の有効/無効 | false | true, false |
| `GOOGLE_CALENDAR_SYNC_INTERVAL` | 同期実行間隔（秒） | 300 | 300, 600, 1800 |
| `TASK_DATABASE_ID` | Notion TaskデータベースID | - | 32文字のUUID |
| `TODO_DATABASE_ID` | Notion ToDoデータベースID | - | 32文字のUUID |

### 3. NotionデータベースID取得

#### 3.1 TaskデータベースID
1. NotionでTaskデータベースを開く
2. URLからデータベースIDを取得
   ```
   https://www.notion.so/your-workspace/TASK_DATABASE_ID?v=...
   ```

#### 3.2 ToDoデータベースID
1. NotionでToDoデータベースを開く
2. URLからデータベースIDを取得
   ```
   https://www.notion.so/your-workspace/TODO_DATABASE_ID?v=...
   ```

## 使用方法

### 1. 手動同期実行

```bash
# 双方向同期を実行
python3 tools/google_calendar_sync.py
```

### 2. 自動同期設定

```bash
# 環境変数から自動同期を設定
bash tools/setup_google_calendar_sync.sh
```

### 3. 同期確認

```bash
# サービス状態確認
launchctl list | grep google-calendar-sync

# ログ確認
tail -f logs/google_calendar_sync_out.log
```

## 同期ルール

### NotionDB → Googleカレンダー

#### 同期条件
- 期日・実施日が設定されている
- ステータスが「完了」以外

#### 同期内容
- **タイトル**: タスク名・ToDo名
- **日時**: 期日・実施日（09:00-10:00の1時間イベント）
- **説明**: 内容プロパティ
- **タイムゾーン**: Asia/Tokyo

### Googleカレンダー → NotionDB

#### 同期条件
- プライマリカレンダーのイベント
- 過去30日以内のイベント

#### 同期内容
- **Taskデータベース**: タスク名、期日、ステータス（未完了）、内容
- **ToDoデータベース**: ToDo名、実施日、ステータス（未完了）、内容

## トラブルシューティング

### 認証エラー

#### 問題: `credentials.json`が見つからない
```
❌ credentials.jsonファイルが見つかりません
```

**解決方法:**
1. Google Cloud ConsoleでOAuth2認証情報を作成
2. JSONファイルをダウンロード
3. `credentials.json`としてプロジェクトルートに配置

#### 問題: 認証フローが失敗する
```
❌ GoogleカレンダーAPI認証エラー
```

**解決方法:**
1. `credentials.json`の内容を確認
2. Google Cloud ConsoleでOAuth2設定を確認
3. リダイレクトURIが`http://localhost`に設定されているか確認

### 同期エラー

#### 問題: NotionDBアクセスエラー
```
❌ NotionDB取得エラー: 401
```

**解決方法:**
1. `NOTION_API_KEY`が正しく設定されているか確認
2. Notion APIキーが有効か確認
3. データベースIDが正しいか確認

#### 問題: データベースIDエラー
```
❌ Task/ToDoデータベースIDが設定されていません
```

**解決方法:**
1. `.env`ファイルに`TASK_DATABASE_ID`と`TODO_DATABASE_ID`を設定
2. データベースIDが32文字のUUID形式か確認

### サービスエラー

#### 問題: launchdサービスが起動しない
```
❌ サービス状態確認で何も表示されない
```

**解決方法:**
1. 設定ファイルの構文を確認
   ```bash
   plutil -p ~/Library/LaunchAgents/com.hovix.prism.google-calendar-sync.plist
   ```
2. ログファイルを確認
   ```bash
   tail -f logs/google_calendar_sync_err.log
   ```
3. サービスを再読み込み
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.hovix.prism.google-calendar-sync.plist
   launchctl load ~/Library/LaunchAgents/com.hovix.prism.google-calendar-sync.plist
   ```

## 管理コマンド

### サービス管理
```bash
# サービス停止
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.google-calendar-sync.plist

# サービス開始
launchctl load ~/Library/LaunchAgents/com.hovix.prism.google-calendar-sync.plist

# サービス状態確認
launchctl list | grep google-calendar-sync
```

### ログ監視
```bash
# 出力ログ監視
tail -f logs/google_calendar_sync_out.log

# エラーログ監視
tail -f logs/google_calendar_sync_err.log

# 全ログ監視
tail -f logs/google_calendar_sync_*.log
```

### 設定確認
```bash
# 環境変数確認
grep -E "GOOGLE_CALENDAR|TASK_DATABASE|TODO_DATABASE" .env

# 設定ファイル確認
plutil -p ~/Library/LaunchAgents/com.hovix.prism.google-calendar-sync.plist
```

## セキュリティ

### 認証情報の管理
- `credentials.json`: Google Cloud ConsoleでダウンロードしたOAuth2認証情報
- `token.pickle`: 自動生成される認証トークン（再認証時に更新）
- これらのファイルは`.gitignore`に追加済み

### データ保護
- 同期されるデータは最小限（タイトル、日時、説明のみ）
- 個人情報や機密情報は同期されません
- ローカル環境でのみ動作

## 関連ファイル

- `tools/google_calendar_sync.py`: メイン同期スクリプト
- `tools/setup_google_calendar_sync.sh`: 自動同期設定スクリプト
- `credentials.json`: Google OAuth2認証情報（作成が必要）
- `token.pickle`: 認証トークン（自動生成）
- `logs/google_calendar_sync_*.log`: 同期ログ

## 制限事項

- GoogleカレンダーAPIの利用制限に従う
- Notion APIの利用制限に従う
- 同期間隔は最小300秒（5分）推奨
- 大量のデータ同期時は時間がかかる場合があります

