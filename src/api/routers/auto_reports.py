"""
自動レポート生成APIエンドポイント
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import verify_api_key
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["auto_reports"])

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

class ReportGenerator:
    """自動レポート生成器"""
    
    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
    
    def generate_weekly_report(self, start_date: datetime = None) -> Dict[str, Any]:
        """週次レポートを生成"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        
        end_date = start_date + timedelta(days=7)
        
        try:
            # 期間内のデータを取得
            data = self._get_period_data(start_date, end_date)
            
            # レポートを生成
            report = self._generate_report_content(data, "週次", start_date, end_date)
            
            return {
                "report_type": "weekly",
                "period": f"{start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}",
                "content": report,
                "generated_at": datetime.now().isoformat(),
                "data_summary": self._get_data_summary(data)
            }
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {
                "report_type": "weekly",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def generate_monthly_report(self, start_date: datetime = None) -> Dict[str, Any]:
        """月次レポートを生成"""
        if start_date is None:
            start_date = datetime.now().replace(day=1) - timedelta(days=30)
        
        end_date = start_date + timedelta(days=30)
        
        try:
            # 期間内のデータを取得
            data = self._get_period_data(start_date, end_date)
            
            # レポートを生成
            report = self._generate_report_content(data, "月次", start_date, end_date)
            
            return {
                "report_type": "monthly",
                "period": f"{start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}",
                "content": report,
                "generated_at": datetime.now().isoformat(),
                "data_summary": self._get_data_summary(data)
            }
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return {
                "report_type": "monthly",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def generate_custom_report(self, start_date: datetime, end_date: datetime, template: str = "standard") -> Dict[str, Any]:
        """カスタムレポートを生成"""
        try:
            # 期間内のデータを取得
            data = self._get_period_data(start_date, end_date)
            
            # レポートを生成
            report = self._generate_report_content(data, "カスタム", start_date, end_date, template)
            
            return {
                "report_type": "custom",
                "period": f"{start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}",
                "template": template,
                "content": report,
                "generated_at": datetime.now().isoformat(),
                "data_summary": self._get_data_summary(data)
            }
            
        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            return {
                "report_type": "custom",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def _get_period_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """期間内のデータを取得"""
        data = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "databases": {}
        }
        
        for db_name, db_id in DATABASE_IDS.items():
            try:
                db_data = self._get_database_data(db_id, db_name, start_date, end_date)
                data["databases"][db_name] = db_data
            except Exception as e:
                logger.warning(f"Failed to get data for {db_name}: {e}")
                data["databases"][db_name] = {"error": str(e)}
        
        return data
    
    def _get_database_data(self, database_id: str, database_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """データベースの期間内データを取得"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        try:
            response = requests.post(url, headers=self.notion_headers, json={})
            response.raise_for_status()
            data = response.json()
            
            items = data.get('results', [])
            
            # 期間内のアイテムをフィルタリング
            period_items = []
            for item in items:
                created_time = item.get('created_time', '')
                if created_time:
                    try:
                        item_date = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        if start_date <= item_date <= end_date:
                            period_items.append(item)
                    except:
                        pass
            
            # データベース別の統計
            stats = {
                "total_items": len(items),
                "period_items": len(period_items),
                "items": period_items
            }
            
            # データベース別の詳細統計
            if database_name in ["Task", "ToDo"]:
                completed = 0
                overdue = 0
                
                for item in period_items:
                    properties = item.get('properties', {})
                    
                    # 完了チェック
                    status = self._extract_select(properties.get('ステータス', {}))
                    if status and status.lower() in ['完了', 'completed', 'done']:
                        completed += 1
                    
                    # 期限切れチェック
                    due_date = self._extract_date(properties.get('期日', {}) or properties.get('実施日', {}))
                    if due_date:
                        try:
                            due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                            if due_date_obj < datetime.now() and status.lower() not in ['完了', 'completed', 'done']:
                                overdue += 1
                        except:
                            pass
                
                stats.update({
                    "completed": completed,
                    "overdue": overdue,
                    "completion_rate": (completed / len(period_items) * 100) if period_items else 0
                })
            
            elif database_name == "Habit":
                completed_today = 0
                for item in period_items:
                    properties = item.get('properties', {})
                    completed = self._extract_checkbox(properties.get('完了', {}))
                    if completed:
                        completed_today += 1
                
                stats.update({
                    "completed_today": completed_today,
                    "completion_rate": (completed_today / len(period_items) * 100) if period_items else 0
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database data for {database_name}: {e}")
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
    
    def _generate_report_content(self, data: Dict[str, Any], report_type: str, start_date: datetime, end_date: datetime, template: str = "standard") -> str:
        """レポートコンテンツを生成"""
        try:
            # レポート生成のためのプロンプト
            prompt = f"""
以下のデータを基に、{report_type}レポートを生成してください：

期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}

データ:
{json.dumps(data, ensure_ascii=False, indent=2)}

レポートの構成：
1. 期間サマリー
2. タスク管理の状況
3. 習慣の達成状況
4. 知識・ノートの成長
5. 改善提案
6. 次の期間の目標

簡潔で実用的なレポートを日本語で生成してください。
"""
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            request_data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "あなたは生産性分析の専門家です。データを分析して実用的なレポートを生成してください。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return f"レポート生成中にエラーが発生しました。API エラー: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error generating report content: {e}")
            return f"レポート生成中にエラーが発生しました: {str(e)}"
    
    def _get_data_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データサマリーを生成"""
        summary = {
            "total_databases": len(data.get("databases", {})),
            "period": data.get("period", {}),
            "database_stats": {}
        }
        
        for db_name, db_data in data.get("databases", {}).items():
            if "error" not in db_data:
                summary["database_stats"][db_name] = {
                    "total_items": db_data.get("total_items", 0),
                    "period_items": db_data.get("period_items", 0)
                }
        
        return summary

# レスポンスモデル
class ReportResponse(BaseModel):
    report_type: str
    period: str
    content: str
    generated_at: str
    data_summary: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    error: Optional[str] = None

# グローバル生成器
report_generator = ReportGenerator()

@router.get("/weekly")
async def get_weekly_report(
    start_date: str = Query(default=None, description="開始日 (YYYY-MM-DD)"),
    _=Depends(verify_api_key)
) -> ReportResponse:
    """週次レポートを生成"""
    try:
        logger.info("Generating weekly report")
        
        start_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        result = report_generator.generate_weekly_report(start_dt)
        
        return ReportResponse(
            report_type=result["report_type"],
            period=result["period"],
            content=result["content"],
            generated_at=result["generated_at"],
            data_summary=result.get("data_summary"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in weekly report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Weekly report generation failed: {str(e)}")

@router.get("/monthly")
async def get_monthly_report(
    start_date: str = Query(default=None, description="開始日 (YYYY-MM-DD)"),
    _=Depends(verify_api_key)
) -> ReportResponse:
    """月次レポートを生成"""
    try:
        logger.info("Generating monthly report")
        
        start_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        result = report_generator.generate_monthly_report(start_dt)
        
        return ReportResponse(
            report_type=result["report_type"],
            period=result["period"],
            content=result["content"],
            generated_at=result["generated_at"],
            data_summary=result.get("data_summary"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in monthly report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Monthly report generation failed: {str(e)}")

@router.get("/custom")
async def get_custom_report(
    start_date: str = Query(..., description="開始日 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="終了日 (YYYY-MM-DD)"),
    template: str = Query(default="standard", description="レポートテンプレート"),
    _=Depends(verify_api_key)
) -> ReportResponse:
    """カスタムレポートを生成"""
    try:
        logger.info("Generating custom report")
        
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        if start_dt >= end_dt:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        result = report_generator.generate_custom_report(start_dt, end_dt, template)
        
        return ReportResponse(
            report_type=result["report_type"],
            period=result["period"],
            content=result["content"],
            generated_at=result["generated_at"],
            data_summary=result.get("data_summary"),
            template=result.get("template"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in custom report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Custom report generation failed: {str(e)}")

@router.get("/templates")
async def get_report_templates(
    _=Depends(verify_api_key)
) -> Dict[str, Any]:
    """利用可能なレポートテンプレートを取得"""
    return {
        "templates": {
            "standard": {
                "name": "標準レポート",
                "description": "基本的な生産性分析レポート",
                "sections": ["期間サマリー", "タスク管理", "習慣達成", "知識成長", "改善提案"]
            },
            "detailed": {
                "name": "詳細レポート",
                "description": "詳細な分析と洞察を含むレポート",
                "sections": ["期間サマリー", "詳細分析", "トレンド分析", "パフォーマンス指標", "改善提案", "次の目標"]
            },
            "summary": {
                "name": "サマリーレポート",
                "description": "簡潔な要約レポート",
                "sections": ["主要指標", "完了状況", "次のアクション"]
            }
        },
        "available_periods": {
            "weekly": "週次レポート",
            "monthly": "月次レポート",
            "custom": "カスタム期間レポート"
        }
    }

@router.get("/test")
async def test_report_generation(
    _=Depends(verify_api_key)
) -> Dict[str, Any]:
    """レポート生成のテスト"""
    try:
        logger.info("Testing report generation")
        
        # 簡単な週次レポートを生成
        result = report_generator.generate_weekly_report()
        
        return {
            "status": "success",
            "test_type": "weekly_report",
            "period": result.get("period", "N/A"),
            "content_length": len(result.get("content", "")),
            "generated_at": result.get("generated_at"),
            "has_error": "error" in result
        }
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
