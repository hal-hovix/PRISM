
from typing import List


def register() -> dict:
    return {
        "name": "task_classifier",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["task"],
    }


def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}".lower()
    
    # Task特有のキーワード（日本語・英語）- 拡充版
    task_indicators = [
        # 既存キーワード
        "todo", "task", "deadline", "due", "schedule", "assign",
        "タスク", "締切", "期限", "予定", "やること", "実施",
        "完了", "実行", "作業", "提出", "レポート", "準備",
        
        # アクション動詞（追加）
        "修正", "調査", "確認", "電話", "連絡", "相談", "打ち合わせ",
        "開発", "実装", "テスト", "デプロイ", "リリース",
        "fix", "bug", "debug", "issue", "solve", "check", "call",
        "contact", "meeting", "develop", "implement", "deploy",
        
        # 定期タスク関連（追加）
        "毎週", "毎月", "毎日", "定例", "レビュー", "週次", "月次",
        "weekly", "monthly", "daily", "review", "recurring",
        
        # その他タスク指標（追加）
        "対応", "処理", "申請", "承認", "更新", "追加", "削除",
        "改善", "最適化", "整理", "まとめ"
    ]
    
    # 除外キーワード（これがあるとTaskではない可能性）
    exclude_indicators = [
        "メモ", "記録", "日記", "雑記", "感想", "思った",
        "memo", "note", "diary", "journal"
    ]
    
    # キーワードマッチ数をカウント
    match_count = sum(1 for k in task_indicators if k in text)
    has_exclude = any(k in text for k in exclude_indicators)
    
    if match_count > 0 and not has_exclude:
        # マッチ数に応じてスコアを調整（複数マッチでより高スコア）
        base_score = 0.85
        bonus = min(0.10, (match_count - 1) * 0.03)
        score = min(0.95, base_score + bonus)
        category = "Task"
        reason = f"keyword match (count: {match_count})"
        tags = list(set([*item.get("tags", []), "task"]))
    elif has_exclude:
        # 除外キーワードがある場合は低スコア
        score = 0.1
        category = "Task"
        reason = "excluded by keyword"
        tags = item.get("tags", [])
    else:
        # タスクキーワードが無い場合は低スコアを返す
        score = 0.2
        category = "Task"
        reason = "no task keyword"
        tags = item.get("tags", [])
    
    return {"type": category, "score": score, "tags": tags, "reason": reason}


