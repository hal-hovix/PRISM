
from typing import List


def register() -> dict:
    return {
        "name": "note_classifier",
        "version": "v1.1.0",
        "capabilities": ["classify"],
        "labels": ["note"],
    }


def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    
    # Note特有のキーワード（日本語・英語）- 拡充版
    note_indicators = [
        # 既存キーワード
        "メモ", "気づき", "記録", "日記", "備忘", "覚書",
        "memo", "note", "diary", "observation", "記憶", "思考",
        "会議メモ", "meeting notes", "学び", "learning",
        "振り返り", "reflection", "感想", "impression",
        
        # 個人的な記録（追加）
        "雑記", "つぶやき", "ログ", "ジャーナル",
        "journal", "log", "thoughts", "random",
        
        # アイデア・思いつき（追加）
        "アイデア", "思いつき", "ひらめき", "発想",
        "idea", "inspiration", "brainstorm",
        
        # 読書・引用（追加）
        "読書", "読んだ", "引用", "抜粋",
        "reading", "quote", "excerpt", "book",
        
        # その他メモ指標（追加）
        "今日の", "昨日の", "最近", "ふと",
        "today", "yesterday", "recently", "suddenly"
    ]
    
    # タスクやナレッジの強いキーワードがないかチェック（拡充版）
    task_keywords = [
        "todo", "task", "deadline", "due", "schedule", "assign",
        "タスク", "締切", "期限", "やること", "実施", "完了"
    ]
    knowledge_keywords = [
        "how to", "architecture", "design", "reference", "knowledge", "faq",
        "設計", "アーキテクチャ", "ナレッジ", "知識", "技術", "原則",
        "ベストプラクティス", "best practice"
    ]
    
    # キーワードマッチ数をカウント
    note_count = sum(1 for k in note_indicators if k in text)
    has_task = any(k in text for k in task_keywords)
    has_knowledge = any(k in text for k in knowledge_keywords)
    
    # スコアリングロジック（改善版）
    if note_count > 0 and not has_task and not has_knowledge:
        # Note特有のキーワードがあり、他のカテゴリのキーワードがない
        base_score = 0.75
        bonus = min(0.15, (note_count - 1) * 0.03)
        score = min(0.90, base_score + bonus)
        category = "Note"
        reason = f"note keyword match (count: {note_count})"
    elif note_count > 0 and (has_task or has_knowledge):
        # Noteキーワードがあるが他のカテゴリとも重複
        score = 0.5
        category = "Note"
        reason = "mixed signals"
    elif not has_task and not has_knowledge and not note_count:
        # どのキーワードもない場合はNoteにフォールバック（スコア下げる）
        score = 0.4
        category = "Note"
        reason = "fallback to note"
    else:
        # 他のカテゴリのキーワードが強い場合は低スコア
        score = 0.2
        category = "Note"
        reason = "low confidence"
    
    tags: List[str] = list(set([*item.get("tags", []), "note"])) if score >= 0.5 else item.get("tags", [])
    return {"type": category, "score": score, "tags": tags, "reason": reason}


