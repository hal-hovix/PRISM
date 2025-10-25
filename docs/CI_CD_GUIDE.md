# CI/CD パイプライン ガイド

## 概要

PRISMシステムのCI/CDパイプラインは、GitHub Actionsを使用して自動化された継続的インテグレーション・継続的デプロイメントを提供します。

## パイプライン構成

### 1. CI/CD Pipeline (`ci-cd.yml`)

**トリガー:**
- `main` ブランチへのプッシュ
- `develop` ブランチへのプッシュ
- プルリクエスト（`main` ブランチ向け）
- 手動実行

**ジョブ:**
1. **Code Quality Check** - コード品質チェック
   - Black（コードフォーマット）
   - isort（インポートソート）
   - flake8（リンティング）
   - mypy（型チェック）
   - bandit（セキュリティチェック）
   - safety（依存関係セキュリティチェック）

2. **Run Tests** - テスト実行
   - 単体テスト
   - 統合テスト
   - 非同期テスト
   - カバレッジレポート生成

3. **Build Docker Images** - Dockerイメージビルド
   - API、Web、Worker、MCPサービスのイメージビルド
   - GitHub Container Registryへのプッシュ

4. **Deployment Test** - デプロイメントテスト
   - テスト環境での動作確認
   - ヘルスチェック
   - スモークテスト

5. **Security Scan** - セキュリティスキャン
   - Trivyによる脆弱性スキャン
   - SARIFレポート生成

6. **Performance Test** - パフォーマンステスト
   - 負荷テスト
   - パフォーマンスレポート生成

### 2. Release Pipeline (`release.yml`)

**トリガー:**
- バージョンタグのプッシュ（`v*`）
- 手動実行

**ジョブ:**
1. **Prepare Release** - リリース準備
   - バージョン抽出・検証
   - リリース情報の準備

2. **Release Quality Check** - リリース品質チェック
   - 包括的なテスト実行
   - テストレポート生成

3. **Build and Push** - イメージビルド・プッシュ
   - リリース用Dockerイメージのビルド
   - レジストリへのプッシュ

4. **Generate Release Notes** - リリースノート生成
   - 変更履歴の自動生成
   - リリースノート作成

5. **Create GitHub Release** - GitHubリリース作成
   - リリースノート付きでGitHubリリース作成

### 3. Deployment Pipeline (`deploy.yml`)

**トリガー:**
- リリースパイプライン完了時
- 手動実行

**ジョブ:**
1. **Prepare Deployment** - デプロイメント準備
   - 環境・バージョン設定
   - デプロイメント検証

2. **Deploy to Staging** - ステージング環境デプロイ
   - ステージング環境へのデプロイ
   - ヘルスチェック・テスト

3. **Deploy to Production** - 本番環境デプロイ
   - 本番環境へのデプロイ
   - ヘルスチェック・テスト

4. **Rollback** - ロールバック機能
   - デプロイメント失敗時の自動ロールバック

## 使用方法

### 1. 基本的な開発フロー

```bash
# 1. 機能ブランチで開発
git checkout -b feature/new-feature
# ... 開発作業 ...

# 2. プルリクエスト作成
git push origin feature/new-feature
# GitHubでプルリクエスト作成

# 3. CI/CDパイプラインが自動実行
# - コード品質チェック
# - テスト実行
# - Dockerイメージビルド
```

### 2. リリース作成

```bash
# 1. バージョンタグを作成
git tag v1.0.0
git push origin v1.0.0

# 2. リリースパイプラインが自動実行
# - リリース品質チェック
# - Dockerイメージビルド・プッシュ
# - GitHubリリース作成
```

### 3. 手動デプロイメント

```bash
# GitHub Actionsの手動実行を使用
# または、ローカルでデプロイスクリプト実行

# ステージング環境
./tools/deploy.sh staging v1.0.0

# 本番環境
./tools/deploy.sh production v1.0.0
```

## 環境設定

### 1. GitHub Secrets

以下のシークレットをGitHubリポジトリに設定してください：

```
API_KEY=your-secure-api-key
OPENAI_API_KEY=sk-your-openai-key
NOTION_API_KEY=your_notion_api_key_here-notion-key
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
REDIS_PASSWORD=your-redis-password
GRAFANA_PASSWORD=your-grafana-password
```

### 2. 環境変数ファイル

**開発環境:** `.env`
**ステージング環境:** `.env.staging`
**本番環境:** `.env.production`

```bash
# 本番環境用の設定例
cp env.production.example .env.production
# 必要な値を設定
```

### 3. Docker Compose ファイル

- **開発環境:** `docker-compose.yml`
- **ステージング環境:** `docker-compose.staging.yml`
- **本番環境:** `docker-compose.production.yml`

## 監視とログ

### 1. GitHub Actions ログ

- 各パイプラインの実行ログはGitHub Actionsで確認可能
- 失敗時の詳細なエラー情報を提供

### 2. アプリケーション監視

**本番環境:**
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000
- **API メトリクス:** http://localhost:8060/metrics

### 3. ログ確認

```bash
# 全サービスのログ
docker-compose -f docker-compose.production.yml logs -f

# 特定サービスのログ
docker-compose -f docker-compose.production.yml logs -f PRISM-API
```

## トラブルシューティング

### 1. パイプライン失敗時の対処

```bash
# 1. ログを確認
# GitHub Actions のログを確認

# 2. ローカルでテスト
python tools/run_tests.py --all

# 3. 手動でデプロイメントテスト
docker-compose -f docker-compose.test.yml up -d
```

### 2. デプロイメント失敗時の対処

```bash
# 1. ロールバック
docker-compose -f docker-compose.production.yml down
# 前のバージョンに戻す

# 2. ヘルスチェック
curl -f http://localhost:8060/healthz

# 3. ログ確認
docker-compose -f docker-compose.production.yml logs
```

### 3. よくある問題

**問題:** Dockerイメージビルド失敗
**解決:** Dockerfileの構文エラーを確認

**問題:** テスト失敗
**解決:** 依存関係の更新、テストデータの確認

**問題:** デプロイメント失敗
**解決:** 環境変数の設定確認、ポート競合の確認

## ベストプラクティス

### 1. ブランチ戦略

- `main`: 本番環境用
- `develop`: 開発環境用
- `feature/*`: 機能開発用
- `hotfix/*`: 緊急修正用

### 2. コミットメッセージ

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードフォーマット
refactor: リファクタリング
test: テスト追加
chore: その他の変更
```

### 3. バージョニング

- **メジャー:** 破壊的変更
- **マイナー:** 新機能追加
- **パッチ:** バグ修正

例: `v1.2.3`

### 4. セキュリティ

- シークレットの適切な管理
- 定期的な依存関係の更新
- セキュリティスキャンの実行

## 参考資料

- [GitHub Actions ドキュメント](https://docs.github.com/ja/actions)
- [Docker Compose ドキュメント](https://docs.docker.com/compose/)
- [Prometheus ドキュメント](https://prometheus.io/docs/)
- [Grafana ドキュメント](https://grafana.com/docs/)
