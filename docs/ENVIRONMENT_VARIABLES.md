# 環境変数設定ガイド

## 概要

PRISMの自動化機能は環境変数で設定を管理します。`.env`ファイルに設定を記述することで、各種機能の有効/無効や実行時刻、インターバルなどを制御できます。

**バージョン**: 2.0.0  
**更新日**: 2025年1月27日

## 設定ファイル

### .envファイルの作成
```bash
# env.exampleをコピーして.envファイルを作成
cp env.example .env

# .envファイルを編集
nano .env
```

### 環境別設定ファイル
- **開発環境**: `.env`
- **ステージング環境**: `.env.staging`
- **本番環境**: `.env.production`

## 環境変数一覧

### 基本設定
```bash
# PRISM 環境変数
PRISM_ENV=development
API_KEY=your-secure-api-key-here
OPENAI_API_KEY=sk-your-openai-key
NOTION_API_KEY=your_notion_api_key_here_key
MCP_BASE_URL=http://mcp-server:8063
```

### セキュリティ設定
```bash
# セキュリティ設定
CORS_ORIGINS=http://localhost:8061,http://localhost:3000
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
```

### ログ設定
```bash
# ログ設定
LOG_LEVEL=INFO
LOG_HUMAN=1
LOG_FILE=logs/prism.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
```

### キャッシュ設定
```bash
# キャッシュ設定
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
CACHE_ENABLED=true
```

### 自動仕訳設定
```bash
# 自動仕訳設定
AUTO_CLASSIFY_INTERVAL=120
AUTO_CLASSIFY_ENABLED=true
```

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `AUTO_CLASSIFY_INTERVAL` | 自動仕訳の実行間隔（秒） | 120 | 60, 120, 300 |
| `AUTO_CLASSIFY_ENABLED` | 自動仕訳の有効/無効 | true | true, false |

### 報告用メール設定
```bash
# 報告用メール設定
REPORT_EMAIL_ENABLED=false
REPORT_EMAIL_SMTP_HOST=smtp.gmail.com
REPORT_EMAIL_SMTP_PORT=587
REPORT_EMAIL_SMTP_USER=your-email@gmail.com
REPORT_EMAIL_SMTP_PASSWORD=your-app-password
REPORT_EMAIL_FROM=your-email@gmail.com
REPORT_EMAIL_TO=recipient@example.com
```

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `REPORT_EMAIL_ENABLED` | 報告用メールの有効/無効 | false | true, false |
| `REPORT_EMAIL_SMTP_HOST` | SMTPサーバーホスト | smtp.gmail.com | smtp.gmail.com |
| `REPORT_EMAIL_SMTP_PORT` | SMTPサーバーポート | 587 | 587, 465 |
| `REPORT_EMAIL_SMTP_USER` | SMTPユーザー名 | - | your-email@gmail.com |
| `REPORT_EMAIL_SMTP_PASSWORD` | SMTPパスワード | - | your-app-password |
| `REPORT_EMAIL_FROM` | 送信者メールアドレス | - | your-email@gmail.com |
| `REPORT_EMAIL_TO` | 宛先メールアドレス | - | recipient@example.com |

### 毎朝のタスク整理設定
```bash
# 毎朝のタスク整理設定
DAILY_SUMMARY_ENABLED=true
DAILY_SUMMARY_TIME=08:00
```

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `DAILY_SUMMARY_ENABLED` | 毎朝のタスク整理の有効/無効 | true | true, false |
| `DAILY_SUMMARY_TIME` | 実行時刻（HH:MM形式） | 08:00 | 07:30, 08:00, 09:00 |

### 毎夕の振り返り設定
```bash
# 毎夕の振り返り設定
DAILY_REFLECTION_ENABLED=true
DAILY_REFLECTION_TIME=18:00
```

| 変数名 | 説明 | デフォルト値 | 例 |
|--------|------|-------------|-----|
| `DAILY_REFLECTION_ENABLED` | 毎夕の振り返りの有効/無効 | true | true, false |
| `DAILY_REFLECTION_TIME` | 実行時刻（HH:MM形式） | 18:00 | 17:30, 18:00, 19:00 |

## 設定方法

### 1. 環境変数から自動仕訳設定
```bash
bash tools/setup_auto_classify_from_env.sh
```

### 2. 環境変数から毎朝のタスク整理設定
```bash
bash tools/setup_daily_summary_from_env.sh
```

### 3. 環境変数から毎夕の振り返り設定
```bash
bash tools/setup_daily_reflection_from_env.sh
```

### 4. 全設定を一括で行う
```bash
bash tools/setup_all_from_env.sh
```

## 設定例

### 基本的な設定例
```bash
# 基本設定
PRISM_ENV=production
API_KEY=your-api-key
OPENAI_API_KEY=sk-your-openai-key
NOTION_API_KEY=your-notion-key

# 自動仕訳（5分間隔）
AUTO_CLASSIFY_INTERVAL=300
AUTO_CLASSIFY_ENABLED=true

# 毎朝のタスク整理（7:30）
DAILY_SUMMARY_ENABLED=true
DAILY_SUMMARY_TIME=07:30

# 毎夕の振り返り（17:30）
DAILY_REFLECTION_ENABLED=true
DAILY_REFLECTION_TIME=17:30

# 報告用メール（無効）
REPORT_EMAIL_ENABLED=false
```

### メール有効化の設定例
```bash
# 報告用メール設定
REPORT_EMAIL_ENABLED=true
REPORT_EMAIL_SMTP_HOST=smtp.gmail.com
REPORT_EMAIL_SMTP_PORT=587
REPORT_EMAIL_SMTP_USER=your-email@gmail.com
REPORT_EMAIL_SMTP_PASSWORD=your-app-password
REPORT_EMAIL_FROM=your-email@gmail.com
REPORT_EMAIL_TO=admin@company.com
```

## 管理コマンド

### サービス状態確認
```bash
# 全サービス状態確認
launchctl list | grep prism

# 個別サービス状態確認
launchctl list | grep classify.interval
launchctl list | grep daily-summary
launchctl list | grep daily-reflection
```

### サービス管理
```bash
# 全サービス停止
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.*.plist

# 全サービス開始
launchctl load ~/Library/LaunchAgents/com.hovix.prism.*.plist

# 個別サービス停止
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.classify.interval.plist
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
```

### ログ監視
```bash
# 全ログ監視
tail -f logs/*.log

# 個別ログ監視
tail -f logs/classify_interval_out.log
tail -f logs/daily_summary_out.log
tail -f logs/daily_reflection_out.log
```

### 報告メール送信
```bash
# 手動で報告メール送信
python3 tools/send_report_email.py
```

## トラブルシューティング

### 環境変数が読み込まれない場合
1. `.env`ファイルの存在確認
   ```bash
   ls -la .env
   ```

2. 環境変数の確認
   ```bash
   source .env
   echo $AUTO_CLASSIFY_INTERVAL
   ```

3. 設定スクリプトの実行
   ```bash
   bash tools/setup_all_from_env.sh
   ```

### サービスが起動しない場合
1. サービス状態確認
   ```bash
   launchctl list | grep prism
   ```

2. エラーログ確認
   ```bash
   tail -f logs/*_err.log
   ```

3. 設定ファイル確認
   ```bash
   plutil -p ~/Library/LaunchAgents/com.hovix.prism.*.plist
   ```

### メール送信エラーの場合
1. メール設定確認
   ```bash
   python3 tools/send_report_email.py
   ```

2. SMTP設定確認
   - Gmailの場合: アプリパスワードを使用
   - ポート: 587 (TLS) または 465 (SSL)

## 関連ファイル

- `env.example`: 環境変数の雛形
- `.env`: 実際の環境変数設定（作成が必要）
- `tools/setup_auto_classify_from_env.sh`: 自動仕訳設定スクリプト
- `tools/setup_daily_summary_from_env.sh`: 毎朝のタスク整理設定スクリプト
- `tools/setup_daily_reflection_from_env.sh`: 毎夕の振り返り設定スクリプト
- `tools/setup_all_from_env.sh`: 全設定一括スクリプト
- `tools/send_report_email.py`: 報告メール送信スクリプト

