#!/usr/bin/env python3
"""
Notion MCP Server
Model Context Protocol (MCP) に準拠したNotion APIサーバー
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import httpx
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class NotionMCPServer:
    """Notion MCP Server"""
    
    def __init__(self):
        self.notion_client = None
        self.tools = {
            "search_databases": {
                "name": "search_databases",
                "description": "Notionのデータベースを検索します",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "query_database": {
                "name": "query_database",
                "description": "指定されたデータベースをクエリします",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "データベースID"
                        },
                        "filter": {
                            "type": "object",
                            "description": "フィルター条件（オプション）"
                        }
                    },
                    "required": ["database_id"]
                }
            },
            "get_page": {
                "name": "get_page",
                "description": "指定されたページの詳細を取得します",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ページID"
                        }
                    },
                    "required": ["page_id"]
                }
            },
            "create_page": {
                "name": "create_page",
                "description": "新しいページを作成します",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "parent": {
                            "type": "object",
                            "description": "親オブジェクト（データベースIDなど）"
                        },
                        "properties": {
                            "type": "object",
                            "description": "ページのプロパティ"
                        }
                    },
                    "required": ["parent", "properties"]
                }
            },
            "update_page": {
                "name": "update_page",
                "description": "既存のページを更新します",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ページID"
                        },
                        "properties": {
                            "type": "object",
                            "description": "更新するプロパティ"
                        }
                    },
                    "required": ["page_id", "properties"]
                }
            }
        }
    
    async def initialize(self):
        """サーバーを初期化"""
        api_key = os.getenv("NOTION_API_KEY")
        if not api_key:
            raise ValueError("NOTION_API_KEY environment variable is required")
        
        self.notion_client = NotionMCPClient(api_key)
        logger.info("Notion MCP Server initialized")
    
    async def handle_request(self, request: Dict) -> Dict:
        """MCPリクエストを処理"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "notion-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = await self.call_tool(tool_name, arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """ツールを実行"""
        if not self.notion_client:
            raise RuntimeError("Server not initialized")
        
        if tool_name == "search_databases":
            return await self.notion_client.search_databases()
        
        elif tool_name == "query_database":
            database_id = arguments.get("database_id")
            filter_obj = arguments.get("filter")
            return await self.notion_client.query_database(database_id, filter_obj)
        
        elif tool_name == "get_page":
            page_id = arguments.get("page_id")
            return await self.notion_client.get_page(page_id)
        
        elif tool_name == "create_page":
            parent = arguments.get("parent")
            properties = arguments.get("properties")
            return await self.notion_client.create_page(parent, properties)
        
        elif tool_name == "update_page":
            page_id = arguments.get("page_id")
            properties = arguments.get("properties")
            return await self.notion_client.update_page(page_id, properties)
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

async def main():
    """メイン関数"""
    server = NotionMCPServer()
    await server.initialize()
    
    logger.info("Notion MCP Server started")
    logger.info("Listening for MCP requests on stdin/stdout")
    
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error processing request: {e}")
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

