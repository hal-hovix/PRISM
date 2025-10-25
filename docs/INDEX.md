# 📚 PRISM ドキュメント索引

**バージョン**: 2.0.0  
**更新日**: 2025年1月27日

## 📋 ドキュメント一覧

すべてのドキュメントは `docs/` フォルダに格納されています。

## ✨ 新機能ドキュメント (v2.0.0)

### 🔒 セキュリティ・監視・テスト
| ドキュメント | 内容 | サイズ |
|------------|------|--------|
| **[CI_CD_GUIDE.md](./CI_CD_GUIDE.md)** | CI/CDパイプラインガイド | 12KB |
| **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** | テストスイートガイド | 8KB |
| **[MONITORING_GUIDE.md](./MONITORING_GUIDE.md)** | 監視・メトリクスガイド | 10KB |

---

### 🚀 クイックスタート（5分で始める）

| ドキュメント | 内容 | 所要時間 |
|------------|------|---------|
| **[README](../README.md)** | プロジェクト概要 | 3分 |
| **[GITHUB_QUICK_START.md](./GITHUB_QUICK_START.md)** | GitHub設定 | 5分 |
| **[AUTOMATION_QUICK_START.md](./AUTOMATION_QUICK_START.md)** | 自動仕分け設定 | 5分 |

---

### 📖 セットアップ・運用ガイド

| # | ドキュメント | 内容 | サイズ |
|---|------------|------|--------|
| 1 | **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** | 詳細なインストール手順 | 6.4KB |
| 2 | **[USER_MANUAL.md](./USER_MANUAL.md)** | 操作マニュアル | 9.9KB |
| 3 | **[REQUIREMENTS.md](./REQUIREMENTS.md)** | システム要件と仕様 | 8.8KB |
| 4 | **[DAILY_TASK_SUMMARY.md](./DAILY_TASK_SUMMARY.md)** | 毎朝のタスク整理機能 | 8.5KB |
| 5 | **[DAILY_REFLECTION.md](./DAILY_REFLECTION.md)** | 毎夕の振り返り機能 | 8.0KB |
| 6 | **[ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)** | 環境変数による設定管理 | 7.5KB |
| 7 | **[GOOGLE_CALENDAR_SYNC.md](./GOOGLE_CALENDAR_SYNC.md)** | GoogleカレンダーとNotionDBの同期 | 8.2KB |
| 8 | **[GOOGLE_TASKS_SYNC.md](./GOOGLE_TASKS_SYNC.md)** | Google TasksとNotionDBの同期 | 7.8KB |
| 9 | **[NOTION_MCP_SERVER.md](./NOTION_MCP_SERVER.md)** | ChatGPT連携用Notion MCPサーバー | 8.5KB |

---

### 🛠️ 開発者向けドキュメント

| # | ドキュメント | 内容 | サイズ |
|---|------------|------|--------|
| 1 | **[DESIGN.md](./DESIGN.md)** | アーキテクチャと設計 | 15KB |
| 2 | **[API_REFERENCE.md](./API_REFERENCE.md)** | API詳細仕様 (v2.0.0) | 16KB |
| 3 | **[PLUGIN_DEVELOPMENT.md](./PLUGIN_DEVELOPMENT.md)** | プラグイン開発ガイド | 15KB |
| 4 | **[CI_CD_GUIDE.md](./CI_CD_GUIDE.md)** | CI/CDパイプラインガイド | 12KB |
| 5 | **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** | テストスイートガイド | 8KB |
| 6 | **[MONITORING_GUIDE.md](./MONITORING_GUIDE.md)** | 監視・メトリクスガイド | 10KB |

---

### 🐙 GitHub・バージョン管理

| # | ドキュメント | 内容 | サイズ |
|---|------------|------|--------|
| 7 | **[GITHUB_QUICK_START.md](./GITHUB_QUICK_START.md)** | クイックスタート | 5.5KB |
| 8 | **[GITHUB_GUIDE.md](./GITHUB_GUIDE.md)** | 詳細ガイド（完全版） | 14KB |

**内容:**
- リポジトリ作成
- SSH鍵設定
- ブランチ戦略
- PR作成
- GitHub Actions
- チーム開発

---

### ⏰ 自動化・運用

| # | ドキュメント | 内容 | サイズ |
|---|------------|------|--------|
| 9 | **[AUTOMATION_QUICK_START.md](./AUTOMATION_QUICK_START.md)** | クイックスタート | 6.2KB |
| 10 | **[AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md)** | 詳細ガイド（完全版） | 12KB |

**内容:**
- 実行タイミング
- cron設定
- launchd設定
- 運用パターン
- トラブルシューティング

---

### 🧪 テスト・データ

| # | ドキュメント | 内容 | サイズ |
|---|------------|------|--------|
| 11 | **[TEST_DATA_README.md](./TEST_DATA_README.md)** | テストデータガイド | 8.0KB |

**内容:**
- テストデータの使い方
- インポート方法
- 検証方法

---

### 📑 その他

| # | ドキュメント | 内容 |
|---|------------|------|
| 12 | **[README.md](./README.md)** | ドキュメント一覧 |
| 13 | **[INDEX.md](./INDEX.md)** | このファイル |

---

## 🗂️ フォルダ構成

```
docs/
├── README.md                       # ドキュメント概要
├── INDEX.md                        # このファイル
│
├── SETUP_GUIDE.md                  # セットアップガイド
├── USER_MANUAL.md                  # ユーザーマニュアル
├── REQUIREMENTS.md                 # 要件定義
├── DAILY_TASK_SUMMARY.md           # 毎朝のタスク整理機能
├── DAILY_REFLECTION.md             # 毎夕の振り返り機能
├── ENVIRONMENT_VARIABLES.md         # 環境変数による設定管理
├── GOOGLE_CALENDAR_SYNC.md         # GoogleカレンダーとNotionDBの同期
├── GOOGLE_TASKS_SYNC.md            # Google TasksとNotionDBの同期
├── NOTION_MCP_SERVER.md            # ChatGPT連携用Notion MCPサーバー
│
├── DESIGN.md                       # 設計ドキュメント
├── API_REFERENCE.md                # API リファレンス
├── PLUGIN_DEVELOPMENT.md           # プラグイン開発
│
├── GITHUB_QUICK_START.md           # GitHub クイックスタート
├── GITHUB_GUIDE.md                 # GitHub 詳細ガイド
│
├── AUTOMATION_QUICK_START.md       # 自動化クイックスタート
├── AUTOMATION_GUIDE.md             # 自動化詳細ガイド
│
└── TEST_DATA_README.md             # テストデータガイド
```

---

## 🎯 推奨読書順序

### 初めての方

1. **[README](../README.md)** - プロジェクト概要
2. **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - セットアップ
3. **[USER_MANUAL.md](./USER_MANUAL.md)** - 使い方
4. **[AUTOMATION_QUICK_START.md](./AUTOMATION_QUICK_START.md)** - 自動化設定

### 開発者の方

1. **[REQUIREMENTS.md](./REQUIREMENTS.md)** - システム理解
2. **[DESIGN.md](./DESIGN.md)** - アーキテクチャ
3. **[API_REFERENCE.md](./API_REFERENCE.md)** - API仕様
4. **[PLUGIN_DEVELOPMENT.md](./PLUGIN_DEVELOPMENT.md)** - プラグイン開発

### GitHub・チーム開発

1. **[GITHUB_QUICK_START.md](./GITHUB_QUICK_START.md)** - まずはこれ
2. **[GITHUB_GUIDE.md](./GITHUB_GUIDE.md)** - 詳細を知りたい時

### 運用担当者の方

1. **[AUTOMATION_QUICK_START.md](./AUTOMATION_QUICK_START.md)** - まずはこれ
2. **[AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md)** - 詳細を知りたい時
3. **[USER_MANUAL.md](./USER_MANUAL.md)** - 操作方法

---

## 📊 ドキュメント統計

- **総ファイル数**: 19ファイル
- **総サイズ**: 約151KB
- **言語**: 日本語
- **フォーマット**: Markdown

### カテゴリ別

| カテゴリ | ファイル数 | サイズ |
|---------|----------|--------|
| セットアップ・運用 | 9 | 73KB |
| 開発者向け | 3 | 43KB |
| GitHub | 2 | 20KB |
| 自動化 | 2 | 18KB |
| テスト | 1 | 8KB |
| その他 | 2 | 7KB |

---

## 🔍 ドキュメント検索

### キーワード別

- **セットアップ**: SETUP_GUIDE.md
- **使い方**: USER_MANUAL.md
- **API**: API_REFERENCE.md
- **開発**: PLUGIN_DEVELOPMENT.md, DESIGN.md
- **GitHub**: GITHUB_QUICK_START.md, GITHUB_GUIDE.md
- **自動化**: AUTOMATION_QUICK_START.md, AUTOMATION_GUIDE.md
- **テスト**: TEST_DATA_README.md
- **要件**: REQUIREMENTS.md

---

## 📝 ドキュメントの更新履歴

- **2025-10-24**: Notion MCPサーバー機能ドキュメント追加
- **2025-10-23**: Google Tasks同期機能ドキュメント追加
- **2025-10-23**: Googleカレンダー同期機能ドキュメント追加
- **2025-10-23**: 環境変数設定ガイド追加
- **2025-10-23**: 毎夕の振り返り機能ドキュメント追加
- **2025-10-23**: 毎朝のタスク整理機能ドキュメント追加
- **2025-10-22**: GitHub・自動化ドキュメント追加
- **2025-10-20**: 初版作成

---

**最終更新**: 2025年10月24日  
**バージョン**: 8.0
