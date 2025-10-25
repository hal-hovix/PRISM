# PRISM 自動仕分け クイックスタート

## 🎯 自動仕分けのタイミング（結論）

### 💡 おすすめ: **毎朝9時に1回**

```bash
# これだけでOK！
cd /Users/hal1956/development/PRISM
bash tools/setup_auto_classify.sh
# → 「1」を選択
```

---

## ⏰ いつ仕分けするべき？

### 推奨される3つのパターン

#### 1️⃣ 朝型（初心者向け・推奨）✨
```
実行: 毎朝 9:00
メリット: 1日の始まりにINBOXをクリア
```
**こんな人におすすめ:**
- 朝にタスクを確認する習慣がある
- 計画的に1日を始めたい

#### 2️⃣ 朝夕型（標準）
```
実行: 毎朝 9:00 と 毎晩 21:00
メリット: 朝と夜に整理、常に最新状態
```
**こんな人におすすめ:**
- 1日に複数回Notionを確認する
- リアルタイムに近い状態を保ちたい

#### 3️⃣ 高頻度型（パワーユーザー）
```
実行: 2時間おき
メリット: ほぼリアルタイム、INBOXが常に空
```
**こんな人におすすめ:**
- 1日に10件以上INBOXに追加する
- チームで共有している

---

## 🚀 5分でセットアップ

### 方法1: 自動セットアップ（推奨）

```bash
# ステップ1: セットアップスクリプトを実行
cd /Users/hal1956/development/PRISM
bash tools/setup_auto_classify.sh

# ステップ2: タイミングを選択
# 1 を選択（毎朝9時）

# ステップ3: 完了！
```

### 方法2: 手動セットアップ

```bash
# cronを編集
crontab -e

# 以下を追加（毎朝9時）
0 9 * * * cd /Users/hal1956/development/PRISM && python3 tools/advanced_classify_inbox.py >> logs/classify.log 2>&1

# 保存して終了（vi: :wq）
```

---

## 📋 よくある実行タイミング

| パターン | cron設定 | 説明 |
|---------|---------|------|
| **毎朝9時** | `0 9 * * *` | 1日1回、朝に整理 |
| **朝夕2回** | `0 9,21 * * *` | 朝9時と夜21時 |
| **2時間おき** | `0 */2 * * *` | 営業時間中ずっと |
| **平日のみ** | `0 9 * * 1-5` | 月〜金の朝9時 |
| **週次** | `0 9 * * 1` | 毎週月曜9時 |

---

## 🖐️ 手動実行

### 今すぐ仕分けする

```bash
cd /Users/hal1956/development/PRISM
python3 tools/advanced_classify_inbox.py
```

### INBOXの状態を確認

```bash
python3 tools/verify_classification_results.py
```

---

## 🔍 確認方法

### 自動実行が設定されているか確認

```bash
# cron設定を確認
crontab -l | grep PRISM

# 出力例:
# 0 9 * * * cd /Users/hal1956/development/PRISM && python3 tools/advanced_classify_inbox.py ...
```

### ログを確認

```bash
# リアルタイムでログを表示
tail -f /Users/hal1956/development/PRISM/logs/classify_*.log

# 最新のログを確認
ls -lt /Users/hal1956/development/PRISM/logs/
```

---

## ⚙️ cron時刻の書き方

```
分  時  日  月  曜日  コマンド
*   *   *   *   *    ...
```

### よく使う例

```bash
# 毎日 9:00
0 9 * * *

# 毎日 9:00, 12:00, 21:00
0 9,12,21 * * *

# 2時間おき（9時〜18時）
0 9-18/2 * * *

# 平日のみ 9:00
0 9 * * 1-5

# 毎週月曜 9:00
0 9 * * 1

# 月初（1日）9:00
0 9 1 * *
```

---

## 🛠️ トラブルシューティング

### ❌ 自動実行されない

```bash
# 1. cronが動いているか確認
ps aux | grep cron

# 2. 手動で実行できるか確認
cd /Users/hal1956/development/PRISM
python3 tools/advanced_classify_inbox.py

# 3. ログディレクトリが存在するか確認
mkdir -p /Users/hal1956/development/PRISM/logs

# 4. cronを再登録
crontab -e  # 設定を確認・修正
```

### ❌ エラーが出る

```bash
# エラーログを確認
cat /Users/hal1956/development/PRISM/logs/classify_*.log | grep -i error

# よくあるエラー:
# - API_KEY エラー → .env ファイルを確認
# - Python not found → python3 のパスを確認（which python3）
# - Permission denied → スクリプトに実行権限を付与（chmod +x）
```

---

## 📊 実行頻度の目安

| INBOXへの追加頻度 | 推奨実行タイミング |
|-----------------|-----------------|
| **1日1〜5件** | 毎朝1回 |
| **1日5〜10件** | 朝夕2回 |
| **1日10〜20件** | 3〜4回/日 |
| **1日20件以上** | 2時間おき |

---

## 🎯 実際の使い方

### シナリオ1: 個人利用

```bash
# 設定: 毎朝9時に1回
0 9 * * * cd /Users/hal1956/development/PRISM && python3 tools/advanced_classify_inbox.py

# 運用:
# - 思いついたらINBOXに追加
# - 翌朝には自動的に整理される
# - Task/ToDo/Projectから作業開始
```

### シナリオ2: チーム利用

```bash
# 設定: 2時間おき（営業時間中）
0 9-18/2 * * 1-5 cd /Users/hal1956/development/PRISM && python3 tools/advanced_classify_inbox.py

# 運用:
# - チームメンバーがINBOXに追加
# - 2時間以内に自動整理
# - 常に最新の状態を共有
```

### シナリオ3: 週次レビュー派

```bash
# 設定: 毎週月曜9時
0 9 * * 1 cd /Users/hal1956/development/PRISM && python3 tools/advanced_classify_inbox.py

# 運用:
# - 週の途中はINBOXに溜める
# - 月曜朝に一括整理
# - 週次レビューと連動
```

---

## 📚 詳細ドキュメント

より詳しい情報は以下を参照：

- **詳細ガイド**: `docs/AUTOMATION_GUIDE.md`
- **セットアップスクリプト**: `tools/setup_auto_classify.sh`
- **手動実行**: `tools/advanced_classify_inbox.py`

---

## 💡 ワンポイントアドバイス

### ✅ DO（推奨）

- ✅ まずは「毎朝1回」から始める
- ✅ ログを定期的に確認する
- ✅ 自分の使い方に合わせて調整する

### ❌ DON'T（非推奨）

- ❌ 最初から高頻度にしない（様子を見る）
- ❌ ログを無限に溜めない（定期削除）
- ❌ エラーを放置しない（早めに対処）

---

## 🎉 まとめ

### 最もシンプルな設定（これだけでOK！）

```bash
# ステップ1: セットアップ実行
cd /Users/hal1956/development/PRISM
bash tools/setup_auto_classify.sh

# ステップ2: 「1」を選択（毎朝9時）

# ステップ3: 完了！あとは毎朝自動で整理されます
```

**これで、毎朝9時に自動的にINBOXが整理されます！** 🚀

---

**作成日**: 2025年10月22日  
**バージョン**: 1.0  
**推奨**: 毎朝9時に1回実行

