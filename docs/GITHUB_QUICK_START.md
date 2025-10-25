# GitHub クイックスタートガイド

## 🚀 PRISMプロジェクト用 GitHub設定

### ✅ SSH鍵の確認

**使用するSSH鍵:**
- 秘密鍵: `~/.ssh/id_ed25519`
- 公開鍵: `~/.ssh/id_ed25519.pub`
- GitHubユーザー: `hal-hovix`

> **注意**: SSH接続テストで表示されるユーザー名（`haloniki-boop`）と、実際のGitHubユーザー名（`hal-hovix`）が異なる場合があります。リポジトリURLには実際のGitHubユーザー名を使用してください。

### 📋 初回セットアップ（3ステップ）

#### 1️⃣ GitHubリポジトリの作成

```bash
# ブラウザで以下にアクセス
https://github.com/new

# 設定:
# - Repository name: PRISM
# - Visibility: Private（または Public）
# - ❌ README, .gitignore, license は追加しない
```

#### 2️⃣ 公開鍵をGitHubに登録

```bash
# 公開鍵を表示してコピー
cat ~/.ssh/id_ed25519.pub
```

出力（この鍵を使用）:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICPzqQkhO0b01DHBaXYBOn7dRcCndJq1qBsPssstH7ZT hal@hovix.jp
```

```bash
# ブラウザで以下にアクセス
https://github.com/settings/keys

# New SSH key をクリック
# - Title: PRISM Development Key
# - Key type: Authentication Key
# - Key: 上記の公開鍵を貼り付け
# → Add SSH key

# 接続テスト
ssh -T git@github.com
# 成功メッセージ: Hi hal-hovix! You've successfully authenticated...
```

#### 3️⃣ リポジトリをプッシュ

```bash
cd /Users/hal1956/development/PRISM

# リモートリポジトリを追加（SSH URL）
git remote add origin git@github.com:hal-hovix/PRISM.git

# 確認
git remote -v

# ブランチ名を確認（mainにする）
git branch -M main

# プッシュ
git push -u origin main
```

---

## 🔧 日常的なGit操作

### 変更のコミットとプッシュ

```bash
# 変更状況を確認
git status

# 全ての変更をステージング
git add .

# コミット
git commit -m "feat: 新機能を追加"

# プッシュ
git push origin main
```

### 最新の変更を取得

```bash
# リモートから最新を取得
git pull origin main
```

### ブランチ操作

```bash
# 新しいブランチを作成して切り替え
git checkout -b feature/new-feature

# 変更をコミット
git add .
git commit -m "feat: Add new feature"

# プッシュ
git push -u origin feature/new-feature

# mainブランチに戻る
git checkout main
```

---

## 📝 コミットメッセージの書き方

### 推奨フォーマット

```
<type>: <subject>

<body>
```

### Type の種類

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: 雑務（ビルド、設定など）

### 例

```bash
git commit -m "feat: INBOX自動仕分け機能を追加"

git commit -m "fix: 分類APIの認証エラーを修正"

git commit -m "docs: GitHub設定手順書を更新"
```

---

## ⚙️ SSH設定の確認

### SSH Agentの起動と鍵の追加

```bash
# SSH Agentを起動
eval "$(ssh-agent -s)"

# 鍵を追加
ssh-add ~/.ssh/id_ed25519

# 登録済み鍵の確認
ssh-add -l
```

### SSH設定ファイル（オプション）

`~/.ssh/config` に以下を追加すると便利：

```bash
cat >> ~/.ssh/config << 'EOF'

# GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    AddKeysToAgent yes
    UseKeychain yes
EOF

# パーミッションを設定
chmod 600 ~/.ssh/config
```

---

## 🔍 トラブルシューティング

### SSH接続エラー

```bash
# 接続テスト
ssh -T git@github.com

# 詳細ログで確認
ssh -vT git@github.com

# 鍵のパーミッション確認
ls -l ~/.ssh/id_ed25519*
# 秘密鍵は 600 (-rw-------)
# 公開鍵は 644 (-rw-r--r--)

# パーミッション修正
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

### プッシュが拒否される

```bash
# リモートの変更を取得
git pull origin main --rebase

# 競合を解決後
git add .
git rebase --continue

# プッシュ
git push origin main
```

### リモートURLの確認・変更

```bash
# 現在のリモートURL確認
git remote -v

# HTTPSからSSHに変更
git remote set-url origin git@github.com:hal-hovix/PRISM.git

# 確認
git remote -v
```

---

## 📊 現在のGit状態確認

```bash
# ブランチ確認
git branch -a

# コミット履歴
git log --oneline -10

# 未コミットの変更
git status

# リモート情報
git remote -v

# 最新のコミット
git show HEAD
```

---

## 🎯 よく使うコマンド一覧

| コマンド | 説明 |
|---------|------|
| `git status` | 変更状況の確認 |
| `git add .` | 全ての変更をステージング |
| `git commit -m "message"` | コミット |
| `git push origin main` | プッシュ |
| `git pull origin main` | プル |
| `git log --oneline` | コミット履歴 |
| `git branch` | ブランチ一覧 |
| `git checkout -b name` | 新ブランチ作成＆切替 |
| `git remote -v` | リモート確認 |
| `ssh -T git@github.com` | SSH接続テスト |

---

## 🔗 リンク集

- **GitHubリポジトリ**: `https://github.com/hal-hovix/PRISM`
- **SSH設定**: `https://github.com/settings/keys`
- **詳細ガイド**: `docs/GITHUB_GUIDE.md`
- **GitHub Docs**: `https://docs.github.com/`

---

## 📌 重要な注意事項

### ⚠️ 絶対にコミットしてはいけないもの

- ✗ `.env` ファイル
- ✗ APIキー・トークン
- ✗ SSH秘密鍵（`id_ed25519`）
- ✗ パスワード

### ✅ 安全な開発のために

1. `.gitignore` を確認
2. コミット前に `git status` で確認
3. 秘密情報は環境変数で管理
4. 定期的にバックアップ

---

**作成日**: 2025年10月22日  
**バージョン**: 1.0  
**対象**: PRISM プロジェクト

