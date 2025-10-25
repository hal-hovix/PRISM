
from typing import Dict, List


def register() -> dict:
    return {
        "name": "template",
        "version": "v1.0.0",
        "capabilities": ["classify"],
        "labels": ["task", "knowledge", "note"],
    }


def classify(item: dict, *, llm, notion, config) -> dict:
    text = f"{item.get('title', '')}\n{item.get('body', '')}"
    category = llm.complete(
        prompt=text,
        system="Classify into Task/Knowledge/Note",
        temperature=0.0,
    )
    
    # template_pluginはフォールバックとして機能するため、
    # 専用プラグインより低いスコアを設定
    score = 0.5
    
    if category == "Task":
        tags: List[str] = list(set([*item.get("tags", []), "task"]))
    elif category == "Knowledge":
        tags = list(set([*item.get("tags", []), "knowledge"]))
    else:
        tags = list(set([*item.get("tags", []), "note"]))
    return {"type": category, "score": score, "tags": tags, "reason": "llm classification"}


