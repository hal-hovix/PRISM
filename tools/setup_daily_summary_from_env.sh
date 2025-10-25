#!/bin/bash
# 環境変数から毎朝のタスク整理を設定

SCRIPT_DIR="/Users/hal1956/development/PRISM"
ENV_FILE="$SCRIPT_DIR/.env"
PLIST_FILE="$HOME/Library/LaunchAgents/com.hovix.prism.daily-summary.plist"

echo "=== 環境変数から毎朝のタスク整理設定 ==="
echo

# .envファイルの存在確認
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .envファイルが見つかりません: $ENV_FILE"
    echo "env.exampleをコピーして.envファイルを作成してください"
    exit 1
fi

# 環境変数を読み込み
source "$ENV_FILE"

# 設定値を取得
ENABLED=${DAILY_SUMMARY_ENABLED:-true}
TIME=${DAILY_SUMMARY_TIME:-08:00}

echo "📋 設定値:"
echo "  有効: ${ENABLED}"
echo "  実行時刻: ${TIME}"
echo

if [ "$ENABLED" != "true" ]; then
    echo "⚠️  毎朝のタスク整理が無効になっています"
    echo "DAILY_SUMMARY_ENABLED=true に設定してください"
    exit 0
fi

# 時刻を解析
HOUR=$(echo "$TIME" | cut -d: -f1)
MINUTE=$(echo "$TIME" | cut -d: -f2)

# launchd設定ファイルを作成
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hovix.prism.daily-summary</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/hal1956/.pyenv/shims/python3</string>
        <string>/Users/hal1956/development/PRISM/tools/daily_task_summary.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/hal1956/development/PRISM</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/hal1956/.pyenv/shims:/Users/hal1956/.pyenv/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>PYENV_ROOT</key>
        <string>/Users/hal1956/.pyenv</string>
        <key>NOTION_API_KEY</key>
        <string>${NOTION_API_KEY}</string>
        <key>OPENAI_API_KEY</key>
        <string>${OPENAI_API_KEY}</string>
        <key>DAILY_SUMMARY_TIME</key>
        <string>${TIME}</string>
    </dict>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>${MINUTE}</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/hal1956/development/PRISM/logs/daily_summary_out.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/hal1956/development/PRISM/logs/daily_summary_err.log</string>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ launchd設定ファイルを作成しました: $PLIST_FILE"
echo

# 既存のサービスを停止
launchctl unload "$PLIST_FILE" 2>/dev/null || true

# 設定ファイルを読み込み
launchctl load "$PLIST_FILE"
echo "✅ launchdサービスを読み込みました"
echo

# 設定を確認
echo "📋 設定内容:"
plutil -p "$PLIST_FILE" | grep -A 3 "StartCalendarInterval"
echo

# サービス状態を確認
echo "🔍 サービス状態:"
launchctl list | grep daily-summary
echo

# ログディレクトリを作成
mkdir -p "$SCRIPT_DIR/logs"
echo "✅ ログディレクトリを作成しました: $SCRIPT_DIR/logs"
echo

echo "🎉 毎朝${TIME}に自動実行されるように設定しました！"
echo
echo "📝 管理コマンド:"
echo "  停止: launchctl unload $PLIST_FILE"
echo "  開始: launchctl load $PLIST_FILE"
echo "  状態確認: launchctl list | grep daily-summary"
echo "  ログ確認: tail -f $SCRIPT_DIR/logs/daily_summary_out.log"
echo
echo "⏰ 実行時刻: 毎朝${TIME}"
echo "📊 実行内容: 今日のタスク整理 + 今日の一言"

