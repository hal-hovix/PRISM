
from typing import List


def register() -> dict:
    return {
        "name": "knowledge_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["knowledge"],
    }


def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    
    # Knowledge特有のキーワード（日本語・英語）- 拡充版
    knowledge_indicators = [
        # 既存キーワード
        "how to", "architecture", "design", "reference", "knowledge", "faq",
        "設計", "アーキテクチャ", "ナレッジ", "知識", "技術", "方法",
        "使い方", "手順", "仕組み", "原理", "解説", "ドキュメント",
        "システム", "docker", "api", "プログラミング", "開発",
        
        # 学習関連（追加）
        "学んだ", "学習", "勉強", "理解", "習得", "マスター",
        "について", "とは", "what is", "learn", "study", "understand",
        
        # 技術・概念関連（追加）
        "原則", "手法", "アルゴリズム", "パターン", "フレームワーク",
        "ライブラリ", "ツール", "best practice", "ベストプラクティス",
        "principle", "method", "algorithm", "pattern", "framework",
        
        # プログラミング言語・技術（追加）
        "python", "javascript", "java", "go", "rust", "sql",
        "react", "vue", "angular", "node", "django", "flask",
        "aws", "azure", "gcp", "kubernetes", "git",
        
        # 学術・理論（追加）
        "理論", "概念", "定義", "規則", "法則", "公式",
        "theory", "concept", "definition", "rule", "formula",
        
        # その他知識指標（追加）
        "ノウハウ", "コツ", "秘訣", "テクニック", "スキル",
        "覚え書き", "備忘録", "tips", "trick", "skill"
    ]
    
    # 除外キーワード（これがあると単純なタスク・メモの可能性）
    exclude_indicators = [
        "やる", "する", "実行", "完了", "提出", "締切",
        "do", "execute", "submit", "deadline"
    ]
    
    # キーワードマッチ数をカウント
    match_count = sum(1 for k in knowledge_indicators if k in text)
    has_exclude = any(k in text for k in exclude_indicators)
    
    if match_count > 0 and not has_exclude:
        # マッチ数に応じてスコアを調整
        base_score = 0.80
        bonus = min(0.15, (match_count - 1) * 0.03)
        score = min(0.95, base_score + bonus)
        category = "Knowledge"
        reason = f"keyword match (count: {match_count})"
        tags = list(set([*item.get("tags", []), "knowledge"]))
    elif has_exclude and match_count > 0:
        # 除外キーワードがあるが知識キーワードもある場合は中スコア
        score = 0.5
        category = "Knowledge"
        reason = "mixed signals"
        tags = item.get("tags", [])
    else:
        # Knowledgeキーワードが無い場合は低スコアを返す
        score = 0.2
        category = "Knowledge"
        reason = "no knowledge keyword"
        tags = item.get("tags", [])
    
    return {"type": category, "score": score, "tags": tags, "reason": reason}


