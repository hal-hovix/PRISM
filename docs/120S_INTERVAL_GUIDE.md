# PRISM 120秒間隔自動仕分け クイックリファレンス

## ⏰ 120秒間隔設定完了

**実行間隔**: 120秒（2分おき）  
**設定方法**: launchd（macOS推奨）  
**ステータス**: ✅ 実行中

---

## 🚀 設定方法（3つのオプション）

### 方法1: 120秒間隔専用設定（推奨）

```bash
cd /Users/hal1956/development/PRISM
bash tools/setup_120s_interval.sh
```

**特徴:**
- ✅ 120秒間隔に最適化
- ✅ シンプルな設定
- ✅ 専用ログファイル

### 方法2: 間隔変更スクリプト

```bash
cd /Users/hal1956/development/PRISM
bash tools/change_interval.sh
# → 「2」を選択（120秒間隔）
```

**特徴:**
- ✅ 他の間隔にも変更可能
- ✅ 動的な間隔変更
- ✅ 現在の設定確認

### 方法3: cron版（上級者向け）

```bash
cd /Users/hal1956/development/PRISM
bash tools/setup_auto_classify_interval.sh
# → 「1」を選択（120秒間隔）
```

---

## 📊 現在の設定確認

### サービス状態

```bash
# launchdサービス確認
launchctl list | grep prism

# 出力例:
# -	0	com.hovix.prism.classify.120s
```

### 設定ファイル

```bash
# 設定ファイルの場所
ls -l ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist

# 設定内容確認
plutil -p ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist
```

### ログ確認

```bash
# リアルタイムログ
tail -f /Users/hal1956/development/PRISM/logs/classify_120s_*.log

# 最新のログ
ls -lt /Users/hal1956/development/PRISM/logs/classify_120s_*
```

---

## 🔧 管理コマンド

### サービス制御

```bash
# 停止
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist

# 再開
launchctl load ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist

# 削除
launchctl unload ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist
rm ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist
```

### 手動実行

```bash
cd /Users/hal1956/development/PRISM
python3 tools/advanced_classify_inbox.py
```

### 間隔変更

```bash
# 他の間隔に変更
bash tools/change_interval.sh

# 選択肢:
# 1) 60秒間隔（1分おき）
# 2) 120秒間隔（2分おき）← 現在
# 3) 300秒間隔（5分おき）
# 4) 600秒間隔（10分おき）
# 5) 1800秒間隔（30分おき）
# 6) カスタム間隔
# 0) 停止
```

---

## 📈 実行頻度の比較

| 間隔 | 1時間あたり | 1日あたり | 用途 |
|------|------------|----------|------|
| 60秒 | 60回 | 1,440回 | 最高頻度（テスト用） |
| **120秒** | **30回** | **720回** | **高頻度（推奨）** |
| 300秒 | 12回 | 288回 | 中頻度 |
| 600秒 | 6回 | 144回 | 低頻度 |
| 1800秒 | 2回 | 48回 | 最低頻度 |

---

## ⚠️ 注意事項

### API レート制限

- **Notion API**: 3リクエスト/秒
- **OpenAI API**: 制限あり（プランによる）
- **120秒間隔**: 安全な間隔

### ログ管理

```bash
# 古いログを削除（30日以上前）
find /Users/hal1956/development/PRISM/logs -name "classify_120s_*.log" -mtime +30 -delete

# ログローテーション（cronで自動化）
0 0 * * 0 find /Users/hal1956/development/PRISM/logs -name "*.log" -mtime +30 -delete
```

### システム負荷

- **CPU使用率**: 低（2分に1回の短時間実行）
- **メモリ使用量**: 最小限
- **ディスク使用量**: ログファイルのみ

---

## 🎯 運用パターン

### パターン1: 常時実行

```bash
# 24時間365日実行
# 設定: 120秒間隔
# 用途: チーム共有、リアルタイム整理
```

### パターン2: 営業時間のみ

```bash
# 平日 9:00-18:00 のみ実行
# 設定: 120秒間隔 + 時間制限
# 用途: 個人利用、業務時間のみ
```

### パターン3: 動的調整

```bash
# 時間帯によって間隔を変更
# 朝: 120秒間隔（高頻度）
# 夜: 600秒間隔（低頻度）
# 用途: 効率的な運用
```

---

## 🔍 トラブルシューティング

### ❌ 実行されない

```bash
# 1. サービス状態確認
launchctl list | grep prism

# 2. ログ確認
tail -f /Users/hal1956/development/PRISM/logs/classify_120s_err.log

# 3. 手動実行テスト
cd /Users/hal1956/development/PRISM
python3 tools/advanced_classify_inbox.py

# 4. 設定ファイル確認
plutil -lint ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist
```

### ❌ エラーが発生

```bash
# エラーログを確認
grep -i error /Users/hal1956/development/PRISM/logs/classify_120s_*.log

# よくあるエラー:
# - API_KEY エラー → .env ファイルを確認
# - Permission denied → ファイル権限を確認
# - Python not found → python3 のパスを確認
```

### ❌ 間隔が正しくない

```bash
# 設定を再確認
plutil -extract StartInterval raw ~/Library/LaunchAgents/com.hovix.prism.classify.120s.plist

# 再設定
bash tools/change_interval.sh
```

---

## 📚 関連ファイル

| ファイル | 用途 |
|---------|------|
| `tools/setup_120s_interval.sh` | 120秒間隔専用設定 |
| `tools/change_interval.sh` | 間隔変更スクリプト |
| `tools/setup_auto_classify_interval.sh` | cron版設定 |
| `tools/advanced_classify_inbox.py` | 仕分け実行スクリプト |
| `docs/AUTOMATION_GUIDE.md` | 詳細ガイド |

---

## 🎉 まとめ

### ✅ 120秒間隔設定完了

- **実行間隔**: 120秒（2分おき）
- **設定方法**: launchd
- **ログファイル**: `classify_120s_*.log`
- **管理**: `bash tools/change_interval.sh`

### 🚀 次のステップ

1. **動作確認**: 数時間様子を見る
2. **ログ確認**: エラーがないかチェック
3. **間隔調整**: 必要に応じて変更
4. **運用開始**: 本格運用

**120秒間隔で、INBOXが常に整理された状態を維持できます！** ⏰✨

---

**設定日**: 2025年10月23日  
**間隔**: 120秒（2分）  
**ステータス**: ✅ 実行中

