# 毎朝のタスク整理機能

## 概要

毎朝8:00に自動実行されるタスク整理機能です。Notionの各データベースから今日のタスクを取得し、整理して表示します。また、日替わりの名言も表示されます。

## 機能

### 📋 タスク整理
- **Task**: 期日が今日または未設定のタスク
- **ToDo**: 実施日が今日または未設定のToDo
- **Project**: 終了予定日が今日または未設定のプロジェクト
- **Habit**: 実行日が今日または未設定の習慣
- **Knowledge**: 登録日が今日または未設定の知識
- **Note**: 日付が今日または未設定のメモ

### 🎯 タスク分類
- **🚨 緊急・高優先度**: 重要度が「高」「緊急」のタスク
- **📅 今日期限**: 今日が期限のタスク
- **🔄 進行中**: ステータスが「進行中」のタスク
- **🔄 習慣**: 習慣データベースのタスク
- **📁 プロジェクト**: プロジェクトデータベースのタスク
- **📝 未着手**: その他のタスク

### 💭 今日の一言
- 日付に基づいて同じ名言を選ぶ
- 30種類の名言からランダム選択
- 毎日異なる名言が表示される
- **著作者名と出典元を併記**

#### 名言の種類
- **松下幸之助**: パナソニック創業者の名言
- **稲盛和夫**: 京セラ・KDDI創業者の名言
- **ビジネス界の著名人**: スティーブ・ジョブズ、ウォルト・ディズニー、トーマス・エジソンなど
- **禅語**: 一期一会、無心、平常心など
- **古典**: 聖徳太子の十七条憲法など
- **ビジネス書**: デール・カーネギー、ナポレオン・ヒル、スティーブン・コヴィーなど

## 設定

### 自動実行設定
```bash
# 設定ファイル
~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist

# 実行時刻
毎朝8:00

# 実行内容
python3 tools/daily_task_summary.py
```

### ログファイル
- **標準出力**: `/Users/hal1956/development/PRISM/logs/daily_summary_out.log`
- **エラー出力**: `/Users/hal1956/development/PRISM/logs/daily_summary_err.log`

## 使用方法

### 手動実行
```bash
cd /Users/hal1956/development/PRISM
python3 tools/daily_task_summary.py
```

### 自動実行設定
```bash
# 設定
bash tools/setup_daily_summary.sh

# テスト実行（1分後）
bash tools/test_daily_summary.sh
```

### 管理コマンド
```bash
# サービス状態確認
launchctl list | grep daily-summary

# 設定確認
plutil -p ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist

# ログ監視
tail -f /Users/hal1956/development/PRISM/logs/daily_summary_out.log

# サービス停止
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist

# サービス開始
launchctl load ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
```

## 実行時刻変更

### 時刻変更
```bash
# 8:00に設定
plutil -replace StartCalendarInterval.Hour -integer 8 ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
plutil -replace StartCalendarInterval.Minute -integer 0 ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist

# サービス再読み込み
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
launchctl load ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
```

### カスタム時刻設定
```bash
# 例: 7:30に設定
plutil -replace StartCalendarInterval.Hour -integer 7 ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
plutil -replace StartCalendarInterval.Minute -integer 30 ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
```

## 出力例

```
🌅 おはようございます！
============================================================
📅 日付: 2025年10月23日 (Thursday)
⏰ 時刻: 08:00

📋 タスクを取得中...
📋 今日のタスク整理
==================================================
📊 総タスク数: 7件

📅 今日期限 (7件)
  • 毎日30分の英語学習 (Habit)
  • 毎朝のチーム朝会 (Habit)
  • 週3回のジム通い (Habit)
  • AWSのセキュリティ設定について学ぶ (Knowledge)
  • データベース設計のベストプラクティス (Knowledge)
  • 今日学んだこと: TypeScriptのジェネリクス (Knowledge)
  • 読書メモ: エンジニアリング組織論への招待 (Note)

💭 今日の一言
==================================================
「困難は成長の機会である。」
— 松下幸之助 (パナソニック創業者)

✨ 今日も素晴らしい一日をお過ごしください！
============================================================
```

## 名言一覧

### 松下幸之助（パナソニック創業者）
- 「困難は成長の機会である。」
- 「継続は力なり。」
- 「感謝の気持ちを忘れずに。」
- 「努力は必ず報われる。」
- 「今日の積み重ねが明日を作る。」
- 「今日も成長の一日にしよう。」

### 稲盛和夫（京セラ・KDDI創業者）
- 「今日も新しい学びがある。」
- 「チャレンジこそが人生を豊かにする。」
- 「今日も素晴らしい一日にしよう。」
- 「可能性は無限大。」

### ビジネス界の著名人
- **スティーブ・ジョブズ**: 「目標に向かって一歩ずつ進もう。」「時間は最も貴重な資源である。」
- **ウォルト・ディズニー**: 「夢は行動によって現実になる。」
- **トーマス・エジソン**: 「失敗は成功の母。」
- **デール・カーネギー**: 「成功への道は、失敗を恐れないことから始まる。」「人を動かす」
- **ナポレオン・ヒル**: 「ポジティブな思考がポジティブな結果を生む。」「思考は現実化する」

### 禅語
- 「一期一会」（茶道の精神）
- 「無心」（禅の教え）
- 「平常心」（禅の教え）
- 「一石二鳥」（禅の教え）
- 「今日という日を大切に。」（一日一生）

### 古典・歴史
- **聖徳太子**: 「和を以て貴しとなす」（十七条憲法）
- **ベンジャミン・フランクリン**: 「今日できることを明日に延ばすな。」
- **マハトマ・ガンディー**: 「小さな一歩が大きな変化をもたらす。」
- **エレノア・ルーズベルト**: 「今日という日は、昨日死んだ人が生きたいと願った明日だ。」

### ビジネス書
- **スティーブン・コヴィー**: 「7つの習慣」
- **ジョン・マクスウェル**: 「リーダーシップ」
- **クレイトン・クリステンセン**: 「イノベーション」

---

## トラブルシューティング

### 実行されない場合
1. サービス状態を確認
   ```bash
   launchctl list | grep daily-summary
   ```

2. 設定ファイルを確認
   ```bash
   plutil -p ~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist
   ```

3. エラーログを確認
   ```bash
   tail -f /Users/hal1956/development/PRISM/logs/daily_summary_err.log
   ```

### 権限エラーの場合
```bash
# 実行権限を付与
chmod +x tools/daily_task_summary.py
```

### 環境変数エラーの場合
- `.env`ファイルの設定を確認
- launchd設定の環境変数を確認

## 関連ファイル

- `tools/daily_task_summary.py`: メインスクリプト
- `tools/setup_daily_summary.sh`: 自動実行設定スクリプト
- `tools/test_daily_summary.sh`: テスト実行スクリプト
- `~/Library/LaunchAgents/com.hovix.prism.daily-summary.plist`: launchd設定ファイル
