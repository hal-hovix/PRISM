"""
AI アシスタント機能APIエンドポイント
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import verify_api_key
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/assistant", tags=["ai_assistant"])

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

class AIAssistantClient:
    """AI アシスタントクライアント"""
    
    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
    
    def get_system_prompt(self) -> str:
        """システムプロンプトを取得"""
        return """あなたはPRISM（Personalized Recommendation and Intelligent System for Management）のAIアシスタントです。

あなたの役割：
1. ユーザーのタスク管理、習慣追跡、知識管理をサポート
2. 自然言語での質問に答える
3. 生産性向上のためのアドバイスを提供
4. データの分析と洞察を提供

利用可能なデータベース：
- Task: タスク管理
- ToDo: やることリスト
- Project: プロジェクト管理
- Habit: 習慣追跡
- Knowledge: 知識ベース
- Note: ノート
- INBOX: 受信箱

常に日本語で回答し、親切で実用的なアドバイスを提供してください。"""
    
    def get_user_context(self) -> Dict[str, Any]:
        """ユーザーのコンテキスト情報を取得"""
        try:
            context = {
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "databases": {}
            }
            
            # 各データベースの基本統計を取得
            for db_name, db_id in DATABASE_IDS.items():
                try:
                    stats = self._get_database_stats(db_id, db_name)
                    context["databases"][db_name] = stats
                except Exception as e:
                    logger.warning(f"Failed to get stats for {db_name}: {e}")
                    context["databases"][db_name] = {"error": str(e)}
            
            return context
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {"error": str(e)}
    
    def _get_database_stats(self, database_id: str, database_name: str) -> Dict[str, Any]:
        """データベースの統計情報を取得"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        try:
            response = requests.post(url, headers=self.notion_headers, json={})
            response.raise_for_status()
            data = response.json()
            
            total_items = len(data.get('results', []))
            
            # データベース別の詳細統計
            stats = {"total_items": total_items}
            
            if database_name in ["Task", "ToDo"]:
                completed = 0
                overdue = 0
                today = datetime.now().date()
                
                for page in data.get('results', []):
                    properties = page.get('properties', {})
                    
                    # 完了チェック
                    status = self._extract_select(properties.get('ステータス', {}))
                    if status and status.lower() in ['完了', 'completed', 'done']:
                        completed += 1
                    
                    # 期限切れチェック
                    due_date = self._extract_date(properties.get('期日', {}) or properties.get('実施日', {}))
                    if due_date:
                        try:
                            due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
                            if due_date_obj < today and status.lower() not in ['完了', 'completed', 'done']:
                                overdue += 1
                        except:
                            pass
                
                stats.update({
                    "completed": completed,
                    "overdue": overdue,
                    "completion_rate": (completed / total_items * 100) if total_items > 0 else 0
                })
            
            elif database_name == "Habit":
                completed_today = 0
                for page in data.get('results', []):
                    properties = page.get('properties', {})
                    completed = self._extract_checkbox(properties.get('完了', {}))
                    if completed:
                        completed_today += 1
                
                stats.update({
                    "completed_today": completed_today,
                    "completion_rate": (completed_today / total_items * 100) if total_items > 0 else 0
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats for {database_name}: {e}")
            return {"error": str(e)}
    
    def _extract_select(self, prop: Dict) -> str:
        """セレクトプロパティから値を抽出"""
        if not prop or prop.get('type') != 'select':
            return ""
        select_obj = prop.get('select')
        return select_obj.get('name', '') if select_obj else ""
    
    def _extract_date(self, prop: Dict) -> str:
        """日付プロパティから値を抽出"""
        if not prop or prop.get('type') != 'date':
            return ""
        date_obj = prop.get('date')
        return date_obj.get('start', '') if date_obj else ""
    
    def _extract_checkbox(self, prop: Dict) -> bool:
        """チェックボックスプロパティから値を抽出"""
        if not prop or prop.get('type') != 'checkbox':
            return False
        return prop.get('checkbox', False)
    
    def chat_with_assistant(self, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """AIアシスタントとチャット"""
        try:
            # ユーザーコンテキストを取得
            context = self.get_user_context()
            
            # 会話履歴を準備
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "system", "content": f"現在のコンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}"}
            ]
            
            # 会話履歴を追加
            if conversation_history:
                for msg in conversation_history[-10:]:  # 最新10件のみ
                    messages.append(msg)
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": message})
            
            # OpenAI APIを呼び出し
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                
                return {
                    "message": assistant_message,
                    "timestamp": datetime.now().isoformat(),
                    "context_used": context
                }
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return {
                    "message": "申し訳ございません。現在AIアシスタントが利用できません。しばらく時間をおいてから再度お試しください。",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"OpenAI API error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error in chat_with_assistant: {e}")
            return {
                "message": "申し訳ございません。エラーが発生しました。",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """生産性の洞察を取得"""
        try:
            context = self.get_user_context()
            
            # 洞察を生成するためのプロンプト
            prompt = f"""
以下のデータを分析して、生産性向上のための洞察を提供してください：

{json.dumps(context, ensure_ascii=False, indent=2)}

以下の観点から分析してください：
1. タスク完了率の分析
2. 習慣の達成状況
3. 期限切れタスクの傾向
4. 改善提案

簡潔で実用的なアドバイスを日本語で提供してください。
"""
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.5
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                insights = result["choices"][0]["message"]["content"]
                
                return {
                    "insights": insights,
                    "timestamp": datetime.now().isoformat(),
                    "data_analyzed": context
                }
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return {
                    "insights": "データの分析中にエラーが発生しました。",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"OpenAI API error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error in get_productivity_insights: {e}")
            return {
                "insights": "洞察の生成中にエラーが発生しました。",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# レスポンスモデル
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatResponse(BaseModel):
    message: str
    timestamp: str
    context_used: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ProductivityInsights(BaseModel):
    insights: str
    timestamp: str
    data_analyzed: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# グローバルクライアント
assistant_client = AIAssistantClient()

@router.post("/chat")
async def chat_with_assistant(
    message: str = Query(..., description="ユーザーのメッセージ"),
    conversation_history: str = Query(default="[]", description="会話履歴（JSON文字列）"),
    _=Depends(verify_api_key)
) -> ChatResponse:
    """AIアシスタントとチャット"""
    try:
        # 会話履歴をパース
        try:
            history = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history = []
        
        logger.info(f"Chat request: {message}")
        
        result = assistant_client.chat_with_assistant(message, history)
        
        return ChatResponse(
            message=result["message"],
            timestamp=result["timestamp"],
            context_used=result.get("context_used"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/insights")
async def get_productivity_insights(
    _=Depends(verify_api_key)
) -> ProductivityInsights:
    """生産性の洞察を取得"""
    try:
        logger.info("Getting productivity insights")
        
        result = assistant_client.get_productivity_insights()
        
        return ProductivityInsights(
            insights=result["insights"],
            timestamp=result["timestamp"],
            data_analyzed=result.get("data_analyzed"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in insights endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@router.get("/context")
async def get_user_context(
    _=Depends(verify_api_key)
) -> Dict[str, Any]:
    """ユーザーのコンテキスト情報を取得"""
    try:
        logger.info("Getting user context")
        
        context = assistant_client.get_user_context()
        
        return {
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in context endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@router.get("/test")
async def test_assistant(
    _=Depends(verify_api_key)
) -> Dict[str, Any]:
    """AIアシスタントのテスト"""
    try:
        logger.info("Testing AI assistant")
        
        # 簡単なテストメッセージ
        result = assistant_client.chat_with_assistant("こんにちは！PRISMについて教えてください。")
        
        return {
            "status": "success",
            "test_message": "こんにちは！PRISMについて教えてください。",
            "response": result["message"],
            "timestamp": result["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
