"""
セマンティック検索APIエンドポイント
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from ..core.security import verify_api_key
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["semantic_search"])

# OpenAI API設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = "2022-06-28"

DATABASE_IDS = {
    "INBOX": "2935fbef-07e2-8008-bea4-d40152540791",
    "Task": "2935fbef-07e2-8074-bdf8-f9c06755f45a",
    "ToDo": "2935fbef-07e2-80bb-a0b3-cd8bac76fa17",
    "Project": "2935fbef-07e2-807f-8de4-daf009cc772e",
    "Habit": "2935fbef-07e2-80af-8596-ee5346044ad1",
    "Knowledge": "2935fbef-07e2-808a-8d27-cfbc1a5fcf25",
    "Note": "2935fbef-07e2-8029-9886-c539d6ed4284"
}

class SemanticSearchClient:
    """セマンティック検索クライアント"""
    
    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
    
    def generate_search_embeddings(self, query: str) -> Optional[List[float]]:
        """クエリから埋め込みベクトルを生成"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-3-small",
                "input": query
            }
            
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def expand_query_semantically(self, query: str) -> List[str]:
        """クエリを意味的に拡張"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
以下の検索クエリを意味的に拡張して、関連するキーワードや同義語を生成してください。
元のクエリ: "{query}"

以下の形式で、関連するキーワードを5-10個生成してください：
- 同義語
- 関連する概念
- より具体的な用語
- より一般的な用語

JSON配列形式で返してください：
["キーワード1", "キーワード2", "キーワード3", ...]
"""
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "あなたは検索クエリを意味的に拡張する専門家です。JSON配列形式で関連キーワードを返してください。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # JSON配列をパース
                try:
                    # コードブロックを除去
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    
                    keywords = json.loads(content)
                    if isinstance(keywords, list):
                        return keywords[:10]  # 最大10個
                except json.JSONDecodeError:
                    # JSONパースに失敗した場合、テキストからキーワードを抽出
                    keywords = [word.strip().strip('"\'') for word in content.split(',')]
                    return keywords[:10]
                
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error expanding query: {e}")
        
        # フォールバック: 基本的なキーワード分割
        return [query] + query.split()
    
    def search_notion_content(self, keywords: List[str], database_types: List[str] = None) -> List[Dict]:
        """Notionコンテンツを検索"""
        if database_types is None:
            database_types = ["Task", "ToDo", "Knowledge", "Note"]
        
        all_results = []
        
        for db_type in database_types:
            if db_type not in DATABASE_IDS:
                continue
                
            try:
                results = self._search_database(DATABASE_IDS[db_type], keywords, db_type)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error searching {db_type}: {e}")
        
        return all_results
    
    def _search_database(self, database_id: str, keywords: List[str], database_name: str) -> List[Dict]:
        """特定のデータベースを検索"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        results = []
        
        # ページネーション対応
        has_more = True
        start_cursor = None
        
        while has_more:
            query_data = {}
            if start_cursor:
                query_data["start_cursor"] = start_cursor
            
            try:
                response = requests.post(url, headers=self.notion_headers, json=query_data)
                response.raise_for_status()
                data = response.json()
                
                for page in data.get('results', []):
                    item = self._extract_searchable_content(page, database_name)
                    if item:
                        # キーワードマッチング
                        relevance_score = self._calculate_relevance_score(item, keywords)
                        if relevance_score > 0:
                            item['relevance_score'] = relevance_score
                            item['database'] = database_name
                            results.append(item)
                
                has_more = data.get('has_more', False)
                start_cursor = data.get('next_cursor')
                
            except Exception as e:
                logger.error(f"Error querying {database_name}: {e}")
                break
        
        return results
    
    def _extract_searchable_content(self, page: Dict, database_name: str) -> Optional[Dict]:
        """ページから検索可能なコンテンツを抽出"""
        properties = page.get('properties', {})
        
        # 共通データ
        item = {
            'id': page['id'],
            'created_time': page.get('created_time', ''),
            'last_edited_time': page.get('last_edited_time', ''),
            'database': database_name
        }
        
        # データベース別のコンテンツ抽出
        if database_name == "Task":
            title = self._extract_title(properties.get('タスク名', {}))
            content = self._extract_rich_text(properties.get('メモ', {}))
        elif database_name == "ToDo":
            title = self._extract_title(properties.get('ToDo名', {}))
            content = self._extract_rich_text(properties.get('メモ', {}))
        elif database_name == "Knowledge":
            title = self._extract_title(properties.get('タイトル', {}))
            content = self._extract_rich_text(properties.get('要約', {}))
        elif database_name == "Note":
            title = self._extract_title(properties.get('タイトル', {}))
            content = self._extract_rich_text(properties.get('内容', {}))
        else:
            return None
        
        if not title and not content:
            return None
        
        item.update({
            'title': title,
            'content': content,
            'searchable_text': f"{title} {content}".strip()
        })
        
        return item
    
    def _extract_title(self, prop: Dict) -> str:
        """タイトルプロパティからテキストを抽出"""
        if not prop or prop.get('type') != 'title':
            return ""
        title_list = prop.get('title', [])
        return ''.join([t.get('plain_text', '') for t in title_list])
    
    def _extract_rich_text(self, prop: Dict) -> str:
        """リッチテキストプロパティからテキストを抽出"""
        if not prop or prop.get('type') != 'rich_text':
            return ""
        rich_text_list = prop.get('rich_text', [])
        return ''.join([t.get('plain_text', '') for t in rich_text_list])
    
    def _calculate_relevance_score(self, item: Dict, keywords: List[str]) -> float:
        """関連度スコアを計算"""
        searchable_text = item.get('searchable_text', '').lower()
        if not searchable_text:
            return 0.0
        
        score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 完全一致（高スコア）
            if keyword_lower in searchable_text:
                score += 2.0
                
                # タイトルでの一致（より高スコア）
                title = item.get('title', '').lower()
                if keyword_lower in title:
                    score += 1.0
            
            # 部分一致（中スコア）
            words = searchable_text.split()
            for word in words:
                if keyword_lower in word or word in keyword_lower:
                    score += 0.5
        
        # 正規化（0-1の範囲）
        max_possible_score = len(keywords) * 3.0
        return min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
    
    def get_related_items(self, item_id: str, limit: int = 5) -> List[Dict]:
        """関連アイテムを取得"""
        try:
            # アイテムの詳細を取得
            url = f"https://api.notion.com/v1/pages/{item_id}"
            response = requests.get(url, headers=self.notion_headers)
            response.raise_for_status()
            
            page = response.json()
            properties = page.get('properties', {})
            
            # タイトルとコンテンツを抽出
            title = ""
            content = ""
            
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title = self._extract_title(prop_data)
                elif prop_data.get('type') == 'rich_text':
                    content = self._extract_rich_text(prop_data)
            
            if not title and not content:
                return []
            
            # 関連キーワードを生成
            search_text = f"{title} {content}".strip()
            keywords = self.expand_query_semantically(search_text)
            
            # 関連アイテムを検索
            related_items = self.search_notion_content(keywords)
            
            # 自分自身を除外
            related_items = [item for item in related_items if item['id'] != item_id]
            
            # 関連度でソートして上位を返す
            related_items.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return related_items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting related items: {e}")
            return []

# レスポンスモデル
class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    database: str
    relevance_score: float
    created_time: str
    last_edited_time: str

class SemanticSearchResponse(BaseModel):
    query: str
    expanded_keywords: List[str]
    results: List[SearchResult]
    total_count: int
    search_time_ms: int

class RelatedItemsResponse(BaseModel):
    item_id: str
    related_items: List[SearchResult]
    total_count: int

# グローバルクライアント
semantic_client = SemanticSearchClient()

@router.post("/semantic")
async def semantic_search(
    query: str = Query(..., description="検索クエリ"),
    database_types: str = Query(default="Task,ToDo,Knowledge,Note", description="検索対象データベース（カンマ区切り）"),
    limit: int = Query(default=20, description="結果の最大数"),
    _=Depends(verify_api_key)
) -> SemanticSearchResponse:
    """セマンティック検索を実行"""
    start_time = datetime.now()
    
    try:
        logger.info(f"Semantic search started for query: {query}")
        
        # クエリを意味的に拡張
        expanded_keywords = semantic_client.expand_query_semantically(query)
        logger.info(f"Expanded keywords: {expanded_keywords}")
        
        # データベースタイプを解析
        db_types = [db.strip() for db in database_types.split(',') if db.strip()]
        
        # Notionコンテンツを検索
        search_results = semantic_client.search_notion_content(expanded_keywords, db_types)
        
        # 関連度でソート
        search_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # 制限を適用
        search_results = search_results[:limit]
        
        # レスポンス形式に変換
        results = []
        for item in search_results:
            results.append(SearchResult(
                id=item['id'],
                title=item.get('title', ''),
                content=item.get('content', ''),
                database=item.get('database', ''),
                relevance_score=item.get('relevance_score', 0.0),
                created_time=item.get('created_time', ''),
                last_edited_time=item.get('last_edited_time', '')
            ))
        
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"Semantic search completed: {len(results)} results in {search_time_ms}ms")
        
        return SemanticSearchResponse(
            query=query,
            expanded_keywords=expanded_keywords,
            results=results,
            total_count=len(results),
            search_time_ms=search_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

@router.get("/related/{item_id}")
async def get_related_items(
    item_id: str,
    limit: int = Query(default=5, description="関連アイテムの最大数"),
    _=Depends(verify_api_key)
) -> RelatedItemsResponse:
    """指定されたアイテムの関連アイテムを取得"""
    try:
        logger.info(f"Getting related items for: {item_id}")
        
        related_items = semantic_client.get_related_items(item_id, limit)
        
        # レスポンス形式に変換
        results = []
        for item in related_items:
            results.append(SearchResult(
                id=item['id'],
                title=item.get('title', ''),
                content=item.get('content', ''),
                database=item.get('database', ''),
                relevance_score=item.get('relevance_score', 0.0),
                created_time=item.get('created_time', ''),
                last_edited_time=item.get('last_edited_time', '')
            ))
        
        logger.info(f"Found {len(results)} related items")
        
        return RelatedItemsResponse(
            item_id=item_id,
            related_items=results,
            total_count=len(results)
        )
        
    except Exception as e:
        logger.error(f"Error getting related items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get related items: {str(e)}")

@router.get("/suggest")
async def get_search_suggestions(
    query: str = Query(..., description="部分的な検索クエリ"),
    _=Depends(verify_api_key)
) -> Dict[str, Any]:
    """検索候補を取得"""
    try:
        logger.info(f"Getting search suggestions for: {query}")
        
        # クエリを意味的に拡張
        suggestions = semantic_client.expand_query_semantically(query)
        
        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search suggestions: {str(e)}")
