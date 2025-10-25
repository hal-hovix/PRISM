#!/bin/bash
# 毎夕の振り返りの実行時刻を変更

PLIST_FILE="$HOME/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist"

echo "=== 毎夕の振り返り 実行時刻変更 ==="
echo

# 現在の設定を確認
echo "📋 現在の設定:"
plutil -p "$PLIST_FILE" | grep -A 3 "StartCalendarInterval"
echo

# 新しい時刻を設定（現在時刻の1分後）
CURRENT_HOUR=$(date +%H)
CURRENT_MINUTE=$(date +%M)
NEXT_MINUTE=$((CURRENT_MINUTE + 1))

if [ $NEXT_MINUTE -ge 60 ]; then
    NEXT_MINUTE=0
    NEXT_HOUR=$((CURRENT_HOUR + 1))
    if [ $NEXT_HOUR -ge 24 ]; then
        NEXT_HOUR=0
    fi
else
    NEXT_HOUR=$CURRENT_HOUR
fi

echo "⏰ 新しい実行時刻: ${NEXT_HOUR}:$(printf "%02d" $NEXT_MINUTE)"
echo

# 設定ファイルを更新
plutil -replace StartCalendarInterval.Hour -integer $NEXT_HOUR "$PLIST_FILE"
plutil -replace StartCalendarInterval.Minute -integer $NEXT_MINUTE "$PLIST_FILE"

echo "✅ 設定を更新しました"
echo

# サービスを再読み込み
launchctl unload "$PLIST_FILE"
launchctl load "$PLIST_FILE"

echo "✅ サービスを再読み込みしました"
echo

# 更新された設定を確認
echo "📋 更新された設定:"
plutil -p "$PLIST_FILE" | grep -A 3 "StartCalendarInterval"
echo

echo "🎉 実行時刻を変更しました！"
echo "⏰ 次回実行: $(date -v +1M '+%Y-%m-%d %H:%M')"
echo
echo "📝 ログ監視:"
echo "  tail -f /Users/hal1956/development/PRISM/logs/daily_reflection_out.log"

