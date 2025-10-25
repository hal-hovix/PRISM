# PRISM プラグイン開発ガイド

**バージョン**: 1.0.0  
**作成日**: 2025年10月21日  
**対象**: 開発者

---

## 目次

1. [プラグインの概要](#1-プラグインの概要)
2. [プラグインの作成](#2-プラグインの作成)
3. [実装例](#3-実装例)
4. [ベストプラクティス](#4-ベストプラクティス)
5. [デバッグ](#5-デバッグ)
6. [テスト](#6-テスト)

---

## 1. プラグインの概要

### 1.1 プラグインとは

PRISMのプラグインは、アイテムの分類ロジックを拡張するためのモジュールです。各プラグインは独立して動作し、独自のロジックでアイテムを分類できます。

### 1.2 プラグインの仕組み

```
アイテム入力
    │
    ▼
プラグイン検出
    │
    ├─ task_classifier.py → スコア: 0.9
    ├─ knowledge_classifier.py → スコア: 0.2
    ├─ note_classifier.py → スコア: 0.6
    └─ template_plugin.py → スコア: 0.5
    │
    ▼
最高スコア選択（0.9）
    │
    ▼
結果返却（Task）
```

### 1.3 プラグインの配置場所

```
src/api/plugins/
├── __init__.py
├── template_plugin.py
├── task_classifier.py
├── knowledge_classifier.py
├── note_classifier.py
└── your_custom_plugin.py  ← ここに追加
```

---

## 2. プラグインの作成

### 2.1 必須インターフェース

すべてのプラグインは以下の2つの関数を実装する必要があります：

#### 2.1.1 register()

プラグインのメタデータを返します。

```python
def register() -> dict:
    """
    プラグインのメタデータを返す
    
    Returns:
        dict: {
            "name": str,              # プラグイン名（一意）
            "version": str,           # バージョン（例: "v1.0.0"）
            "capabilities": List[str], # 機能リスト（例: ["classify"]）
            "labels": List[str]       # ラベル（例: ["task"]）
        }
    """
    return {
        "name": "my_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["custom"],
    }
```

#### 2.1.2 classify()

アイテムを分類します。

```python
def classify(item: dict, *, llm, notion, config) -> dict:
    """
    アイテムを分類する
    
    Args:
        item: 分類対象アイテム
            {
                "title": str,
                "body": str | None,
                "properties": dict,
                "tags": List[str]
            }
        llm: LLMクライアント（MockLLM）
        notion: Notionクライアント（MockNotion）
        config: 設定オブジェクト
    
    Returns:
        dict: {
            "type": str,      # "Task" | "Knowledge" | "Note"
            "score": float,   # 0.0 ~ 1.0（信頼度）
            "tags": List[str],
            "reason": str     # 分類理由
        }
    """
    # 実装
    return {
        "type": "Task",
        "score": 0.9,
        "tags": ["custom"],
        "reason": "custom logic"
    }
```

### 2.2 最小プラグイン

```python
# src/api/plugins/my_plugin.py

from typing import List

def register() -> dict:
    return {
        "name": "my_plugin",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["custom"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    # シンプルなロジック
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    
    if "重要" in text:
        return {
            "type": "Task",
            "score": 0.95,
            "tags": ["important", "task"],
            "reason": "contains '重要'"
        }
    
    return {
        "type": "Note",
        "score": 0.3,
        "tags": [],
        "reason": "no match"
    }
```

---

## 3. 実装例

### 3.1 キーワードベース分類

```python
# src/api/plugins/priority_classifier.py

from typing import List

def register() -> dict:
    return {
        "name": "priority_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["task", "priority"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    
    # 優先度キーワード
    high_priority_keywords = ["緊急", "urgent", "asap", "重要", "critical"]
    medium_priority_keywords = ["important", "必要", "required"]
    
    has_high = any(k in text for k in high_priority_keywords)
    has_medium = any(k in text for k in medium_priority_keywords)
    
    if has_high:
        return {
            "type": "Task",
            "score": 0.95,
            "tags": ["task", "high-priority"],
            "reason": "high priority keyword detected"
        }
    elif has_medium:
        return {
            "type": "Task",
            "score": 0.85,
            "tags": ["task", "medium-priority"],
            "reason": "medium priority keyword detected"
        }
    
    # マッチしない場合は低スコア
    return {
        "type": "Task",
        "score": 0.1,
        "tags": [],
        "reason": "no priority keyword"
    }
```

### 3.2 日付ベース分類

```python
# src/api/plugins/deadline_classifier.py

import re
from datetime import datetime, timedelta
from typing import List

def register() -> dict:
    return {
        "name": "deadline_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["task", "deadline"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    
    # 日付パターン
    date_patterns = [
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2025-10-21
        r'\d{1,2}[-/]\d{1,2}',            # 10-21
        r'明日|tomorrow',
        r'今週|this week',
        r'来週|next week',
    ]
    
    has_date = any(re.search(pattern, text) for pattern in date_patterns)
    
    if has_date:
        # 締切キーワードも確認
        deadline_keywords = ["締切", "期限", "deadline", "due"]
        has_deadline = any(k in text for k in deadline_keywords)
        
        if has_deadline:
            score = 0.95
            reason = "deadline with date"
        else:
            score = 0.85
            reason = "date mentioned"
        
        return {
            "type": "Task",
            "score": score,
            "tags": ["task", "deadline"],
            "reason": reason
        }
    
    return {
        "type": "Task",
        "score": 0.1,
        "tags": [],
        "reason": "no date found"
    }
```

### 3.3 LLM活用型

```python
# src/api/plugins/ai_classifier.py

from typing import List

def register() -> dict:
    return {
        "name": "ai_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["ai", "llm"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}"
    
    # LLMに問い合わせ
    prompt = f"""
以下のテキストを「Task」「Knowledge」「Note」のいずれかに分類してください。
分類のみを返してください。

テキスト:
{text}

分類:"""
    
    category = llm.complete(
        prompt=prompt,
        system="あなたは優秀な分類AIです。",
        temperature=0.0
    )
    
    # LLMの結果を検証
    valid_categories = ["Task", "Knowledge", "Note"]
    if category not in valid_categories:
        category = "Note"
    
    return {
        "type": category,
        "score": 0.7,  # LLMベースは中程度のスコア
        "tags": [category.lower()],
        "reason": "AI classification"
    }
```

### 3.4 複合ロジック

```python
# src/api/plugins/smart_classifier.py

from typing import List

def register() -> dict:
    return {
        "name": "smart_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["smart", "multi"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    title = item.get('title', '').lower()
    
    # 複数の条件を組み合わせ
    score = 0.0
    category = "Note"
    reasons = []
    
    # 条件1: タイトルに「TODO」「タスク」
    if any(k in title for k in ["todo", "task", "タスク"]):
        score += 0.4
        reasons.append("title_task")
    
    # 条件2: 締切キーワード
    if any(k in text for k in ["締切", "期限", "deadline"]):
        score += 0.3
        reasons.append("deadline")
    
    # 条件3: アクション動詞
    action_verbs = ["する", "実施", "実行", "完了", "提出", "送信"]
    if any(v in text for v in action_verbs):
        score += 0.2
        reasons.append("action_verb")
    
    # スコアが0.5以上ならTask
    if score >= 0.5:
        category = "Task"
        tags = ["task"]
    else:
        tags = []
    
    return {
        "type": category,
        "score": min(score, 1.0),  # 最大1.0に制限
        "tags": tags,
        "reason": " + ".join(reasons) if reasons else "no match"
    }
```

---

## 4. ベストプラクティス

### 4.1 スコアリングの推奨値

| 信頼度 | スコア範囲 | 使用場面 |
|--------|----------|---------|
| 非常に高い | 0.9 - 1.0 | 明確なキーワード一致 |
| 高い | 0.7 - 0.9 | 複数条件一致 |
| 中程度 | 0.5 - 0.7 | LLMベース、単一条件 |
| 低い | 0.3 - 0.5 | 弱い一致 |
| フォールバック | 0.1 - 0.3 | マッチしない場合 |

### 4.2 プラグイン優先度の設定

高いスコアを返すプラグインが優先されます。専用プラグインは汎用プラグインより高いスコアを返すべきです。

```python
# 専用プラグイン（高スコア）
if keyword_match:
    score = 0.9  # 専用ロジックは高スコア

# 汎用プラグイン（中スコア）
if general_match:
    score = 0.5  # 汎用ロジックは中スコア
```

### 4.3 タグの活用

タグは検索やフィルタリングに使用されます。適切にタグを付けましょう。

```python
# 良い例
tags = ["task", "urgent", "deadline", "high-priority"]

# 悪い例
tags = []  # タグなし
tags = ["その他"]  # 意味のないタグ
```

### 4.4 エラーハンドリング

```python
def classify(item: dict, *, llm, notion, config) -> dict:
    try:
        # メイン処理
        text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
        # ... 分類ロジック ...
        
    except Exception as e:
        # エラー時はフォールバック
        return {
            "type": "Note",
            "score": 0.1,
            "tags": [],
            "reason": f"error: {str(e)}"
        }
```

### 4.5 パフォーマンス

- 重い処理は避ける（目標: 100ms以内）
- 外部API呼び出しは最小限に
- キャッシュを活用（将来）

---

## 5. デバッグ

### 5.1 ログ出力

```python
import logging

logger = logging.getLogger(__name__)

def classify(item: dict, *, llm, notion, config) -> dict:
    logger.info(f"Classifying: {item.get('title')}")
    
    # ... 処理 ...
    
    logger.debug(f"Score: {score}, Reason: {reason}")
    
    return result
```

### 5.2 デバッグ用プラグイン

```python
# src/api/plugins/debug_plugin.py

def register() -> dict:
    return {
        "name": "debug_plugin",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["debug"],
    }

def classify(item: dict, *, llm, notion, config) -> dict:
    print(f"=== DEBUG ===")
    print(f"Title: {item.get('title')}")
    print(f"Body: {item.get('body')}")
    print(f"Tags: {item.get('tags')}")
    print(f"=============")
    
    # 常に低スコアを返す（他のプラグインが優先される）
    return {
        "type": "Note",
        "score": 0.0,
        "tags": ["debug"],
        "reason": "debug only"
    }
```

### 5.3 テストデータ

```python
# テスト用アイテム
test_items = [
    {"title": "レポート提出", "body": "明日までに提出"},
    {"title": "Dockerの使い方", "body": "コンテナ技術"},
    {"title": "今日の気づき", "body": "プロジェクトの学び"},
]

for item in test_items:
    result = classify(item, llm=None, notion=None, config=None)
    print(f"{item['title']} → {result['type']} ({result['score']})")
```

---

## 6. テスト

### 6.1 ユニットテスト

```python
# tests/test_my_plugin.py

import pytest
from src.api.plugins.my_plugin import register, classify

def test_register():
    """register()のテスト"""
    meta = register()
    assert meta["name"] == "my_plugin"
    assert "classify" in meta["capabilities"]

def test_classify_task():
    """Task分類のテスト"""
    item = {
        "title": "重要なタスク",
        "body": "明日までに完了",
        "tags": []
    }
    
    result = classify(item, llm=None, notion=None, config=None)
    
    assert result["type"] == "Task"
    assert result["score"] > 0.5
    assert "task" in result["tags"]

def test_classify_note():
    """Note分類のテスト"""
    item = {
        "title": "ただのメモ",
        "body": "特に何もない",
        "tags": []
    }
    
    result = classify(item, llm=None, notion=None, config=None)
    
    assert result["type"] == "Note"
    assert result["score"] < 0.5
```

### 6.2 統合テスト

```python
# tests/test_plugin_integration.py

from src.api.core.plugins import discover_plugins, classify_with_plugins

def test_plugin_discovery():
    """プラグイン検出のテスト"""
    plugins = discover_plugins()
    
    assert "my_plugin" in plugins
    assert plugins["my_plugin"].version == "v1.0.0"

def test_classification_flow():
    """分類フロー全体のテスト"""
    item = {"title": "重要タスク", "body": "明日まで"}
    
    result = classify_with_plugins(
        item,
        llm=None,
        notion=None,
        config=None
    )
    
    assert result["type"] in ["Task", "Knowledge", "Note"]
    assert 0.0 <= result["score"] <= 1.0
```

---

## 7. 配布とバージョン管理

### 7.1 バージョニング

```python
def register() -> dict:
    return {
        "name": "my_plugin",
        "version": "v1.2.0",  # セマンティックバージョニング
        ...
    }
```

### 7.2 変更履歴

プラグインファイルにコメントで記載：

```python
"""
my_plugin.py - カスタム分類プラグイン

変更履歴:
- v1.2.0 (2025-10-22): スコアリングロジック改善
- v1.1.0 (2025-10-21): 新キーワード追加
- v1.0.0 (2025-10-20): 初版リリース
"""
```

---

## 8. よくある質問

### Q1: プラグインは自動的に読み込まれますか？

**A**: はい、`src/api/plugins/` に配置すれば自動的に検出されます。再起動が必要です。

### Q2: 複数のプラグインが同じスコアを返した場合は？

**A**: 最初に評価されたプラグインの結果が採用されます（順序は不定）。

### Q3: プラグインを無効化できますか？

**A**: はい、ファイル名を`.py.disabled`などに変更すれば無効化されます。

### Q4: LLMやNotionクライアントは必須ですか？

**A**: いいえ、使わない場合は`llm`や`notion`引数を無視してください。

---

**ドキュメント改訂履歴**

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-10-21 | 初版作成 | PRISM Team |







