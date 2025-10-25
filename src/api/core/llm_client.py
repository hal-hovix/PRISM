
from typing import Optional


class MockLLM:
    def complete(self, prompt: str, system: Optional[str] = None, temperature: float = 0.0) -> str:
        # Simple heuristic for tests - improved classification logic
        text = f"{system or ''}\n{prompt}".lower()
        
        # Note特有のキーワードを優先的にチェック
        note_keywords = [
            "メモ", "気づき", "記録", "日記", "備忘", "覚書",
            "memo", "note", "diary", "observation", "記憶", "思考",
            "会議メモ", "meeting notes", "学び", "learning",
            "振り返り", "reflection", "感想", "impression"
        ]
        
        # Task特有のキーワード
        task_keywords = [
            "deadline", "todo", "due", "schedule", "task", "assign",
            "タスク", "締切", "期限", "予定", "やること", "実施",
            "完了", "実行", "作業", "提出", "レポート", "準備"
        ]
        
        # Knowledge特有のキーワード
        knowledge_keywords = [
            "how to", "architecture", "doc", "knowledge", "learn",
            "設計", "アーキテクチャ", "ナレッジ", "知識", "技術", "方法",
            "使い方", "手順", "仕組み", "原理", "解説", "ドキュメント",
            "システム", "docker", "api", "プログラミング", "開発"
        ]
        
        has_task = any(k in text for k in task_keywords)
        has_knowledge = any(k in text for k in knowledge_keywords)
        has_note = any(k in text for k in note_keywords)
        
        # 優先順位: Task > Knowledge > Note
        if has_task:
            return "Task"
        elif has_knowledge:
            return "Knowledge"
        elif has_note:
            return "Note"
        else:
            # デフォルトはNote
            return "Note"


