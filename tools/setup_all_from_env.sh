#!/bin/bash
# 環境変数からすべての自動化設定を一括で行う

SCRIPT_DIR="/Users/hal1956/development/PRISM"
ENV_FILE="$SCRIPT_DIR/.env"

echo "=== 環境変数から全自動化設定 ==="
echo

# .envファイルの存在確認
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .envファイルが見つかりません: $ENV_FILE"
    echo "env.exampleをコピーして.envファイルを作成してください"
    exit 1
fi

# 環境変数を読み込み
source "$ENV_FILE"

echo "📋 設定値:"
echo "  自動仕訳間隔: ${AUTO_CLASSIFY_INTERVAL:-120}秒"
echo "  自動仕訳有効: ${AUTO_CLASSIFY_ENABLED:-true}"
echo "  毎朝のタスク整理: ${DAILY_SUMMARY_ENABLED:-true} (${DAILY_SUMMARY_TIME:-08:00})"
echo "  毎夕の振り返り: ${DAILY_REFLECTION_ENABLED:-true} (${DAILY_REFLECTION_TIME:-18:00})"
echo "  報告用メール: ${REPORT_EMAIL_ENABLED:-false}"
echo

# 自動仕訳設定
if [ "${AUTO_CLASSIFY_ENABLED:-true}" = "true" ]; then
    echo "🔄 自動仕訳設定中..."
    bash "$SCRIPT_DIR/tools/setup_auto_classify_from_env.sh"
    echo
fi

# 毎朝のタスク整理設定
if [ "${DAILY_SUMMARY_ENABLED:-true}" = "true" ]; then
    echo "🌅 毎朝のタスク整理設定中..."
    bash "$SCRIPT_DIR/tools/setup_daily_summary_from_env.sh"
    echo
fi

# 毎夕の振り返り設定
if [ "${DAILY_REFLECTION_ENABLED:-true}" = "true" ]; then
    echo "🌅 毎夕の振り返り設定中..."
    bash "$SCRIPT_DIR/tools/setup_daily_reflection_from_env.sh"
    echo
fi

echo "🎉 全自動化設定が完了しました！"
echo
echo "📊 現在のサービス状態:"
launchctl list | grep prism
echo
echo "📝 管理コマンド:"
echo "  全サービス停止: launchctl unload ~/Library/LaunchAgents/com.hovix.prism.*.plist"
echo "  全サービス開始: launchctl load ~/Library/LaunchAgents/com.hovix.prism.*.plist"
echo "  ログ監視: tail -f $SCRIPT_DIR/logs/*.log"

