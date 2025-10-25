#!/bin/bash
# PRISM 自動仕分け設定スクリプト（120秒間隔版）

set -e

PRISM_DIR="/Users/hal1956/development/PRISM"
LOG_DIR="$PRISM_DIR/logs"

echo "=========================================="
echo "PRISM 自動仕分け設定（120秒間隔）"
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
echo "1) 120秒間隔（2分おき）- 高頻度"
echo "2) 300秒間隔（5分おき）- 中頻度"
echo "3) 600秒間隔（10分おき）- 低頻度"
echo "4) 1800秒間隔（30分おき）- 最低頻度"
echo "5) カスタム間隔（秒数指定）"
echo "0) スキップ（手動実行のみ）"
echo ""
read -p "選択 (0-5): " choice

case $choice in
    1)
        INTERVAL_SECONDS=120
        DESCRIPTION="120秒間隔（2分おき）"
        ;;
    2)
        INTERVAL_SECONDS=300
        DESCRIPTION="300秒間隔（5分おき）"
        ;;
    3)
        INTERVAL_SECONDS=600
        DESCRIPTION="600秒間隔（10分おき）"
        ;;
    4)
        INTERVAL_SECONDS=1800
        DESCRIPTION="1800秒間隔（30分おき）"
        ;;
    5)
        echo ""
        read -p "間隔を秒数で入力 (例: 120): " INTERVAL_SECONDS
        DESCRIPTION="カスタム: ${INTERVAL_SECONDS}秒間隔"
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
echo "  実行間隔: $DESCRIPTION"
echo "  間隔: ${INTERVAL_SECONDS}秒"
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

# 新しいcron設定を追加（毎分実行して内部で間隔制御）
NEW_CRON="* * * * * cd $PRISM_DIR && bash -c 'if [ ! -f $LOG_DIR/last_run ]; then touch $LOG_DIR/last_run; fi; if [ \$(date +%s) -gt \$(($(date +%s) - $INTERVAL_SECONDS + \$(cat $LOG_DIR/last_run 2>/dev/null || echo 0))) ]; then python3 tools/advanced_classify_inbox.py >> $LOG_DIR/classify_\$(date +\\%Y\\%m\\%d).log 2>&1; echo \$(date +%s) > $LOG_DIR/last_run; fi'"

if [ -z "$CURRENT_CRON" ]; then
    FULL_CRON="# PRISM 自動仕分け（${INTERVAL_SECONDS}秒間隔）
$NEW_CRON"
else
    FULL_CRON="$CURRENT_CRON

# PRISM 自動仕分け（${INTERVAL_SECONDS}秒間隔）
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
echo "実行間隔の変更:"
echo "  bash tools/setup_auto_classify_interval.sh"
echo ""
echo "cron設定の削除:"
echo "  crontab -e  # エディタで該当行を削除"
echo ""
echo "=========================================="
echo "✅ セットアップ完了！"
echo "=========================================="


