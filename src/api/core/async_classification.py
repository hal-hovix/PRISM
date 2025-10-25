"""
非同期分類処理
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.logging import get_logger
from ..core.config import load_config
from ..core.async_notion_client import AsyncNotionClient, AsyncBatchProcessor
from ..core.cache import NotionCache, cache_manager

logger = get_logger(__name__)

class AsyncClassificationProcessor:
    """非同期分類処理クラス"""
    
    def __init__(self, notion_client: AsyncNotionClient, cache: NotionCache):
        self.notion_client = notion_client
        self.cache = cache
        self.batch_processor = AsyncBatchProcessor(notion_client)
    
    async def classify_items_async(self, items: List[Dict[str, Any]], config: Any) -> List[Dict[str, Any]]:
        """アイテムを非同期で分類"""
        logger.info(f"Starting async classification of {len(items)} items")
        
        # バッチサイズを設定（並行処理数を制限）
        batch_size = 10
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_batch_async(batch, config)
            results.extend(batch_results)
            
            # バッチ間で少し待機（API制限を考慮）
            await asyncio.sleep(0.1)
        
        logger.info(f"Completed async classification: {len(results)} results")
        return results
    
    async def _process_batch_async(self, batch: List[Dict[str, Any]], config: Any) -> List[Dict[str, Any]]:
        """バッチを非同期で処理"""
        async def process_item(item):
            try:
                # ここで実際の分類ロジックを実装
                # 現在はモック実装
                result = await self._classify_single_item_async(item, config)
                return result
            except Exception as e:
                logger.error(f"Error processing item {item.get('id', 'unknown')}: {e}")
                return {
                    "id": item.get('id'),
                    "status": "error",
                    "error": str(e)
                }
        
        # バッチ内のアイテムを並行処理
        tasks = [process_item(item) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外をフィルタリング
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        if failed_results:
            logger.warning(f"Failed to process {len(failed_results)} items in batch")
        
        return successful_results
    
    async def _classify_single_item_async(self, item: Dict[str, Any], config: Any) -> Dict[str, Any]:
        """単一アイテムを非同期で分類"""
        # モック実装 - 実際の分類ロジックに置き換え
        await asyncio.sleep(0.01)  # 非同期処理をシミュレート
        
        # タイトルと内容を取得
        properties = item.get('properties', {})
        title_prop = properties.get('タイトル', {})
        title = ''.join([t.get('plain_text', '') for t in title_prop.get('title', [])])
        
        content_prop = properties.get('内容', {})
        content = ''.join([t.get('plain_text', '') for t in content_prop.get('rich_text', [])])
        
        # 要約生成（20文字程度）
        summary = self._generate_summary(title, content)
        
        return {
            "id": item.get('id'),
            "title": title,
            "content": content,
            "summary": summary,
            "status": "classified",
            "category": "general",
            "confidence": 0.85,
            "processed_at": datetime.now().isoformat()
        }
    
    def _generate_summary(self, title: str, content: str) -> str:
        """タイトルと内容から要約を生成（20文字程度）"""
        # 内容がある場合は内容を要約、なければタイトルを使用
        source_text = content.strip() if content.strip() else title.strip()
        
        if not source_text:
            return "内容なし"
        
        # 20文字程度に要約
        if len(source_text) <= 20:
            return source_text
        
        # 文の区切りで切る
        sentences = source_text.split('。')
        summary = ""
        
        for sentence in sentences:
            if len(summary + sentence) <= 20:
                summary += sentence + "。"
            else:
                break
        
        # まだ長い場合は文字数で切る
        if len(summary) > 20:
            summary = summary[:17] + "..."
        
        return summary.strip()
    
    async def sync_to_notion_async(self, results: List[Dict[str, Any]], database_id: str) -> Dict[str, int]:
        """結果をNotionに非同期で同期"""
        logger.info(f"Starting async Notion sync for {len(results)} results")
        
        # 成功した結果のみをフィルタリング
        successful_results = [r for r in results if r.get('status') == 'classified']
        
        if not successful_results:
            logger.warning("No successful results to sync")
            return {"created": 0, "updated": 0, "errors": 0}
        
        # バッチでページを作成
        pages_data = []
        for result in successful_results:
            page_data = self._convert_to_notion_properties(result)
            pages_data.append(page_data)
        
        # 非同期でバッチ作成
        created_pages = await self.batch_processor.create_pages_batch(database_id, pages_data)
        
        # 結果を集計
        created_count = len([p for p in created_pages if p is not None])
        error_count = len(successful_results) - created_count
        
        logger.info(f"Notion sync completed: {created_count} created, {error_count} errors")
        
        return {
            "created": created_count,
            "updated": 0,  # 更新は現在未実装
            "errors": error_count
        }
    
    def _convert_to_notion_properties(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """結果をNotionプロパティに変換"""
        return {
            "タイトル": {
                "title": [{"text": {"content": result.get("summary", result.get("title", ""))}}]
            },
            "内容": {
                "rich_text": [{"text": {"content": result.get("content", "")}}]
            },
            "ステータス": {
                "select": {"name": result.get("status", "pending")}
            },
            "カテゴリ": {
                "select": {"name": result.get("category", "general")}
            },
            "信頼度": {
                "number": result.get("confidence", 0)
            },
            "処理日時": {
                "date": {"start": result.get('processed_at', datetime.now().isoformat())}
            }
        }

class AsyncInboxProcessor:
    """非同期INBOX処理クラス"""
    
    def __init__(self, notion_client: AsyncNotionClient, cache: NotionCache):
        self.notion_client = notion_client
        self.cache = cache
        self.classification_processor = AsyncClassificationProcessor(notion_client, cache)
    
    async def process_inbox_async(self, inbox_database_id: str, target_database_id: str) -> Dict[str, Any]:
        """INBOXを非同期で処理"""
        logger.info("Starting async inbox processing")
        
        # キャッシュからINBOXアイテムを取得を試行
        cached_items = await self.cache.get_database_pages(inbox_database_id)
        
        if cached_items:
            logger.info(f"Using cached inbox items: {len(cached_items)}")
            items = cached_items
        else:
            # INBOXアイテムを非同期で取得
            items = await self.notion_client.fetch_pages_async(inbox_database_id)
            
            # キャッシュに保存
            await self.cache.set_database_pages(inbox_database_id, items)
        
        if not items:
            logger.info("No items found in inbox")
            return {"processed": 0, "created": 0, "errors": 0}
        
        # 前処理：タイトルと内容の相互コピー
        preprocessed_items = []
        for item in items:
            preprocessed_item = await self._preprocess_inbox_item(item)
            if preprocessed_item:
                preprocessed_items.append(preprocessed_item)
        
        logger.info(f"Preprocessed {len(preprocessed_items)} items from {len(items)} total items")
        
        # 設定を読み込み
        config = load_config()
        
        # 非同期で分類処理
        results = await self.classification_processor.classify_items_async(preprocessed_items, config)
        
        # Notionに同期
        sync_results = await self.classification_processor.sync_to_notion_async(results, target_database_id)
        
        # 処理済みアイテムをINBOXからアーカイブ
        processed_item_ids = [r.get('id') for r in results if r.get('status') == 'classified']
        if processed_item_ids:
            await self._archive_processed_items_async(processed_item_ids)
        
        # キャッシュを無効化
        await self.cache.invalidate_database(inbox_database_id)
        
        logger.info(f"Inbox processing completed: {sync_results}")
        return sync_results
    
    async def _preprocess_inbox_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """INBOXアイテムの前処理：タイトルと内容の相互コピー"""
        properties = item.get('properties', {})
        
        # タイトル取得
        title_prop = properties.get('タイトル', {})
        title = ''.join([t.get('plain_text', '') for t in title_prop.get('title', [])])
        
        # 内容取得
        content_prop = properties.get('内容', {})
        content = ''.join([t.get('plain_text', '') for t in content_prop.get('rich_text', [])])
        
        updated = False
        
        # タイトルが空で内容がある場合：内容をタイトルにコピー
        if (not title or title == '(タイトルなし)' or not title.strip()) and content.strip():
            # Notionページを更新
            await self.notion_client.update_page(item['id'], {
                'タイトル': {'title': [{'text': {'content': content.strip()}}]}
            })
            updated = True
            logger.info(f"Copied content to title: {content[:30]}...")
        
        # 内容が空でタイトルがある場合：タイトルを内容にコピー
        elif title.strip() and (not content or not content.strip()):
            # Notionページを更新
            await self.notion_client.update_page(item['id'], {
                '内容': {'rich_text': [{'text': {'content': title.strip()}}]}
            })
            updated = True
            logger.info(f"Copied title to content: {title[:30]}...")
        
        # 更新された場合は新しいデータで返す
        if updated:
            # 更新されたプロパティで新しいアイテムを作成
            updated_item = item.copy()
            updated_item['properties'] = properties.copy()
            return updated_item
        
        return item
    
    async def _archive_processed_items_async(self, item_ids: List[str]) -> int:
        """処理済みアイテムをアーカイブ"""
        logger.info(f"Archiving {len(item_ids)} processed items")
        
        archived_count = await self.classification_processor.batch_processor.archive_pages_batch(item_ids)
        successful_archives = len([r for r in archived_count if r])
        
        logger.info(f"Archived {successful_archives} items")
        return successful_archives
