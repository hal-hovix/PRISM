#!/bin/bash
# 環境変数から自動仕訳のインターバルを設定

SCRIPT_DIR="/Users/hal1956/development/PRISM"
ENV_FILE="$SCRIPT_DIR/.env"
PLIST_FILE="$HOME/Library/LaunchAgents/com.hovix.prism.classify.interval.plist"

echo "=== 環境変数から自動仕訳インターバル設定 ==="
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
INTERVAL=${AUTO_CLASSIFY_INTERVAL:-120}
ENABLED=${AUTO_CLASSIFY_ENABLED:-true}

echo "📋 設定値:"
echo "  インターバル: ${INTERVAL}秒"
echo "  有効: ${ENABLED}"
echo

if [ "$ENABLED" != "true" ]; then
    echo "⚠️  自動仕訳が無効になっています"
    echo "AUTO_CLASSIFY_ENABLED=true に設定してください"
    exit 0
fi

# launchd設定ファイルを作成
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hovix.prism.classify.interval</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/hal1956/.pyenv/shims/python3</string>
        <string>/Users/hal1956/development/PRISM/tools/advanced_classify_inbox.py</string>
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
        <key>AUTO_CLASSIFY_INTERVAL</key>
        <string>${INTERVAL}</string>
    </dict>
    
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    
    <key>StandardOutPath</key>
    <string>/Users/hal1956/development/PRISM/logs/classify_interval_out.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/hal1956/development/PRISM/logs/classify_interval_err.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
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
plutil -p "$PLIST_FILE" | grep -A 1 "StartInterval"
echo

# サービス状態を確認
echo "🔍 サービス状態:"
launchctl list | grep classify.interval
echo

# ログディレクトリを作成
mkdir -p "$SCRIPT_DIR/logs"
echo "✅ ログディレクトリを作成しました: $SCRIPT_DIR/logs"
echo

echo "🎉 自動仕訳が${INTERVAL}秒間隔で実行されるように設定しました！"
echo
echo "📝 管理コマンド:"
echo "  停止: launchctl unload $PLIST_FILE"
echo "  開始: launchctl load $PLIST_FILE"
echo "  状態確認: launchctl list | grep classify.interval"
echo "  ログ確認: tail -f $SCRIPT_DIR/logs/classify_interval_out.log"
echo
echo "⏰ 実行間隔: ${INTERVAL}秒"
echo "📊 実行内容: INBOXの自動仕分け"

