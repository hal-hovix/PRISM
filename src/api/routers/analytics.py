"""
生産性分析APIエンドポイント
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import verify_api_key
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Notion API設定
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

class NotionAnalyticsClient:
    """Notion分析用クライアント"""
    
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
    
    def get_database_items(self, database_id: str, database_name: str) -> List[Dict]:
        """データベースの全アイテムを取得"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        items = []
        has_more = True
        start_cursor = None
        
        while has_more:
            query_data = {}
            if start_cursor:
                query_data["start_cursor"] = start_cursor
            
            try:
                response = requests.post(url, headers=self.headers, json=query_data)
                response.raise_for_status()
                data = response.json()
                
                for page in data.get('results', []):
                    item = self._extract_item_data(page, database_name)
                    items.append(item)
                
                has_more = data.get('has_more', False)
                start_cursor = data.get('next_cursor')
                
            except Exception as e:
                logger.error(f"Error fetching {database_name}: {e}")
                break
        
        return items
    
    def _extract_item_data(self, page: Dict, database_name: str) -> Dict:
        """ページから分析用データを抽出"""
        properties = page.get('properties', {})
        
        # 共通データ
        item = {
            'id': page['id'],
            'database': database_name,
            'created_time': page.get('created_time', ''),
            'last_edited_time': page.get('last_edited_time', ''),
        }
        
        # データベース別のデータ抽出
        if database_name == "Task":
            item.update({
                'title': self._extract_title(properties.get('タスク名', {})),
                'status': self._extract_select(properties.get('ステータス', {})),
                'priority': self._extract_select(properties.get('重要度', {})),
                'urgency': self._extract_select(properties.get('緊急度', {})),
                'due_date': self._extract_date(properties.get('期日', {})),
                'created_date': self._extract_date(properties.get('作成日', {})),
                'estimated_time': self._extract_number(properties.get('所要時間', {})),
            })
        elif database_name == "ToDo":
            item.update({
                'title': self._extract_title(properties.get('ToDo名', {})),
                'status': self._extract_select(properties.get('ステータス', {})),
                'priority': self._extract_number(properties.get('優先度', {})),
                'due_date': self._extract_date(properties.get('実施日', {})),
                'reminder': self._extract_checkbox(properties.get('リマインダー', {})),
            })
        elif database_name == "Habit":
            item.update({
                'title': self._extract_title(properties.get('習慣名', {})),
                'completed': self._extract_checkbox(properties.get('完了', {})),
                'execution_date': self._extract_date(properties.get('実行日', {})),
                'frequency': self._extract_select(properties.get('頻度', {})),
                'category': self._extract_select(properties.get('カテゴリ', {})),
            })
        elif database_name == "Knowledge":
            item.update({
                'title': self._extract_title(properties.get('タイトル', {})),
                'category': self._extract_select(properties.get('カテゴリ', {})),
                'tags': self._extract_multi_select(properties.get('タグ', {})),
                'registered_date': self._extract_date(properties.get('登録日', {})),
            })
        elif database_name == "Note":
            item.update({
                'title': self._extract_title(properties.get('タイトル', {})),
                'type': self._extract_select(properties.get('種類', {})),
                'status': self._extract_select(properties.get('状態', {})),
                'date': self._extract_date(properties.get('日付', {})),
                'tags': self._extract_multi_select(properties.get('タグ', {})),
            })
        elif database_name == "INBOX":
            item.update({
                'title': self._extract_title(properties.get('タイトル', {})),
                'status': self._extract_select(properties.get('状態', {})),
                'priority': self._extract_select(properties.get('重要度', {})),
                'urgency': self._extract_select(properties.get('緊急度', {})),
                'due_date': self._extract_date(properties.get('期限', {})),
                'category': self._extract_multi_select(properties.get('カテゴリ', {})),
                'type': self._extract_select(properties.get('タイプ', {})),
            })
        
        return item
    
    def _extract_title(self, prop: Dict) -> str:
        """タイトルプロパティからテキストを抽出"""
        if not prop or prop.get('type') != 'title':
            return ""
        title_list = prop.get('title', [])
        return ''.join([t.get('plain_text', '') for t in title_list])
    
    def _extract_select(self, prop: Dict) -> str:
        """セレクトプロパティから値を抽出"""
        if not prop or prop.get('type') != 'select':
            return ""
        select_obj = prop.get('select')
        return select_obj.get('name', '') if select_obj else ""
    
    def _extract_multi_select(self, prop: Dict) -> List[str]:
        """マルチセレクトプロパティから値を抽出"""
        if not prop or prop.get('type') != 'multi_select':
            return []
        multi_select_list = prop.get('multi_select', [])
        return [item.get('name', '') for item in multi_select_list if item.get('name')]
    
    def _extract_date(self, prop: Dict) -> str:
        """日付プロパティから値を抽出"""
        if not prop or prop.get('type') != 'date':
            return ""
        date_obj = prop.get('date')
        return date_obj.get('start', '') if date_obj else ""
    
    def _extract_number(self, prop: Dict) -> float:
        """数値プロパティから値を抽出"""
        if not prop or prop.get('type') != 'number':
            return 0.0
        return prop.get('number', 0.0)
    
    def _extract_checkbox(self, prop: Dict) -> bool:
        """チェックボックスプロパティから値を抽出"""
        if not prop or prop.get('type') != 'checkbox':
            return False
        return prop.get('checkbox', False)

# 分析用レスポンスモデル
class TaskCompletionStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    overdue_tasks: int
    high_priority_tasks: int

class CategoryDistribution(BaseModel):
    category: str
    count: int
    percentage: float

class TimeAnalysis(BaseModel):
    period: str
    tasks_created: int
    tasks_completed: int
    completion_rate: float

class ProductivityOverview(BaseModel):
    task_stats: TaskCompletionStats
    category_distribution: List[CategoryDistribution]
    time_analysis: List[TimeAnalysis]
    habit_completion_rate: float
    knowledge_growth: int

# グローバルクライアント
analytics_client = NotionAnalyticsClient()

@router.get("/test")
async def test_analytics(_=Depends(verify_api_key)):
    """テスト用エンドポイント"""
    try:
        # シンプルなテスト
        task_items = analytics_client.get_database_items(DATABASE_IDS["Task"], "Task")
        logger.info(f"Task items count: {len(task_items)}")
        
        if task_items:
            logger.info(f"First task: {task_items[0]}")
        
        return {
            "status": "success",
            "task_count": len(task_items),
            "message": "Test completed successfully"
        }
    except Exception as e:
        logger.error(f"Test error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/overview")
async def get_productivity_overview(
    days: int = Query(default=30, description="分析期間（日数）"),
    _=Depends(verify_api_key)
) -> ProductivityOverview:
    """生産性の概要を取得"""
    try:
        # 期間の計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 各データベースからデータを取得
        logger.info("Fetching data from Notion databases...")
        task_items = analytics_client.get_database_items(DATABASE_IDS["Task"], "Task")
        logger.info(f"Task items: {len(task_items)}")
        
        todo_items = analytics_client.get_database_items(DATABASE_IDS["ToDo"], "ToDo")
        logger.info(f"ToDo items: {len(todo_items)}")
        
        habit_items = analytics_client.get_database_items(DATABASE_IDS["Habit"], "Habit")
        logger.info(f"Habit items: {len(habit_items)}")
        
        knowledge_items = analytics_client.get_database_items(DATABASE_IDS["Knowledge"], "Knowledge")
        logger.info(f"Knowledge items: {len(knowledge_items)}")
        
        # タスク統計の計算
        logger.info("Calculating task stats...")
        task_stats = _calculate_task_stats(task_items, todo_items)
        
        # カテゴリ分布の計算
        logger.info("Calculating category distribution...")
        category_distribution = _calculate_category_distribution(task_items, todo_items)
        
        # 時間分析の計算
        logger.info("Calculating time analysis...")
        time_analysis = _calculate_time_analysis(task_items, todo_items, days)
        
        # 習慣完了率の計算
        logger.info("Calculating habit completion rate...")
        habit_completion_rate = _calculate_habit_completion_rate(habit_items, days)
        
        # 知識成長の計算
        logger.info("Calculating knowledge growth...")
        knowledge_growth = _calculate_knowledge_growth(knowledge_items, days)
        
        return ProductivityOverview(
            task_stats=task_stats,
            category_distribution=category_distribution,
            time_analysis=time_analysis,
            habit_completion_rate=habit_completion_rate,
            knowledge_growth=knowledge_growth
        )
        
    except Exception as e:
        logger.error(f"Error in productivity overview: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        raise HTTPException(status_code=500, detail=f"Failed to generate productivity overview: {str(e)}")

@router.get("/task-completion")
async def get_task_completion_stats(
    days: int = Query(default=30, description="分析期間（日数）"),
    _=Depends(verify_api_key)
) -> TaskCompletionStats:
    """タスク完了統計を取得"""
    try:
        task_items = analytics_client.get_database_items(DATABASE_IDS["Task"], "Task")
        todo_items = analytics_client.get_database_items(DATABASE_IDS["ToDo"], "ToDo")
        
        return _calculate_task_stats(task_items, todo_items)
        
    except Exception as e:
        logger.error(f"Error in task completion stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate task completion stats: {str(e)}")

@router.get("/category-distribution")
async def get_category_distribution(
    _=Depends(verify_api_key)
) -> List[CategoryDistribution]:
    """カテゴリ分布を取得"""
    try:
        task_items = analytics_client.get_database_items(DATABASE_IDS["Task"], "Task")
        todo_items = analytics_client.get_database_items(DATABASE_IDS["ToDo"], "ToDo")
        
        return _calculate_category_distribution(task_items, todo_items)
        
    except Exception as e:
        logger.error(f"Error in category distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate category distribution: {str(e)}")

def _calculate_task_stats(task_items: List[Dict], todo_items: List[Dict]) -> TaskCompletionStats:
    """タスク統計を計算"""
    all_tasks = task_items + todo_items
    
    total_tasks = len(all_tasks)
    
    # 完了タスクの計算（安全な方法）
    completed_tasks = 0
    for task in all_tasks:
        status = task.get('status')
        if status and isinstance(status, str) and status.lower() in ['完了', 'completed', 'done']:
            completed_tasks += 1
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # 期限切れタスクの計算
    today = datetime.now().date()
    overdue_tasks = 0
    high_priority_tasks = 0
    
    for task in all_tasks:
        # 期限切れチェック
        due_date_str = task.get('due_date', '')
        if due_date_str and isinstance(due_date_str, str):
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                status = task.get('status', '')
                if due_date < today and (not status or not isinstance(status, str) or status.lower() not in ['完了', 'completed', 'done']):
                    overdue_tasks += 1
            except:
                pass
        
        # 優先度チェック
        priority = task.get('priority', '')
        urgency = task.get('urgency', '')
        if (priority and isinstance(priority, str) and priority.lower() in ['高', 'high', 'urgent']) or \
           (urgency and isinstance(urgency, str) and urgency.lower() in ['高', 'high', 'urgent']):
            high_priority_tasks += 1
    
    return TaskCompletionStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate=round(completion_rate, 2),
        overdue_tasks=overdue_tasks,
        high_priority_tasks=high_priority_tasks
    )

def _calculate_category_distribution(task_items: List[Dict], todo_items: List[Dict]) -> List[CategoryDistribution]:
    """カテゴリ分布を計算"""
    all_tasks = task_items + todo_items
    
    # カテゴリの集計
    category_counts = {}
    for task in all_tasks:
        categories = task.get('category', [])
        if isinstance(categories, list):
            for category in categories:
                if category and isinstance(category, str):
                    category_counts[category] = category_counts.get(category, 0) + 1
        elif isinstance(categories, str) and categories:
            category_counts[categories] = category_counts.get(categories, 0) + 1
    
    total_tasks = len(all_tasks)
    
    # パーセンテージを計算してソート
    distribution = []
    for category, count in category_counts.items():
        percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
        distribution.append(CategoryDistribution(
            category=category,
            count=count,
            percentage=round(percentage, 2)
        ))
    
    return sorted(distribution, key=lambda x: x.count, reverse=True)

def _calculate_time_analysis(task_items: List[Dict], todo_items: List[Dict], days: int) -> List[TimeAnalysis]:
    """時間分析を計算"""
    all_tasks = task_items + todo_items
    
    # 日別の分析
    daily_stats = {}
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        daily_stats[date_str] = {'created': 0, 'completed': 0}
    
    for task in all_tasks:
        # 作成日の分析
        created_time = task.get('created_time', '')
        if created_time:
            try:
                created_date = datetime.fromisoformat(created_time.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                if created_date in daily_stats:
                    daily_stats[created_date]['created'] += 1
            except:
                pass
        
        # 完了日の分析（ステータスが完了の場合）
        status = task.get('status', '')
        if status and isinstance(status, str) and status.lower() in ['完了', 'completed', 'done']:
            last_edited = task.get('last_edited_time', '')
            if last_edited:
                try:
                    completed_date = datetime.fromisoformat(last_edited.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    if completed_date in daily_stats:
                        daily_stats[completed_date]['completed'] += 1
                except:
                    pass
    
    # 結果の生成
    time_analysis = []
    for date_str, stats in daily_stats.items():
        completion_rate = (stats['completed'] / stats['created'] * 100) if stats['created'] > 0 else 0
        time_analysis.append(TimeAnalysis(
            period=date_str,
            tasks_created=stats['created'],
            tasks_completed=stats['completed'],
            completion_rate=round(completion_rate, 2)
        ))
    
    return sorted(time_analysis, key=lambda x: x.period, reverse=True)

def _calculate_habit_completion_rate(habit_items: List[Dict], days: int) -> float:
    """習慣完了率を計算"""
    if not habit_items:
        return 0.0
    
    # 過去N日間の習慣実行を分析
    recent_habits = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for habit in habit_items:
        execution_date_str = habit.get('execution_date', '')
        if execution_date_str:
            try:
                execution_date = datetime.fromisoformat(execution_date_str.replace('Z', '+00:00'))
                if execution_date >= cutoff_date:
                    recent_habits.append(habit)
            except:
                pass
    
    if not recent_habits:
        return 0.0
    
    completed_habits = len([h for h in recent_habits if h.get('completed', False)])
    completion_rate = (completed_habits / len(recent_habits) * 100) if recent_habits else 0
    
    return round(completion_rate, 2)

def _calculate_knowledge_growth(knowledge_items: List[Dict], days: int) -> int:
    """知識成長を計算"""
    if not knowledge_items:
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_knowledge = 0
    
    for knowledge in knowledge_items:
        created_time = knowledge.get('created_time', '')
        if created_time:
            try:
                created_date = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                if created_date >= cutoff_date:
                    recent_knowledge += 1
            except:
                pass
    
    return recent_knowledge
