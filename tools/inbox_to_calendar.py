#!/usr/bin/env python3
"""
INBOXの期日情報をGoogleカレンダーに自動登録する機能
"""

import os
import re
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

# Google Calendar API設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

# NotionデータベースID
INBOX_DATABASE_ID = os.getenv("NOTION_INBOX_DB_ID", "2935fbef07e28074bdf8f9c06755f45a")  # Task DBをINBOXとして使用

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

class InboxToCalendarSync:
    def __init__(self):
        self.service = None
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def authenticate_google_calendar(self):
        """GoogleカレンダーAPI認証"""
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"{Colors.RED}❌ credentials.jsonファイルが見つかりません{Colors.END}")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        print(f"{Colors.GREEN}✅ GoogleカレンダーAPI認証完了{Colors.END}")
        return True
    
    def get_inbox_items(self):
        """INBOXからアイテムを取得"""
        url = f"https://api.notion.com/v1/databases/{INBOX_DATABASE_ID}/query"
        
        query_data = {
            "filter": {
                "property": "ステータス",
                "select": {
                    "equals": "INBOX"
                }
            }
        }
        
        try:
            response = requests.post(url, headers=self.notion_headers, json=query_data)
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                print(f"{Colors.RED}❌ INBOX取得エラー: {response.status_code}{Colors.END}")
                return []
        except Exception as e:
            print(f"{Colors.RED}❌ INBOX取得例外: {e}{Colors.END}")
            return []
    
    def extract_date_from_text(self, text):
        """テキストから日付を抽出"""
        if not text:
            return None
        
        # 日付パターンの定義
        patterns = [
            # 2025/10/25, 2025-10-25, 2025.10.25
            r'(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})',
            # 10/25, 10-25, 10.25 (今年)
            r'(\d{1,2})[/\-\.](\d{1,2})',
            # 明日, 明後日
            r'(明日|明後日)',
            # 来週, 来月
            r'(来週|来月)',
            # 具体的な日付表現
            r'(月曜日|火曜日|水曜日|木曜日|金曜日|土曜日|日曜日)',
        ]
        
        current_year = datetime.now().year
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if pattern == r'(明日|明後日)':
                    if match.group(1) == '明日':
                        return datetime.now() + timedelta(days=1)
                    elif match.group(1) == '明後日':
                        return datetime.now() + timedelta(days=2)
                
                elif pattern == r'(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})':
                    year, month, day = match.groups()
                    try:
                        return datetime(int(year), int(month), int(day))
                    except ValueError:
                        continue
                
                elif pattern == r'(\d{1,2})[/\-\.](\d{1,2})':
                    month, day = match.groups()
                    try:
                        return datetime(current_year, int(month), int(day))
                    except ValueError:
                        continue
        
        return None
    
    def create_calendar_event(self, title, date, description=""):
        """Googleカレンダーにイベントを作成"""
        if not self.service:
            return False
        
        # 日付を文字列に変換
        date_str = date.strftime('%Y-%m-%d')
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'date': date_str,
            },
            'end': {
                'date': date_str,
            },
        }
        
        try:
            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f"{Colors.GREEN}✅ Googleカレンダーにイベント作成: {title} ({date_str}){Colors.END}")
            return created_event['id']
        except Exception as e:
            print(f"{Colors.RED}❌ Googleカレンダーイベント作成エラー: {e}{Colors.END}")
            return None
    
    def process_inbox_items(self):
        """INBOXアイテムを処理してカレンダーに登録"""
        print(f"{Colors.CYAN}📅 INBOX → Googleカレンダー同期開始{Colors.END}")
        
        # Googleカレンダー認証
        if not self.authenticate_google_calendar():
            return False
        
        # INBOXアイテムを取得
        items = self.get_inbox_items()
        if not items:
            print(f"{Colors.YELLOW}⚠️  INBOXにアイテムがありません{Colors.END}")
            return True
        
        print(f"{Colors.BLUE}📋 INBOXアイテム: {len(items)}件{Colors.END}")
        
        processed_count = 0
        for item in items:
            # タイトルを取得
            title_property = item.get('properties', {}).get('タスク名', {})
            title = ""
            if title_property.get('title'):
                title = title_property['title'][0]['text']['content']
            
            # 説明を取得
            description_property = item.get('properties', {}).get('説明', {})
            description = ""
            if description_property.get('rich_text'):
                description = description_property['rich_text'][0]['text']['content']
            
            if not title:
                continue
            
            # 日付を抽出
            date = self.extract_date_from_text(title + " " + description)
            
            if date:
                # Googleカレンダーに登録
                event_id = self.create_calendar_event(title, date, description)
                if event_id:
                    processed_count += 1
                    print(f"{Colors.GREEN}  ✓ {title} → {date.strftime('%Y-%m-%d')}{Colors.END}")
                else:
                    print(f"{Colors.RED}  ✗ {title} → 登録失敗{Colors.END}")
            else:
                print(f"{Colors.YELLOW}  ⊘ {title} → 日付なし{Colors.END}")
        
        print(f"{Colors.CYAN}📊 処理完了: {processed_count}/{len(items)}件をカレンダーに登録{Colors.END}")
        return True

def main():
    """メイン処理"""
    print(f"{Colors.BOLD}{Colors.CYAN}📅 INBOX → Googleカレンダー自動登録{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    
    if not GOOGLE_CALENDAR_ENABLED:
        print(f"{Colors.RED}❌ Googleカレンダー機能が無効です{Colors.END}")
        print("GOOGLE_CALENDAR_ENABLED=true に設定してください")
        return 1
    
    sync = InboxToCalendarSync()
    success = sync.process_inbox_items()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
