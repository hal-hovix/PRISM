# INBOX前処理機能 - 実装完了

## 📋 概要

INBOXの自動仕訳前処理機能を実装しました。この機能により、NotionDBの"INBOX"において以下の処理が自動的に行われます：

1. **タイトルと内容の相互コピー**
2. **内容の要約生成（20文字程度）**
3. **自動仕訳でのタイトル上書き**

## 🔧 実装内容

### 1. タイトルと内容の相互コピー

#### ケース1: タイトルが空で内容がある場合
```
元の状態:
- タイトル: (空)
- 内容: "これは内容のみのテストアイテムです。詳細な説明が含まれています。"

処理後:
- タイトル: "これは内容のみのテストアイテムです。詳細な説明が含まれています。"
- 内容: "これは内容のみのテストアイテムです。詳細な説明が含まれています。"
```

#### ケース2: 内容が空でタイトルがある場合
```
元の状態:
- タイトル: "これはタイトルのみのテストアイテムです"
- 内容: (空)

処理後:
- タイトル: "これはタイトルのみのテストアイテムです"
- 内容: "これはタイトルのみのテストアイテムです"
```

### 2. 要約生成機能

内容を20文字程度に要約し、自動仕訳時にタイトルに上書きします。

```
元の内容: "これは長い内容のテストです。詳細な説明が含まれており、20文字を超える長い文章になっています。"

要約結果: "これは長い内容のテストです。"
```

## 📁 実装ファイル

### 1. 同期処理 (`tools/advanced_classify_inbox.py`)

#### 追加された関数
- `preprocess_inbox_item(item)`: INBOXアイテムの前処理
- `generate_summary(title, content)`: 要約生成
- `extract_item_data(page)`: 内容フィールドの追加

#### 修正された処理フロー
```python
# 各アイテムを処理
for i, page in enumerate(items, 1):
    # アイテムデータ抽出（タイトル + 内容）
    item = extract_item_data(page)
    
    # 前処理：タイトルと内容の相互コピー
    preprocess_inbox_item(item)
    
    # 分類実行
    classification = classify_with_prism(item)
    
    # 要約生成（20文字程度）
    summary = generate_summary(item['title'], item.get('content', ''))
    
    # 新しいデータベースに作成（要約をタイトルに使用）
    create_page_in_database(target_db, summary, ...)
```

### 2. 非同期処理 (`src/api/core/async_classification.py`)

#### 追加された関数
- `_preprocess_inbox_item(item)`: 非同期INBOX前処理
- `_generate_summary(title, content)`: 非同期要約生成

#### 修正された処理フロー
```python
async def process_inbox_async(self, inbox_database_id: str, target_database_id: str):
    # INBOXアイテムを取得
    items = await self.notion_client.fetch_pages_async(inbox_database_id)
    
    # 前処理：タイトルと内容の相互コピー
    preprocessed_items = []
    for item in items:
        preprocessed_item = await self._preprocess_inbox_item(item)
        if preprocessed_item:
            preprocessed_items.append(preprocessed_item)
    
    # 分類処理
    results = await self.classification_processor.classify_items_async(preprocessed_items, config)
```

### 3. テストスクリプト (`tools/test_inbox_preprocessing.py`)

4つのテストケースを実装：
1. タイトルが空で内容がある場合
2. 内容が空でタイトルがある場合
3. タイトルと内容の両方がある場合
4. タイトルと内容の両方が空の場合

## 🚀 使用方法

### 1. 手動実行（同期処理）
```bash
cd /Users/hal1956/development/PRISM
python tools/advanced_classify_inbox.py
```

### 2. API経由（非同期処理）
```bash
curl -X POST http://localhost:8060/async/inbox/process \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_database_id": "2935fbef-07e2-8008-bea4-d40152540791",
    "target_database_id": "2935fbef-07e2-8074-bdf8-f9c06755f45a",
    "use_cache": true
  }'
```

### 3. テスト実行
```bash
python tools/test_inbox_preprocessing.py
```

## 📊 処理結果例

### テスト実行結果
```
テストケース1: タイトルが空で内容がある場合
  📝 内容をタイトルにコピー: これは内容のみのテストアイテムです。詳細な説明が含まれていま...
  更新後タイトル: 'これは内容のみのテストアイテムです。詳細な説明が含まれています。'
  生成された要約: 'これは内容のみのテストアイテムです。'

テストケース2: 内容が空でタイトルがある場合
  📝 タイトルを内容にコピー: これはタイトルのみのテストアイテムです...
  更新後タイトル: 'これはタイトルのみのテストアイテムです'
  更新後内容: 'これはタイトルのみのテストアイテムです'
  生成された要約: 'これはタイトルのみのテストアイテムです'

テストケース3: タイトルと内容の両方がある場合
  更新された: False
  生成された要約: 'これは長い内容のテストです。'
```

## ✅ 実装完了項目

- [x] タイトルが空で内容がある場合の処理
- [x] 内容が空でタイトルがある場合の処理
- [x] 内容の20文字程度要約生成
- [x] 自動仕訳でのタイトル上書き
- [x] 同期処理での実装
- [x] 非同期処理での実装
- [x] テストスクリプトの作成
- [x] 動作確認完了

## 🎯 効果

1. **データの整合性向上**: タイトルと内容の相互補完により、不完全なデータを自動修正
2. **処理効率向上**: 要約により、自動仕訳時のタイトルが適切な長さに調整
3. **ユーザビリティ向上**: 手動での修正作業が不要
4. **一貫性確保**: すべてのINBOXアイテムが統一された形式で処理

この実装により、INBOXの自動仕訳処理がより効率的かつ正確になりました。
