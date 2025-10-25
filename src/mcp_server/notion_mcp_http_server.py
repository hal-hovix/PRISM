#!/usr/bin/env python3
"""
Notion MCP HTTP Server
ChatGPT連携用のHTTP APIサーバー
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="Notion MCP HTTP Server",
    description="ChatGPT連携用のNotion MCP HTTP API",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NotionMCPClient:
    """Notion API クライアント"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def search_databases(self) -> List[Dict]:
        """データベースを検索"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json={"filter": {"property": "object", "value": "database"}}
            )
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def query_database(self, database_id: str, filter_obj: Optional[Dict] = None) -> List[Dict]:
        """データベースをクエリ"""
        async with httpx.AsyncClient() as client:
            payload = {}
            if filter_obj:
                payload["filter"] = filter_obj
            
            response = await client.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def get_page(self, page_id: str) -> Dict:
        """ページを取得"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_page(self, parent: Dict, properties: Dict) -> Dict:
        """ページを作成"""
        async with httpx.AsyncClient() as client:
            payload = {
                "parent": parent,
                "properties": properties
            }
            response = await client.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def update_page(self, page_id: str, properties: Dict) -> Dict:
        """ページを更新"""
        async with httpx.AsyncClient() as client:
            payload = {"properties": properties}
            response = await client.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

# グローバルクライアント
notion_client = None

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    global notion_client
    
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        raise ValueError("NOTION_API_KEY environment variable is required")
    
    notion_client = NotionMCPClient(api_key)
    logger.info("Notion MCP HTTP Server started")

# Pydanticモデル
class DatabaseQueryRequest(BaseModel):
    database_id: str
    filter: Optional[Dict] = None

class PageCreateRequest(BaseModel):
    parent: Dict
    properties: Dict

class PageUpdateRequest(BaseModel):
    page_id: str
    properties: Dict

# API エンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Notion MCP HTTP Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/tools")
async def list_tools():
    """利用可能なツール一覧"""
    return {
        "tools": [
            {
                "name": "search_databases",
                "description": "Notionのデータベースを検索します",
                "method": "GET",
                "endpoint": "/tools/search_databases"
            },
            {
                "name": "query_database",
                "description": "指定されたデータベースをクエリします",
                "method": "POST",
                "endpoint": "/tools/query_database"
            },
            {
                "name": "get_page",
                "description": "指定されたページの詳細を取得します",
                "method": "GET",
                "endpoint": "/tools/get_page/{page_id}"
            },
            {
                "name": "create_page",
                "description": "新しいページを作成します",
                "method": "POST",
                "endpoint": "/tools/create_page"
            },
            {
                "name": "update_page",
                "description": "既存のページを更新します",
                "method": "PUT",
                "endpoint": "/tools/update_page"
            }
        ]
    }

@app.get("/tools/search_databases")
async def search_databases():
    """データベースを検索"""
    try:
        result = await notion_client.search_databases()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error searching databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/query_database")
async def query_database(request: DatabaseQueryRequest):
    """データベースをクエリ"""
    try:
        result = await notion_client.query_database(request.database_id, request.filter)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/get_page/{page_id}")
async def get_page(page_id: str):
    """ページを取得"""
    try:
        result = await notion_client.get_page(page_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error getting page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/create_page")
async def create_page(request: PageCreateRequest):
    """ページを作成"""
    try:
        result = await notion_client.create_page(request.parent, request.properties)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error creating page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/tools/update_page")
async def update_page(request: PageUpdateRequest):
    """ページを更新"""
    try:
        result = await notion_client.update_page(request.page_id, request.properties)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error updating page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ChatGPT連携用のエンドポイント
@app.post("/chatgpt/query")
async def chatgpt_query(query: Dict[str, Any]):
    """ChatGPTからの問い合わせを処理"""
    try:
        query_type = query.get("type")
        params = query.get("params", {})
        
        if query_type == "search_databases":
            result = await notion_client.search_databases()
        elif query_type == "query_database":
            result = await notion_client.query_database(
                params.get("database_id"), 
                params.get("filter")
            )
        elif query_type == "get_page":
            result = await notion_client.get_page(params.get("page_id"))
        elif query_type == "create_page":
            result = await notion_client.create_page(
                params.get("parent"), 
                params.get("properties")
            )
        elif query_type == "update_page":
            result = await notion_client.update_page(
                params.get("page_id"), 
                params.get("properties")
            )
        else:
            raise ValueError(f"Unknown query type: {query_type}")
        
        return {
            "success": True,
            "type": query_type,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing ChatGPT query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8062)
