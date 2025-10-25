#!/usr/bin/env python3
"""
GoogleカレンダーとNotionDBの同期機能
Task/ToDoデータベースとの双方向同期
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
GOOGLE_CALENDAR_ENABLED = os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() == "true"
GOOGLE_CALENDAR_SYNC_INTERVAL = int(os.getenv("GOOGLE_CALENDAR_SYNC_INTERVAL", "300"))  # 5分間隔

# Google Calendar API設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

# NotionデータベースID
TASK_DATABASE_ID = os.getenv("NOTION_TASK_DB_ID", "")
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

class GoogleCalendarSync:
    def __init__(self):
        self.service = None
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def authenticate_google_calendar(self):
        """GoogleカレンダーAPIの認証"""
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
        
        # Google Calendar APIサービスを構築
        self.service = build('calendar', 'v3', credentials=creds)
        print(f"{Colors.GREEN}✅ GoogleカレンダーAPI認証完了{Colors.END}")
        return True
    
    def get_notion_tasks(self, database_id):
        """NotionDBからタスクを取得"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        response = requests.post(url, headers=self.notion_headers)
        if response.status_code != 200:
            print(f"{Colors.RED}❌ NotionDB取得エラー: {response.status_code}{Colors.END}")
            return []
        
        data = response.json()
        tasks = []
        
        for page in data.get('results', []):
            task = {
                'id': page['id'],
                'title': self.extract_title(page),
                'date': self.extract_date(page),
                'status': self.extract_status(page),
                'description': self.extract_description(page)
            }
            tasks.append(task)
        
        return tasks
    
    def extract_title(self, page):
        """ページからタイトルを抽出"""
        properties = page.get('properties', {})
        
        # Taskデータベースの場合
        if 'タスク名' in properties:
            title_prop = properties['タスク名']
            if title_prop['type'] == 'title' and title_prop['title']:
                return title_prop['title'][0]['text']['content']
        
        # ToDoデータベースの場合
        if 'ToDo名' in properties:
            title_prop = properties['ToDo名']
            if title_prop['type'] == 'title' and title_prop['title']:
                return title_prop['title'][0]['text']['content']
        
        return "タイトルなし"
    
    def extract_date(self, page):
        """ページから日付を抽出"""
        properties = page.get('properties', {})
        
        # Taskデータベースの場合
        if '期日' in properties:
            date_prop = properties['期日']
            if date_prop['type'] == 'date' and date_prop['date']:
                return date_prop['date']['start']
        
        # ToDoデータベースの場合
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
        
        # Taskデータベースの場合
        if 'メモ' in properties:
            desc_prop = properties['メモ']
            if desc_prop['type'] == 'rich_text' and desc_prop['rich_text']:
                return desc_prop['rich_text'][0]['text']['content']
        
        # ToDoデータベースの場合
        if 'メモ' in properties:
            desc_prop = properties['メモ']
            if desc_prop['type'] == 'rich_text' and desc_prop['rich_text']:
                return desc_prop['rich_text'][0]['text']['content']
        
        return ""
    
    def get_google_calendar_events(self, days=30):
        """Googleカレンダーからイベントを取得"""
        if not self.service:
            return []
        
        # 現在時刻から指定日数後まで
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events:
            formatted_event = {
                'id': event.get('id'),
                'title': event.get('summary', 'タイトルなし'),
                'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                'description': event.get('description', ''),
                'status': 'confirmed'
            }
            formatted_events.append(formatted_event)
        
        return formatted_events
    
    def get_events_by_date(self, target_date, page_token=None):
        """指定日付のイベントを取得（ページネーション対応、広範囲検索）"""
        if not self.service:
            return []
        
        # より広範囲の時間で検索（前日23:00から翌日01:00まで）
        start_time = f"{target_date}T00:00:00+09:00"
        end_time = f"{target_date}T23:59:59+09:00"
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime',
                maxResults=250,  # 最大250件
                pageToken=page_token,
                showDeleted=True,  # 削除されたイベントも含める
                showHiddenInvitations=False  # 非表示の招待は除外
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                # 削除されたイベントやキャンセルされたイベントを除外
                if event.get('status') in ['cancelled', 'tentative']:
                    continue
                    
                formatted_event = {
                    'id': event.get('id'),
                    'title': event.get('summary', 'タイトルなし'),
                    'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                    'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                    'description': event.get('description', ''),
                    'status': event.get('status', 'confirmed'),
                    'created': event.get('created', ''),
                    'updated': event.get('updated', '')
                }
                formatted_events.append(formatted_event)
            
            return formatted_events
        except Exception as e:
            print(f"{Colors.RED}❌ イベント取得エラー: {e}{Colors.END}")
            return []
    
    def delete_google_calendar_event(self, event_id):
        """Googleカレンダーからイベントを削除（cancelledステータスも含む）"""
        if not self.service:
            return False
        
        try:
            # まずイベントの詳細を取得してステータスを確認
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            status = event.get('status', 'confirmed')
            
            if status == 'cancelled':
                # cancelledステータスのイベントは既に削除済み
                print(f"{Colors.YELLOW}⚠️  イベントは既に削除済み: {event_id}{Colors.END}")
                return True
            else:
                # 通常のイベントを削除
                self.service.events().delete(calendarId='primary', eventId=event_id).execute()
                print(f"{Colors.GREEN}✅ Googleカレンダーからイベント削除: {event_id}{Colors.END}")
                return True
        except Exception as e:
            # 404エラー（既に削除済み）の場合は成功として扱う
            if "404" in str(e) or "Not Found" in str(e):
                print(f"{Colors.YELLOW}⚠️  イベントは既に削除済み: {event_id}{Colors.END}")
                return True
            print(f"{Colors.RED}❌ Googleカレンダーイベント削除エラー: {e}{Colors.END}")
            return False
    
    def delete_events_by_date(self, target_date):
        """指定日付のすべてのイベントを削除（全件対応）"""
        print(f"{Colors.CYAN}🗑️  {target_date}の予定を全件削除中...{Colors.END}")
        
        total_deleted = 0
        page_token = None
        
        while True:
            try:
                # 指定日付の開始と終了時刻
                start_time = f"{target_date}T00:00:00+09:00"
                end_time = f"{target_date}T23:59:59+09:00"
                
                events_result = self.service.events().list(
                    calendarId='primary',
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy='startTime',
                    maxResults=250,  # 最大250件
                    pageToken=page_token,
                    showDeleted=True  # 削除されたイベントも含める
                ).execute()
                
                events = events_result.get('items', [])
                
                if not events:
                    break
                
                print(f"{Colors.BLUE}📅 {target_date}の予定: {len(events)}件 (ページ処理中){Colors.END}")
                
                deleted_count = 0
                for event in events:
                    event_title = event.get('summary', 'タイトルなし')
                    event_start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                    print(f"  - {event_title} ({event_start})")
                    
                    if self.delete_google_calendar_event(event.get('id')):
                        deleted_count += 1
                
                total_deleted += deleted_count
                print(f"{Colors.GREEN}✅ このページの削除完了: {deleted_count}/{len(events)}件{Colors.END}")
                
                # 次のページがあるかチェック
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break
                    
            except Exception as e:
                print(f"{Colors.RED}❌ ページ処理エラー: {e}{Colors.END}")
                break
        
        print(f"{Colors.GREEN}✨ {target_date}の予定削除完了: 合計{total_deleted}件{Colors.END}")
        return True
    
    def create_google_calendar_event(self, task):
        """Googleカレンダーにイベントを作成"""
        if not self.service or not task['date']:
            return None
        
        event = {
            'summary': task['title'],
            'description': task['description'],
            'start': {
                'dateTime': f"{task['date']}T09:00:00",
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': f"{task['date']}T10:00:00",
                'timeZone': 'Asia/Tokyo',
            },
        }
        
        try:
            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f"{Colors.GREEN}✅ Googleカレンダーにイベント作成: {task['title']}{Colors.END}")
            return created_event['id']
        except Exception as e:
            print(f"{Colors.RED}❌ Googleカレンダーイベント作成エラー: {e}{Colors.END}")
            return None
    
    def create_test_events(self, target_date, count=5):
        """テスト用のイベントを作成"""
        if not self.service:
            return False
        
        test_events = [
            {"title": "テスト会議1", "description": "テスト用の会議です"},
            {"title": "テスト会議2", "description": "テスト用の会議です"},
            {"title": "テスト会議3", "description": "テスト用の会議です"},
            {"title": "テスト会議4", "description": "テスト用の会議です"},
            {"title": "テスト会議5", "description": "テスト用の会議です"}
        ]
        
        created_count = 0
        for i in range(min(count, len(test_events))):
            event = {
                'summary': test_events[i]['title'],
                'description': test_events[i]['description'],
                'start': {
                    'dateTime': f"{target_date}T09:00:00+09:00",
                },
                'end': {
                    'dateTime': f"{target_date}T10:00:00+09:00",
                },
            }
            
            try:
                created_event = self.service.events().insert(calendarId='primary', body=event).execute()
                print(f"{Colors.GREEN}✅ テストイベント作成: {test_events[i]['title']} (ID: {created_event['id']}){Colors.END}")
                created_count += 1
            except Exception as e:
                print(f"{Colors.RED}❌ テストイベント作成エラー: {e}{Colors.END}")
        
        print(f"{Colors.CYAN}📊 テストイベント作成完了: {created_count}/{count}件{Colors.END}")
        return created_count > 0
    
    def check_duplicate_task(self, event, database_id):
        """重複タスクをチェック（ページネーション対応）"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        # タイトルフィールド名を決定
        title_field = "タスク名" if database_id == TASK_DATABASE_ID else "ToDo名"
        
        query_data = {
            "filter": {
                "property": title_field,
                "title": {
                    "equals": event['title']
                }
            }
        }
        
        # ページネーション対応で重複チェック
        has_more = True
        next_cursor = None
        
        while has_more:
            if next_cursor:
                query_data['start_cursor'] = next_cursor
            
            try:
                response = requests.post(url, headers=self.notion_headers, json=query_data)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    # 重複が見つかったら即座にTrueを返す
                    if len(results) > 0:
                        print(f"{Colors.YELLOW}⚠️  重複タスク発見: {event['title']} (既存件数: {len(results)}){Colors.END}")
                        return True
                    
                    # 次のページがあるかチェック
                    has_more = data.get('has_more', False)
                    next_cursor = data.get('next_cursor')
                else:
                    print(f"{Colors.RED}❌ 重複チェックエラー: {response.status_code}{Colors.END}")
                    return False
            except Exception as e:
                print(f"{Colors.RED}❌ 重複チェック例外: {e}{Colors.END}")
                return False
        
        return False
    
    def create_notion_task(self, event, database_id):
        """NotionDBにタスクを作成（重複チェック付き）"""
        # 重複チェック
        if self.check_duplicate_task(event, database_id):
            print(f"{Colors.YELLOW}⚠️  重複タスクをスキップ: {event['title']}{Colors.END}")
            return None
        
        url = "https://api.notion.com/v1/pages"
        
        # データベースに応じてプロパティを設定
        if database_id == TASK_DATABASE_ID:
            properties = {
                "タスク名": {
                    "title": [{"text": {"content": event['title']}}]
                },
                "期日": {
                    "date": {"start": event['start'][:10] if event['start'] else None}
                },
                "ステータス": {
                    "select": {"name": "未完了"}
                },
                "メモ": {
                    "rich_text": [{"text": {"content": event['description']}}]
                }
            }
        else:  # ToDoデータベース
            properties = {
                "ToDo名": {
                    "title": [{"text": {"content": event['title']}}]
                },
                "実施日": {
                    "date": {"start": event['start'][:10] if event['start'] else None}
                },
                "ステータス": {
                    "select": {"name": "未完了"}
                },
                "メモ": {
                    "rich_text": [{"text": {"content": event['description']}}]
                }
            }
        
        data = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        response = requests.post(url, headers=self.notion_headers, json=data)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ NotionDBにタスク作成: {event['title']}{Colors.END}")
            return response.json()['id']
        else:
            print(f"{Colors.RED}❌ NotionDBタスク作成エラー: {response.status_code}{Colors.END}")
            return None
    
    def sync_notion_to_google(self):
        """NotionDBからGoogleカレンダーへ同期"""
        print(f"{Colors.CYAN}📤 NotionDB → Googleカレンダー 同期開始{Colors.END}")
        
        # Taskデータベースから同期
        if TASK_DATABASE_ID:
            tasks = self.get_notion_tasks(TASK_DATABASE_ID)
            for task in tasks:
                if task['date'] and task['status'] != '完了':
                    self.create_google_calendar_event(task)
        
        # ToDoデータベースから同期
        if TODO_DATABASE_ID:
            todos = self.get_notion_tasks(TODO_DATABASE_ID)
            for todo in todos:
                if todo['date'] and todo['status'] != '完了':
                    self.create_google_calendar_event(todo)
    
    def sync_google_to_notion(self):
        """GoogleカレンダーからNotionDBへ同期"""
        print(f"{Colors.CYAN}📥 Googleカレンダー → NotionDB 同期開始{Colors.END}")
        
        events = self.get_google_calendar_events()
        
        for event in events:
            # Taskデータベースに同期
            if TASK_DATABASE_ID:
                self.create_notion_task(event, TASK_DATABASE_ID)
            
            # ToDoデータベースに同期
            if TODO_DATABASE_ID:
                self.create_notion_task(event, TODO_DATABASE_ID)
    
    def full_sync(self):
        """双方向同期を実行"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔄 Googleカレンダー ↔ NotionDB 双方向同期{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        if not self.authenticate_google_calendar():
            return False
        
        # NotionDB → Googleカレンダー
        self.sync_notion_to_google()
        
        # Googleカレンダー → NotionDB
        self.sync_google_to_notion()
        
        print(f"{Colors.GREEN}✨ 双方向同期完了！{Colors.END}")
        return True

def main():
    """メイン処理"""
    import sys
    
    # コマンドライン引数をチェック
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "delete":
            if len(sys.argv) < 3:
                print(f"{Colors.RED}❌ 削除する日付を指定してください{Colors.END}")
                print("使用例: python google_calendar_sync.py delete 2025-10-27")
                return 1
            
            target_date = sys.argv[2]
            print(f"{Colors.BOLD}{Colors.RED}🗑️  Googleカレンダー予定削除{Colors.END}")
            print(f"{Colors.RED}{'='*60}{Colors.END}")
            print(f"{Colors.RED}削除対象日付: {target_date}{Colors.END}")
            
            # 削除確認（自動実行）
            print(f"{Colors.YELLOW}⚠️  {target_date}の予定を全て削除します{Colors.END}")
            
            # 削除実行
            sync = GoogleCalendarSync()
            if not sync.authenticate_google_calendar():
                return 1
            
            success = sync.delete_events_by_date(target_date)
            return 0 if success else 1
        
        elif command == "test":
            if len(sys.argv) < 3:
                print(f"{Colors.RED}❌ テスト用イベントを作成する日付を指定してください{Colors.END}")
                print("使用例: python google_calendar_sync.py test 2025-10-28")
                return 1
            
            target_date = sys.argv[2]
            count = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            
            print(f"{Colors.BOLD}{Colors.CYAN}🧪 テスト用イベント作成{Colors.END}")
            print(f"{Colors.CYAN}{'='*60}{Colors.END}")
            print(f"{Colors.CYAN}作成対象日付: {target_date}{Colors.END}")
            print(f"{Colors.CYAN}作成件数: {count}件{Colors.END}")
            
            # テストイベント作成
            sync = GoogleCalendarSync()
            if not sync.authenticate_google_calendar():
                return 1
            
            success = sync.create_test_events(target_date, count)
            return 0 if success else 1
        
        elif command == "list":
            if len(sys.argv) < 3:
                print(f"{Colors.RED}❌ 表示する日付を指定してください{Colors.END}")
                print("使用例: python google_calendar_sync.py list 2025-10-27")
                return 1
            
            target_date = sys.argv[2]
            print(f"{Colors.BOLD}{Colors.BLUE}📅 Googleカレンダー予定一覧{Colors.END}")
            print(f"{Colors.BLUE}{'='*60}{Colors.END}")
            print(f"{Colors.BLUE}表示対象日付: {target_date}{Colors.END}")
            
            # 予定一覧表示
            sync = GoogleCalendarSync()
            if not sync.authenticate_google_calendar():
                return 1
            
            events = sync.get_events_by_date(target_date)
            
            if not events:
                print(f"{Colors.YELLOW}⚠️  {target_date}の予定は見つかりませんでした{Colors.END}")
            else:
                print(f"{Colors.BLUE}📅 {target_date}の予定: {len(events)}件{Colors.END}")
                for i, event in enumerate(events, 1):
                    print(f"  {i}. {event['title']} ({event['start']})")
            
            return 0
    
    # 通常の同期処理
    print(f"{Colors.BOLD}{Colors.BLUE}📅 Googleカレンダー ↔ NotionDB 同期{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 設定確認
    if not GOOGLE_CALENDAR_ENABLED:
        print(f"{Colors.YELLOW}⚠️  Googleカレンダー同期が無効になっています{Colors.END}")
        print("GOOGLE_CALENDAR_ENABLED=true に設定してください")
        return 1
    
    if not NOTION_API_KEY:
        print(f"{Colors.RED}❌ Notion APIキーが設定されていません{Colors.END}")
        return 1
    
    if not TASK_DATABASE_ID and not TODO_DATABASE_ID:
        print(f"{Colors.RED}❌ Task/ToDoデータベースIDが設定されていません{Colors.END}")
        return 1
    
    # 同期実行
    sync = GoogleCalendarSync()
    success = sync.full_sync()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
