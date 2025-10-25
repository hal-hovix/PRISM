# 毎夕の振り返り機能

## 概要

毎夕18:00に自動実行される振り返り機能です。Notionの各データベースから今日のタスクを取得し、完了状況を確認して振り返りを行います。また、日替わりの振り返り用名言も表示されます。

## 機能

### 📋 タスク振り返り
- **Task**: 期日が今日または未設定のタスク
- **ToDo**: 実施日が今日または未設定のToDo
- **Project**: 終了予定日が今日または未設定のプロジェクト
- **Habit**: 実行日が今日または未設定の習慣
- **Knowledge**: 登録日が今日または未設定の知識
- **Note**: 日付が今日または未設定のメモ

### 🎯 タスク分類
- **✅ 完了**: ステータスが「完了」のタスク
- **🔄 進行中**: ステータスが「進行中」のタスク
- **📝 未着手**: その他のタスク
- **🔄 習慣**: 習慣データベースのタスク（完了/未完了表示）
- **📚 知識**: 知識データベースのタスク
- **📝 メモ**: メモデータベースのタスク

### 📈 完了率サマリー
- **完了タスク数**: 完了したタスクの数
- **総タスク数**: 今日の全タスク数
- **完了率**: 完了率の計算と表示
- **完了率に応じたメッセージ**:
  - 80%以上: 🎉 素晴らしい一日でした！
  - 60%以上: 👍 良い一日でした！
  - 40%以上: 📝 明日も頑張りましょう！
  - 40%未満: 💪 明日はもっと頑張りましょう！

### 💭 今日の振り返り名言
- 日付に基づいて同じ名言を選ぶ
- 10種類の振り返り用名言からランダム選択
- 毎日異なる名言が表示される
- **著作者名と出典元を併記**

## 設定

### 自動実行設定
```bash
# 設定ファイル
~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist

# 実行時刻
毎夕18:00

# 実行内容
python3 tools/daily_reflection.py
```

### ログファイル
- **標準出力**: `/Users/hal1956/development/PRISM/logs/daily_reflection_out.log`
- **エラー出力**: `/Users/hal1956/development/PRISM/logs/daily_reflection_err.log`

## 使用方法

### 手動実行
```bash
cd /Users/hal1956/development/PRISM
python3 tools/daily_reflection.py
```

### 自動実行設定
```bash
# 設定
bash tools/setup_daily_reflection.sh

# テスト実行（1分後）
bash tools/test_daily_reflection.sh
```

### 管理コマンド
```bash
# サービス状態確認
launchctl list | grep daily-reflection

# 設定確認
plutil -p ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist

# ログ監視
tail -f /Users/hal1956/development/PRISM/logs/daily_reflection_out.log

# サービス停止
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist

# サービス開始
launchctl load ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
```

## 実行時刻変更

### 時刻変更
```bash
# 18:00に設定
plutil -replace StartCalendarInterval.Hour -integer 18 ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
plutil -replace StartCalendarInterval.Minute -integer 0 ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist

# サービス再読み込み
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
launchctl load ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
```

### カスタム時刻設定
```bash
# 例: 17:30に設定
plutil -replace StartCalendarInterval.Hour -integer 17 ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
plutil -replace StartCalendarInterval.Minute -integer 30 ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
```

## 出力例

```
🌅 お疲れ様でした！
============================================================
📅 日付: 2025年10月23日 (Thursday)
⏰ 時刻: 18:00

📋 タスクを取得中...
📋 今日のタスク振り返り
==================================================
📊 総タスク数: 7件

🔄 習慣 (3件)
  ⏳ 毎日30分の英語学習
  ⏳ 毎朝のチーム朝会
  ⏳ 週3回のジム通い

📚 知識 (3件)
  • AWSのセキュリティ設定について学ぶ
  • データベース設計のベストプラクティス
  • 今日学んだこと: TypeScriptのジェネリクス

📝 メモ (1件)
  • 読書メモ: エンジニアリング組織論への招待

📈 完了率サマリー
==================================================
完了タスク: 0件
総タスク数: 7件
完了率: 0.0%

💪 明日はもっと頑張りましょう！

💭 今日の振り返り
==================================================
「今日の学びを明日に活かそう。」
— スティーブ・ジョブズ (Apple共同創業者)

✨ 今日もお疲れ様でした！
============================================================
```

## 名言一覧

### 松下幸之助（パナソニック創業者）
- 「今日の振り返りが明日の成長につながる。」
- 「振り返りこそが成長の源である。」
- 「継続は力なり。」
- 「感謝の気持ちを忘れずに。」

### 稲盛和夫（京セラ・KDDI創業者）
- 「一日の終わりに感謝を忘れずに。」
- 「今日の努力が明日の成果となる。」
- 「今日も成長の一日だった。」

### ビジネス界の著名人
- **スティーブ・ジョブズ**: 「今日の学びを明日に活かそう。」

### 禅語
- 「一日一生」（禅の教え）
- 「今日という日を大切に過ごせたか。」（禅の教え）

## トラブルシューティング

### 実行されない場合
1. サービス状態を確認
   ```bash
   launchctl list | grep daily-reflection
   ```

2. 設定ファイルを確認
   ```bash
   plutil -p ~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist
   ```

3. エラーログを確認
   ```bash
   tail -f /Users/hal1956/development/PRISM/logs/daily_reflection_err.log
   ```

### 権限エラーの場合
```bash
# 実行権限を付与
chmod +x tools/daily_reflection.py
```

### 環境変数エラーの場合
- `.env`ファイルの設定を確認
- launchd設定の環境変数を確認

## 関連ファイル

- `tools/daily_reflection.py`: メインスクリプト
- `tools/setup_daily_reflection.sh`: 自動実行設定スクリプト
- `tools/test_daily_reflection.sh`: テスト実行スクリプト
- `~/Library/LaunchAgents/com.hovix.prism.daily-reflection.plist`: launchd設定ファイル

