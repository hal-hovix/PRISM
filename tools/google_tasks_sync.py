#!/usr/bin/env python3
"""
Google TasksとNotionDBの完全同期機能
ToDoデータベースとの双方向同期
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# .envファイルを読み込み
load_dotenv()

# 環境変数から設定を読み込み
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
GOOGLE_TASKS_ENABLED = os.getenv("GOOGLE_TASKS_ENABLED", "false").lower() == "true"
GOOGLE_TASKS_SYNC_INTERVAL = int(os.getenv("GOOGLE_TASKS_SYNC_INTERVAL", "300"))  # 5分間隔

# Google Tasks API設定
SCOPES = ['https://www.googleapis.com/auth/tasks']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token_tasks.pickle'

# NotionデータベースID
TODO_DATABASE_ID = os.getenv("NOTION_TODO_DB_ID", "")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

class GoogleTasksSync:
    def __init__(self):
        self.service = None
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def authenticate_google_tasks(self):
        """Google Tasks APIの認証"""
        creds = None
        
        # 既存のトークンファイルを確認
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # 有効な認証情報がない場合は認証フローを実行
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"{Colors.RED}❌ credentials.jsonファイルが見つかりません{Colors.END}")
                    print("Google Cloud ConsoleでOAuth2認証情報を作成してください")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        # Google Tasks APIサービスを構築
        self.service = build('tasks', 'v1', credentials=creds)
        print(f"{Colors.GREEN}✅ Google Tasks API認証完了{Colors.END}")
        return True
    
    def get_notion_todos(self):
        """NotionDBからToDoを取得"""
        url = f"https://api.notion.com/v1/databases/{TODO_DATABASE_ID}/query"
        
        response = requests.post(url, headers=self.notion_headers)
        if response.status_code != 200:
            print(f"{Colors.RED}❌ NotionDB取得エラー: {response.status_code}{Colors.END}")
            return []
        
        data = response.json()
        todos = []
        
        for page in data.get('results', []):
            todo = {
                'id': page['id'],
                'title': self.extract_title(page),
                'date': self.extract_date(page),
                'status': self.extract_status(page),
                'description': self.extract_description(page),
                'priority': self.extract_priority(page),
                'reminder': self.extract_reminder(page)
            }
            todos.append(todo)
        
        return todos
    
    def extract_title(self, page):
        """ページからタイトルを抽出"""
        properties = page.get('properties', {})
        
        if 'ToDo名' in properties:
            title_prop = properties['ToDo名']
            if title_prop['type'] == 'title' and title_prop['title']:
                return title_prop['title'][0]['text']['content']
        
        return "タイトルなし"
    
    def extract_date(self, page):
        """ページから日付を抽出"""
        properties = page.get('properties', {})
        
        if '実施日' in properties:
            date_prop = properties['実施日']
            if date_prop['type'] == 'date' and date_prop['date']:
                return date_prop['date']['start']
        
        return None
    
    def extract_status(self, page):
        """ページからステータスを抽出"""
        properties = page.get('properties', {})
        
        if 'ステータス' in properties:
            status_prop = properties['ステータス']
            if status_prop['type'] == 'select' and status_prop['select']:
                return status_prop['select']['name']
        
        return "未完了"
    
    def extract_description(self, page):
        """ページから説明を抽出"""
        properties = page.get('properties', {})
        
        if 'メモ' in properties:
            desc_prop = properties['メモ']
            if desc_prop['type'] == 'rich_text' and desc_prop['rich_text']:
                return desc_prop['rich_text'][0]['text']['content']
        
        return ""
    
    def extract_priority(self, page):
        """ページから優先度を抽出"""
        properties = page.get('properties', {})
        
        if '優先度' in properties:
            priority_prop = properties['優先度']
            if priority_prop['type'] == 'number' and priority_prop['number']:
                return priority_prop['number']
        
        return 0
    
    def extract_reminder(self, page):
        """ページからリマインダーを抽出"""
        properties = page.get('properties', {})
        
        if 'リマインダー' in properties:
            reminder_prop = properties['リマインダー']
            if reminder_prop['type'] == 'checkbox':
                return reminder_prop['checkbox']
        
        return False
    
    def get_google_tasks(self):
        """Google Tasksからタスクを取得"""
        if not self.service:
            return []
        
        try:
            # タスクリストを取得
            tasklists = self.service.tasklists().list().execute()
            tasks = []
            
            for tasklist in tasklists.get('items', []):
                # 各タスクリストからタスクを取得
                tasklist_tasks = self.service.tasks().list(
                    tasklist=tasklist['id'],
                    showCompleted=False,
                    showHidden=False
                ).execute()
                
                for task in tasklist_tasks.get('items', []):
                    formatted_task = {
                        'id': task.get('id'),
                        'title': task.get('title', 'タイトルなし'),
                        'due': task.get('due'),
                        'status': task.get('status'),
                        'notes': task.get('notes', ''),
                        'position': task.get('position'),
                        'tasklist_id': tasklist['id'],
                        'tasklist_title': tasklist['title']
                    }
                    tasks.append(formatted_task)
            
            return tasks
        except Exception as e:
            print(f"{Colors.RED}❌ Google Tasks取得エラー: {e}{Colors.END}")
            return []
    
    def create_google_task(self, todo):
        """Google Tasksにタスクを作成"""
        if not self.service:
            return None
        
        try:
            # デフォルトのタスクリストを取得
            tasklists = self.service.tasklists().list().execute()
            if not tasklists.get('items'):
                print(f"{Colors.RED}❌ Google Tasksにタスクリストがありません{Colors.END}")
                return None
            
            tasklist_id = tasklists['items'][0]['id']
            
            # タスクを作成
            task = {
                'title': todo['title'],
                'notes': todo['description']
            }
            
            # 日付が設定されている場合はdueを設定
            if todo['date']:
                task['due'] = f"{todo['date']}T00:00:00.000Z"
            
            created_task = self.service.tasks().insert(
                tasklist=tasklist_id,
                body=task
            ).execute()
            
            print(f"{Colors.GREEN}✅ Google Tasksにタスク作成: {todo['title']}{Colors.END}")
            return created_task['id']
        except Exception as e:
            print(f"{Colors.RED}❌ Google Tasksタスク作成エラー: {e}{Colors.END}")
            return None
    
    def create_notion_todo(self, task):
        """NotionDBにToDoを作成"""
        url = "https://api.notion.com/v1/pages"
        
        properties = {
            "ToDo名": {
                "title": [{"text": {"content": task['title']}}]
            },
            "実施日": {
                "date": {"start": task['due'][:10] if task['due'] else None}
            },
            "ステータス": {
                "select": {"name": "完了" if task['status'] == 'completed' else "未完了"}
            },
            "メモ": {
                "rich_text": [{"text": {"content": task['notes']}}]
            },
            "優先度": {
                "number": 1 if task.get('position') else 0
            },
            "リマインダー": {
                "checkbox": False
            }
        }
        
        data = {
            "parent": {"database_id": TODO_DATABASE_ID},
            "properties": properties
        }
        
        response = requests.post(url, headers=self.notion_headers, json=data)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ NotionDBにToDo作成: {task['title']}{Colors.END}")
            return response.json()['id']
        else:
            print(f"{Colors.RED}❌ NotionDB ToDo作成エラー: {response.status_code}{Colors.END}")
            return None
    
    def sync_notion_to_google(self):
        """NotionDBからGoogle Tasksへ同期"""
        print(f"{Colors.CYAN}📤 NotionDB → Google Tasks 同期開始{Colors.END}")
        
        todos = self.get_notion_todos()
        for todo in todos:
            if todo['status'] != '完了':
                self.create_google_task(todo)
    
    def sync_google_to_notion(self):
        """Google TasksからNotionDBへ同期"""
        print(f"{Colors.CYAN}📥 Google Tasks → NotionDB 同期開始{Colors.END}")
        
        tasks = self.get_google_tasks()
        for task in tasks:
            if task['status'] != 'completed':
                self.create_notion_todo(task)
    
    def full_sync(self):
        """双方向同期を実行"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔄 Google Tasks ↔ NotionDB 双方向同期{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        if not self.authenticate_google_tasks():
            return False
        
        # NotionDB → Google Tasks
        self.sync_notion_to_google()
        
        # Google Tasks → NotionDB
        self.sync_google_to_notion()
        
        print(f"{Colors.GREEN}✨ 双方向同期完了！{Colors.END}")
        return True

def main():
    """メイン処理"""
    print(f"{Colors.BOLD}{Colors.BLUE}📋 Google Tasks ↔ NotionDB 同期{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 設定確認
    if not GOOGLE_TASKS_ENABLED:
        print(f"{Colors.YELLOW}⚠️  Google Tasks同期が無効になっています{Colors.END}")
        print("GOOGLE_TASKS_ENABLED=true に設定してください")
        return 1
    
    if not NOTION_API_KEY:
        print(f"{Colors.RED}❌ Notion APIキーが設定されていません{Colors.END}")
        return 1
    
    if not TODO_DATABASE_ID:
        print(f"{Colors.RED}❌ ToDoデータベースIDが設定されていません{Colors.END}")
        return 1
    
    # 同期実行
    sync = GoogleTasksSync()
    success = sync.full_sync()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

