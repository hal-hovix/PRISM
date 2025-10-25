# GitHub セットアップ手順書

## 📚 目次

1. [GitHubリポジトリの作成](#1-githubリポジトリの作成)
2. [ローカルリポジトリの設定](#2-ローカルリポジトリの設定)
3. [初回プッシュ](#3-初回プッシュ)
4. [ブランチ戦略](#4-ブランチ戦略)
5. [プルリクエストの作成](#5-プルリクエストの作成)
6. [よくある問題と対処法](#6-よくある問題と対処法)

---

## 1. GitHubリポジトリの作成

### 1.1 新規リポジトリの作成

1. GitHubにログイン: https://github.com
2. 右上の `+` ボタンをクリック → `New repository` を選択
3. リポジトリ情報を入力:
   - **Repository name**: `PRISM`
   - **Description**: `分類・問い合わせ可能なToDo/習慣/知識ベース`
   - **Visibility**: 
     - Public (公開) または Private (非公開) を選択
   - **Initialize this repository with**:
     - ✅ **チェックを入れない** (既存のローカルリポジトリがあるため)
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license

4. `Create repository` をクリック

### 1.2 リポジトリURLの確認

作成後、以下のようなURLが表示されます：

```
https://github.com/YOUR_USERNAME/PRISM.git
```

このURLを控えておきます。

> **PRISM プロジェクトの場合**: `https://github.com/hal-hovix/PRISM.git`

---

## 2. ローカルリポジトリの設定

### 2.1 現在の状態を確認

```bash
cd /Users/hal1956/development/PRISM
git status
```

### 2.2 .gitignoreの作成（未作成の場合）

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# Environment
.env
*.env
!env.example

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Docker
docker-compose.override.yml

# Keys & Secrets
*.pem
*.key
*.pub
195603
195603.pub

# Test outputs
.pytest_cache/
.coverage
htmlcov/

# Temporary files
*.tmp
*.bak
EOF
```

### 2.3 不要なファイルを削除

SSH鍵ファイルが誤って追跡されている場合は削除します：

```bash
# ステージングから削除（ファイルは残す）
git restore --staged 195603 195603.pub

# ファイル自体も削除（必要に応じて）
rm -f 195603 195603.pub

# .gitignoreに追加済みなので今後は追跡されません
```

### 2.4 変更をコミット

```bash
# 全ての変更をステージング
git add .

# コミット
git commit -m "feat: Initial commit - PRISM v1.0.0

- FastAPI ベースの分類・検索API
- Docker Compose による3サービス構成
- プラグイン式分類システム
- Web UI インターフェース
- 包括的なドキュメント
- テストスイート完備"
```

---

## 3. 初回プッシュ

### 3.1 リモートリポジトリの追加

```bash
# GitHubリポジトリをリモートとして追加
git remote add origin https://github.com/YOUR_USERNAME/PRISM.git
# PRISM プロジェクトの場合: git remote add origin git@github.com:hal-hovix/PRISM.git

# 確認
git remote -v
```

### 3.2 ブランチ名の確認・変更（必要に応じて）

```bash
# 現在のブランチ名を確認
git branch

# mainブランチでない場合は変更
git branch -M main
```

### 3.3 プッシュ

```bash
# 初回プッシュ（upstream設定付き）
git push -u origin main
```

認証方法：

#### Option A: Personal Access Token (推奨)

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. `Generate new token` をクリック
3. スコープ: `repo` にチェック
4. トークンをコピー
5. プッシュ時にパスワードの代わりに使用

#### Option B: SSH Key（推奨）

PRISMプロジェクトでは以下のSSH鍵を使用します：

**鍵ファイル:**
- 秘密鍵: `~/.ssh/id_ed25519`
- 公開鍵: `~/.ssh/id_ed25519.pub`

**設定手順:**

```bash
# 1. 公開鍵の内容を確認・コピー
cat ~/.ssh/id_ed25519.pub
```

出力例：
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICPzqQkhO0b01DHBaXYBOn7dRcCndJq1qBsPssstH7ZT hal@hovix.jp
```

```bash
# 2. GitHubに公開鍵を登録
# GitHub → Settings → SSH and GPG keys → New SSH key
# - Title: PRISM Development Key (任意の名前)
# - Key type: Authentication Key
# - Key: 上記の公開鍵の内容を貼り付け
# → Add SSH key をクリック

# 3. SSH接続をテスト
ssh -T git@github.com
# 成功すると以下のメッセージが表示されます：
# Hi YOUR_USERNAME! You've successfully authenticated, but GitHub does not provide shell access.
# PRISM プロジェクトの場合: Hi haloniki-boop! ... (GitHubユーザー名: hal-hovix)

# 4. リモートURLをSSHに変更
git remote set-url origin git@github.com:YOUR_USERNAME/PRISM.git
# PRISM プロジェクトの場合: git remote set-url origin git@github.com:hal-hovix/PRISM.git

# 5. 確認
git remote -v
# 出力例：
# origin  git@github.com:YOUR_USERNAME/PRISM.git (fetch)
# origin  git@github.com:YOUR_USERNAME/PRISM.git (push)
# PRISM プロジェクトの場合: git@github.com:hal-hovix/PRISM.git

# 6. プッシュ
git push -u origin main
```

**SSHキーが存在しない場合:**

```bash
# ED25519形式でSSH鍵を生成
ssh-keygen -t ed25519 -C "your_email@example.com"

# 保存場所を聞かれたら Enter (デフォルト: ~/.ssh/id_ed25519)
# パスフレーズを入力（推奨）または空でEnter

# SSH agentに鍵を追加
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

---

## 4. ブランチ戦略

### 4.1 推奨ブランチ構成

```
main        - 本番環境用の安定版
├── develop - 開発統合ブランチ
├── feature/* - 機能開発ブランチ
├── bugfix/*  - バグ修正ブランチ
└── hotfix/*  - 緊急修正ブランチ
```

### 4.2 開発フロー

#### 新機能の開発

```bash
# developブランチから新機能ブランチを作成
git checkout -b develop
git push -u origin develop

git checkout -b feature/new-classifier develop

# 開発作業...
git add .
git commit -m "feat: Add new classifier plugin"

# プッシュ
git push -u origin feature/new-classifier
```

#### バグ修正

```bash
# バグ修正ブランチを作成
git checkout -b bugfix/fix-api-error develop

# 修正作業...
git add .
git commit -m "fix: Resolve API authentication error"

# プッシュ
git push -u origin bugfix/fix-api-error
```

#### 緊急修正（Hotfix）

```bash
# mainから直接ホットフィックスブランチを作成
git checkout -b hotfix/critical-security-fix main

# 修正作業...
git add .
git commit -m "fix: Critical security vulnerability patch"

# プッシュ
git push -u origin hotfix/critical-security-fix
```

### 4.3 コミットメッセージ規約

Conventional Commits 形式を推奨：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type の種類:**

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（フォーマット、セミコロン等）
- `refactor`: リファクタリング
- `perf`: パフォーマンス改善
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

**例:**

```bash
git commit -m "feat(classifier): Add sentiment analysis plugin

- Implement sentiment scoring
- Add emotion detection
- Update plugin registry

Closes #123"
```

---

## 5. プルリクエストの作成

### 5.1 GitHub上でPRを作成

1. GitHubのリポジトリページへアクセス
2. `Pull requests` タブをクリック
3. `New pull request` をクリック
4. ブランチを選択:
   - **base**: `develop` (マージ先)
   - **compare**: `feature/new-classifier` (マージ元)
5. タイトルと説明を記入
6. レビュアーを指定（チーム開発の場合）
7. `Create pull request` をクリック

### 5.2 PRテンプレート

`.github/pull_request_template.md` を作成:

```markdown
## 変更内容

<!-- この PR で何を変更したか簡潔に説明 -->

## 変更の種類

- [ ] 新機能 (feat)
- [ ] バグ修正 (fix)
- [ ] ドキュメント更新 (docs)
- [ ] リファクタリング (refactor)
- [ ] テスト追加 (test)

## テスト

<!-- どのようにテストしたか -->

- [ ] ローカルでテスト済み
- [ ] 自動テストを追加
- [ ] 既存のテストが全て通過

## チェックリスト

- [ ] コードレビューの準備ができている
- [ ] ドキュメントを更新した
- [ ] テストを追加/更新した
- [ ] Linterエラーがない

## 関連Issue

Closes #(issue番号)
```

### 5.3 PRのマージ

1. レビューが完了したら
2. `Merge pull request` をクリック
3. マージ方法を選択:
   - **Merge commit**: 全履歴を保持
   - **Squash and merge**: 1つのコミットにまとめる（推奨）
   - **Rebase and merge**: 線形な履歴を維持
4. `Confirm merge` をクリック
5. マージ後、ブランチを削除（オプション）

---

## 6. よくある問題と対処法

### 6.1 プッシュが拒否される

**エラー:**
```
! [rejected] main -> main (fetch first)
```

**対処法:**
```bash
# リモートの変更を取得してマージ
git pull origin main --rebase

# 競合がある場合は解決後
git add .
git rebase --continue

# プッシュ
git push origin main
```

### 6.2 間違ってコミットした

```bash
# 直前のコミットを取り消し（変更は保持）
git reset --soft HEAD^

# 直前のコミットを完全に取り消し
git reset --hard HEAD^

# リモートにプッシュ済みの場合（注意: 履歴書き換え）
git push origin main --force
```

### 6.3 大きなファイルをコミットしてしまった

```bash
# 履歴から完全削除（BFG Repo-Cleaner使用）
# https://rtyley.github.io/bfg-repo-cleaner/

# または git-filter-repo
pip install git-filter-repo
git filter-repo --path-glob '*.log' --invert-paths

# 強制プッシュ
git push origin main --force
```

### 6.4 ブランチ間の変更を移動

```bash
# 間違ったブランチで作業してしまった場合
git stash

# 正しいブランチに移動
git checkout correct-branch

# 変更を適用
git stash pop
```

### 6.5 マージ競合の解決

```bash
# マージを試みる
git merge feature-branch

# 競合が発生した場合
# 1. 競合ファイルを手動で編集
# 2. 競合マーカーを削除 (<<<<<<<, =======, >>>>>>>)

# 解決後
git add .
git commit -m "Merge feature-branch into main"
```

---

## 7. GitHub Actions (CI/CD)

### 7.1 基本的なワークフロー

`.github/workflows/ci.yml` を作成:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src
    
    - name: Lint
      run: |
        pip install flake8
        flake8 src/ --max-line-length=120

  docker:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker images
      run: |
        docker-compose build
    
    - name: Test Docker containers
      run: |
        docker-compose up -d
        sleep 10
        curl -f http://localhost:8060/healthz || exit 1
        docker-compose down
```

### 7.2 自動デプロイ

`.github/workflows/deploy.yml` を作成:

```yaml
name: Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      run: |
        # デプロイスクリプトを実行
        ./scripts/deploy.sh
```

---

## 8. セキュリティのベストプラクティス

### 8.1 シークレット管理

**絶対にコミットしてはいけないもの:**
- API キー
- パスワード
- 秘密鍵
- アクセストークン
- `.env` ファイル

**対処法:**

1. `.gitignore` に追加
2. GitHub Secrets を使用
3. 環境変数で管理
4. Vault などのシークレット管理ツールを使用

### 8.2 GitHub Secrets の設定

1. リポジトリ → Settings → Secrets and variables → Actions
2. `New repository secret` をクリック
3. シークレットを追加:
   - `OPENAI_API_KEY`
   - `NOTION_API_KEY`
   - `API_KEY`

### 8.3 ブランチ保護ルール

1. Settings → Branches → Add rule
2. `main` ブランチに以下を設定:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

---

## 9. チーム開発のワークフロー

### 9.1 日常的な開発フロー

```bash
# 1. 最新のdevelopを取得
git checkout develop
git pull origin develop

# 2. 機能ブランチを作成
git checkout -b feature/my-new-feature

# 3. 開発作業
# ... コード編集 ...

# 4. コミット
git add .
git commit -m "feat: Add my new feature"

# 5. developの最新変更を取り込む
git fetch origin
git rebase origin/develop

# 6. プッシュ
git push -u origin feature/my-new-feature

# 7. GitHub上でPR作成

# 8. レビュー後、マージ

# 9. ローカルのブランチを削除
git checkout develop
git pull origin develop
git branch -d feature/my-new-feature
```

### 9.2 リリースフロー

```bash
# 1. リリースブランチを作成
git checkout -b release/v1.1.0 develop

# 2. バージョン番号を更新
# README.md, setup.py, package.json など

# 3. コミット
git commit -am "chore: Bump version to v1.1.0"

# 4. mainにマージ
git checkout main
git merge --no-ff release/v1.1.0

# 5. タグを作成
git tag -a v1.1.0 -m "Release version 1.1.0"

# 6. developにもマージ
git checkout develop
git merge --no-ff release/v1.1.0

# 7. プッシュ
git push origin main develop --tags

# 8. リリースブランチを削除
git branch -d release/v1.1.0
```

---

## 10. 参考リンク

- [GitHub Docs](https://docs.github.com/)
- [Git Book](https://git-scm.com/book/ja/v2)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

---

## 修正履歴

- 2025-10-22 v1.0.0: 初版作成

EOF

