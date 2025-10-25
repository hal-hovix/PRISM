"""
非同期APIエンドポイント
"""
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.logging import get_logger
from ..core.config import load_config
from ..core.security import verify_api_key
from ..core.async_notion_client import AsyncNotionClient
from ..core.cache import NotionCache, cache_manager
from ..core.async_classification import AsyncInboxProcessor

logger = get_logger(__name__)

router = APIRouter(prefix="/async", tags=["async"])

class AsyncBatchRequest(BaseModel):
    """非同期バッチリクエスト"""
    items: List[Dict[str, Any]] = Field(..., description="処理するアイテムのリスト")
    database_id: str = Field(..., description="対象データベースID")
    batch_size: int = Field(default=10, description="バッチサイズ")

class AsyncClassificationRequest(BaseModel):
    """非同期分類リクエスト"""
    inbox_database_id: str = Field(..., description="INBOXデータベースID")
    target_database_id: str = Field(..., description="対象データベースID")
    use_cache: bool = Field(default=True, description="キャッシュを使用するか")

class AsyncTaskResponse(BaseModel):
    """非同期タスクレスポンス"""
    task_id: str = Field(..., description="タスクID")
    status: str = Field(..., description="タスクステータス")
    message: str = Field(..., description="メッセージ")

# タスク管理用の辞書（本番環境ではRedis等を使用）
active_tasks: Dict[str, Dict[str, Any]] = {}

@router.post("/classify/batch")
async def async_classify_batch(
    request: AsyncBatchRequest,
    background_tasks: BackgroundTasks,
    _=Depends(verify_api_key)
):
    """非同期バッチ分類"""
    try:
        config = load_config()
        
        # タスクIDを生成
        import uuid
        task_id = str(uuid.uuid4())
        
        # タスクを登録
        active_tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "total_items": len(request.items),
            "results": [],
            "created_at": asyncio.get_event_loop().time()
        }
        
        # バックグラウンドで処理を開始
        background_tasks.add_task(
            process_async_classification,
            task_id,
            request.items,
            request.database_id,
            request.batch_size,
            config
        )
        
        return AsyncTaskResponse(
            task_id=task_id,
            status="processing",
            message=f"Started processing {len(request.items)} items"
        )
        
    except Exception as e:
        logger.error(f"Failed to start async classification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.post("/inbox/process")
async def async_process_inbox(
    request: AsyncClassificationRequest,
    background_tasks: BackgroundTasks,
    _=Depends(verify_api_key)
):
    """非同期INBOX処理"""
    try:
        config = load_config()
        
        # タスクIDを生成
        import uuid
        task_id = str(uuid.uuid4())
        
        # タスクを登録
        active_tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "inbox_database_id": request.inbox_database_id,
            "target_database_id": request.target_database_id,
            "results": {},
            "created_at": asyncio.get_event_loop().time()
        }
        
        # バックグラウンドで処理を開始
        background_tasks.add_task(
            process_async_inbox,
            task_id,
            request.inbox_database_id,
            request.target_database_id,
            request.use_cache,
            config
        )
        
        return AsyncTaskResponse(
            task_id=task_id,
            status="processing",
            message="Started inbox processing"
        )
        
    except Exception as e:
        logger.error(f"Failed to start async inbox processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")

@router.get("/task/{task_id}")
async def get_task_status(task_id: str, _=Depends(verify_api_key)):
    """タスクステータスを取得"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "total_items": task.get("total_items", 0),
        "results": task.get("results", {}),
        "created_at": task["created_at"],
        "elapsed_time": asyncio.get_event_loop().time() - task["created_at"]
    }

@router.delete("/task/{task_id}")
async def cancel_task(task_id: str, _=Depends(verify_api_key)):
    """タスクをキャンセル"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    active_tasks[task_id]["status"] = "cancelled"
    
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancelled successfully"
    }

@router.get("/tasks")
async def list_tasks(_=Depends(verify_api_key)):
    """アクティブタスク一覧を取得"""
    current_time = asyncio.get_event_loop().time()
    
    # 古いタスクをクリーンアップ（1時間以上前）
    expired_tasks = [
        task_id for task_id, task in active_tasks.items()
        if current_time - task["created_at"] > 3600
    ]
    
    for task_id in expired_tasks:
        del active_tasks[task_id]
    
    return {
        "active_tasks": len(active_tasks),
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "progress": task["progress"],
                "created_at": task["created_at"],
                "elapsed_time": current_time - task["created_at"]
            }
            for task_id, task in active_tasks.items()
        ]
    }

async def process_async_classification(
    task_id: str,
    items: List[Dict[str, Any]],
    database_id: str,
    batch_size: int,
    config: Any
):
    """非同期分類処理を実行"""
    try:
        async with AsyncNotionClient(config.notion_api_key) as notion_client:
            async with cache_manager as cache:
                notion_cache = NotionCache(cache)
                processor = AsyncInboxProcessor(notion_client, notion_cache)
                
                # バッチで処理
                total_items = len(items)
                processed_items = 0
                
                for i in range(0, total_items, batch_size):
                    batch = items[i:i + batch_size]
                    
                    # 分類処理
                    results = await processor.classification_processor.classify_items_async(batch, config)
                    
                    # Notionに同期
                    sync_results = await processor.classification_processor.sync_to_notion_async(
                        results, database_id
                    )
                    
                    processed_items += len(batch)
                    progress = int((processed_items / total_items) * 100)
                    
                    # タスクステータスを更新
                    active_tasks[task_id].update({
                        "progress": progress,
                        "results": sync_results
                    })
                    
                    # バッチ間で少し待機
                    await asyncio.sleep(0.1)
                
                # 完了
                active_tasks[task_id]["status"] = "completed"
                active_tasks[task_id]["progress"] = 100
                
                logger.info(f"Async classification completed for task {task_id}")
                
    except Exception as e:
        logger.error(f"Async classification failed for task {task_id}: {e}")
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error"] = str(e)

async def process_async_inbox(
    task_id: str,
    inbox_database_id: str,
    target_database_id: str,
    use_cache: bool,
    config: Any
):
    """非同期INBOX処理を実行"""
    try:
        async with AsyncNotionClient(config.notion_api_key) as notion_client:
            async with cache_manager as cache:
                notion_cache = NotionCache(cache)
                processor = AsyncInboxProcessor(notion_client, notion_cache)
                
                # INBOX処理
                results = await processor.process_inbox_async(
                    inbox_database_id, target_database_id
                )
                
                # 完了
                active_tasks[task_id]["status"] = "completed"
                active_tasks[task_id]["progress"] = 100
                active_tasks[task_id]["results"] = results
                
                logger.info(f"Async inbox processing completed for task {task_id}")
                
    except Exception as e:
        logger.error(f"Async inbox processing failed for task {task_id}: {e}")
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error"] = str(e)
