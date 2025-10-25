#!/bin/bash
# PRISM 自動仕分け設定スクリプト

set -e

PRISM_DIR="/Users/hal1956/development/PRISM"
LOG_DIR="$PRISM_DIR/logs"

echo "=========================================="
echo "PRISM 自動仕分け設定"
echo "=========================================="
echo ""

# ログディレクトリ作成
echo "📁 ログディレクトリを作成..."
mkdir -p "$LOG_DIR"
echo "✓ 完了: $LOG_DIR"
echo ""

# 実行タイミングを選択
echo "⏰ 自動実行のタイミングを選択してください:"
echo ""
echo "1) 毎朝 9:00（初心者向け）"
echo "2) 毎朝 9:00 と 毎晩 21:00（標準）"
echo "3) 2時間おき（パワーユーザー向け）"
echo "4) 平日のみ 毎朝 9:00"
echo "5) 週次（毎週月曜 9:00）"
echo "6) カスタム設定"
echo "0) スキップ（手動実行のみ）"
echo ""
read -p "選択 (0-6): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 9 * * *"
        DESCRIPTION="毎朝 9:00"
        ;;
    2)
        CRON_SCHEDULE="0 9,21 * * *"
        DESCRIPTION="毎朝 9:00 と 毎晩 21:00"
        ;;
    3)
        CRON_SCHEDULE="0 */2 * * *"
        DESCRIPTION="2時間おき"
        ;;
    4)
        CRON_SCHEDULE="0 9 * * 1-5"
        DESCRIPTION="平日 9:00"
        ;;
    5)
        CRON_SCHEDULE="0 9 * * 1"
        DESCRIPTION="毎週月曜 9:00"
        ;;
    6)
        echo ""
        read -p "cron形式で入力 (例: 0 9 * * *): " CRON_SCHEDULE
        DESCRIPTION="カスタム: $CRON_SCHEDULE"
        ;;
    0)
        echo ""
        echo "✓ 自動実行の設定をスキップしました"
        echo ""
        echo "手動で実行する場合:"
        echo "  cd $PRISM_DIR"
        echo "  python3 tools/advanced_classify_inbox.py"
        exit 0
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac

echo ""
echo "📝 設定内容:"
echo "  実行タイミング: $DESCRIPTION"
echo "  cron形式: $CRON_SCHEDULE"
echo ""

# 現在のcronを確認
echo "🔍 現在のcron設定を確認..."
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

if echo "$CURRENT_CRON" | grep -q "advanced_classify_inbox.py"; then
    echo "⚠️  既存のPRISM自動仕分け設定が見つかりました"
    echo ""
    read -p "上書きしますか？ (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "❌ キャンセルしました"
        exit 0
    fi
    # 既存の設定を削除
    CURRENT_CRON=$(echo "$CURRENT_CRON" | grep -v "advanced_classify_inbox.py" || echo "")
fi

# 新しいcron設定を追加
NEW_CRON="$CRON_SCHEDULE cd $PRISM_DIR && python3 tools/advanced_classify_inbox.py >> $LOG_DIR/classify_\$(date +\\%Y\\%m\\%d).log 2>&1"

if [ -z "$CURRENT_CRON" ]; then
    FULL_CRON="# PRISM 自動仕分け
$NEW_CRON"
else
    FULL_CRON="$CURRENT_CRON

# PRISM 自動仕分け
$NEW_CRON"
fi

# cronに登録
echo ""
echo "📝 cronに登録中..."
echo "$FULL_CRON" | crontab -

echo "✓ 完了"
echo ""

# 確認
echo "=========================================="
echo "✅ 設定完了"
echo "=========================================="
echo ""
echo "設定された内容:"
crontab -l | grep -A 1 "PRISM"
echo ""

# テスト実行
echo "🧪 テスト実行を行いますか？"
read -p "今すぐ仕分けを実行しますか？ (y/N): " test_run

if [[ $test_run =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 仕分けを実行中..."
    cd "$PRISM_DIR"
    python3 tools/advanced_classify_inbox.py
fi

echo ""
echo "=========================================="
echo "📚 使い方"
echo "=========================================="
echo ""
echo "cron設定の確認:"
echo "  crontab -l"
echo ""
echo "手動実行:"
echo "  cd $PRISM_DIR"
echo "  python3 tools/advanced_classify_inbox.py"
echo ""
echo "ログ確認:"
echo "  tail -f $LOG_DIR/classify_*.log"
echo ""
echo "cron設定の削除:"
echo "  crontab -e  # エディタで該当行を削除"
echo ""
echo "=========================================="
echo "✅ セットアップ完了！"
echo "=========================================="


