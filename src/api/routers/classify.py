
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.config import load_config
from ..core.plugins import classify_with_plugins
from ..core import llm_client, notion_client
from ..core.security import verify_api_key


router = APIRouter(prefix="", tags=["classify"])


class ItemModel(BaseModel):
    title: str
    body: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class BatchRequest(BaseModel):
    items: List[ItemModel]


def get_clients():
    cfg = load_config()
    llm = llm_client.MockLLM()
    notion = notion_client.MockNotion()
    return cfg, llm, notion


@router.post("/classify")
def classify_endpoint(payload: BatchRequest, _=Depends(verify_api_key)):
    """アイテムを分類するエンドポイント（認証必須）"""
    try:
        cfg, llm, notion = get_clients()
        results = []
        for item in payload.items:
            result = classify_with_plugins(item.model_dump(), llm=llm, notion=notion, config=cfg)
            results.append(result)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/sync/notion")
def sync_notion(_=Depends(verify_api_key)):
    """Notion同期エンドポイント（認証必須）"""
    try:
        # Mock sync for now
        return {"status": "queued", "message": "Sync request received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

