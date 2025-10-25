"""
非同期Notionクライアント
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from ..core.logging import get_logger
from ..core.config import load_config

logger = get_logger(__name__)

class AsyncNotionClient:
    """非同期Notionクライアント"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
    
    async def fetch_pages_async(self, database_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """非同期でページを取得"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
        all_pages = []
        has_more = True
        start_cursor = None
        
        while has_more:
            try:
                url = f"{self.base_url}/databases/{database_id}/query"
                data = {
                    "page_size": page_size
                }
                
                if start_cursor:
                    data["start_cursor"] = start_cursor
                
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        pages = result.get('results', [])
                        all_pages.extend(pages)
                        
                        has_more = result.get('has_more', False)
                        start_cursor = result.get('next_cursor')
                        
                        logger.debug(f"Fetched {len(pages)} pages from database {database_id}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch pages: {response.status} - {error_text}")
                        break
                        
            except Exception as e:
                logger.error(f"Error fetching pages: {e}")
                break
        
        logger.info(f"Total pages fetched: {len(all_pages)}")
        return all_pages
    
    async def create_page_async(self, database_id: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """非同期でページを作成"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
        try:
            url = f"{self.base_url}/pages"
            data = {
                "parent": {"database_id": database_id},
                "properties": properties
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Created page: {result.get('id')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create page: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            return None
    
    async def update_page_async(self, page_id: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """非同期でページを更新"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
        try:
            url = f"{self.base_url}/pages/{page_id}"
            data = {"properties": properties}
            
            async with self.session.patch(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Updated page: {page_id}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update page: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating page: {e}")
            return None
    
    async def archive_page_async(self, page_id: str) -> bool:
        """非同期でページをアーカイブ"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
        try:
            url = f"{self.base_url}/pages/{page_id}"
            data = {"archived": True}
            
            async with self.session.patch(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"Archived page: {page_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to archive page: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error archiving page: {e}")
            return False

class AsyncBatchProcessor:
    """非同期バッチ処理クラス"""
    
    def __init__(self, notion_client: AsyncNotionClient, max_concurrent: int = 10):
        self.notion_client = notion_client
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_pages_batch(self, pages: List[Dict[str, Any]], processor_func) -> List[Any]:
        """ページをバッチで非同期処理"""
        async def process_with_semaphore(page):
            async with self.semaphore:
                return await processor_func(page)
        
        tasks = [process_with_semaphore(page) for page in pages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外をフィルタリング
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        if failed_results:
            logger.warning(f"Failed to process {len(failed_results)} pages")
            for error in failed_results:
                logger.error(f"Processing error: {error}")
        
        return successful_results
    
    async def create_pages_batch(self, database_id: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ページをバッチで非同期作成"""
        async def create_page(page_data):
            return await self.notion_client.create_page_async(database_id, page_data)
        
        return await self.process_pages_batch(pages_data, create_page)
    
    async def update_pages_batch(self, pages_updates: List[tuple]) -> List[Dict[str, Any]]:
        """ページをバッチで非同期更新"""
        async def update_page(page_update):
            page_id, properties = page_update
            return await self.notion_client.update_page_async(page_id, properties)
        
        return await self.process_pages_batch(pages_updates, update_page)
    
    async def archive_pages_batch(self, page_ids: List[str]) -> List[bool]:
        """ページをバッチで非同期アーカイブ"""
        async def archive_page(page_id):
            return await self.notion_client.archive_page_async(page_id)
        
        return await self.process_pages_batch(page_ids, archive_page)
