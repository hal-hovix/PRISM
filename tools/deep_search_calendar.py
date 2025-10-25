#!/usr/bin/env python3
"""
Googleカレンダーの詳細検索ツール
"""

import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from datetime import datetime, timedelta

# 環境変数から設定を読み込み
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DeepCalendarSearch:
    def __init__(self):
        self.service = None
        self.authenticate_google_calendar()
    
    def authenticate_google_calendar(self):
        """GoogleカレンダーAPI認証"""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print(f"{Colors.RED}❌ credentials.jsonファイルが見つかりません{Colors.END}")
                    return False
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print(f"{Colors.GREEN}✅ GoogleカレンダーAPI認証完了{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ GoogleカレンダーAPI認証エラー: {e}{Colors.END}")
            return False
    
    def search_all_events(self, target_date):
        """指定日付のすべてのイベントを詳細検索"""
        if not self.service:
            return []
        
        print(f"{Colors.CYAN}🔍 {target_date}の詳細検索を開始...{Colors.END}")
        
        # 複数の時間範囲で検索
        search_ranges = [
            # 当日
            (f"{target_date}T00:00:00+09:00", f"{target_date}T23:59:59+09:00"),
            # 前日から当日
            (f"{target_date}T00:00:00+09:00", f"{target_date}T23:59:59+09:00"),
            # UTC時間で検索
            (f"{target_date}T00:00:00Z", f"{target_date}T23:59:59Z"),
            # より広範囲
            (f"{target_date}T00:00:00+09:00", f"{target_date}T23:59:59+09:00"),
        ]
        
        all_events = []
        
        for i, (start_time, end_time) in enumerate(search_ranges):
            print(f"{Colors.BLUE}📅 検索範囲 {i+1}: {start_time} ～ {end_time}{Colors.END}")
            
            try:
                events_result = self.service.events().list(
                    calendarId='primary',
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy='startTime',
                    maxResults=1000,  # 最大1000件
                    showDeleted=True,  # 削除されたイベントも含める
                    showHiddenInvitations=True  # 非表示の招待も含める
                ).execute()
                
                events = events_result.get('items', [])
                print(f"{Colors.YELLOW}  → {len(events)}件のイベントを発見{Colors.END}")
                
                for event in events:
                    event_info = {
                        'id': event.get('id'),
                        'title': event.get('summary', 'タイトルなし'),
                        'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                        'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                        'description': event.get('description', ''),
                        'status': event.get('status', 'confirmed'),
                        'created': event.get('created', ''),
                        'updated': event.get('updated', ''),
                        'creator': event.get('creator', {}).get('email', ''),
                        'organizer': event.get('organizer', {}).get('email', ''),
                        'visibility': event.get('visibility', ''),
                        'transparency': event.get('transparency', ''),
                        'recurringEventId': event.get('recurringEventId', ''),
                        'originalStartTime': event.get('originalStartTime', ''),
                        'iCalUID': event.get('iCalUID', ''),
                        'htmlLink': event.get('htmlLink', ''),
                        'hangoutLink': event.get('hangoutLink', ''),
                        'conferenceData': event.get('conferenceData', ''),
                        'attendees': event.get('attendees', []),
                        'reminders': event.get('reminders', {}),
                        'source': event.get('source', {}),
                        'extendedProperties': event.get('extendedProperties', {}),
                        'gadget': event.get('gadget', {}),
                        'anyoneCanAddSelf': event.get('anyoneCanAddSelf', False),
                        'guestsCanInviteOthers': event.get('guestsCanInviteOthers', False),
                        'guestsCanModify': event.get('guestsCanModify', False),
                        'guestsCanSeeOtherGuests': event.get('guestsCanSeeOtherGuests', False),
                        'privateCopy': event.get('privateCopy', False),
                        'locked': event.get('locked', False),
                        'sequence': event.get('sequence', 0),
                        'recurrence': event.get('recurrence', []),
                        'attachments': event.get('attachments', []),
                        'eventType': event.get('eventType', ''),
                        'workingLocationProperties': event.get('workingLocationProperties', {}),
                        'outOfOfficeProperties': event.get('outOfOfficeProperties', {}),
                        'focusTimeProperties': event.get('focusTimeProperties', {}),
                        'location': event.get('location', ''),
                        'colorId': event.get('colorId', ''),
                        'kind': event.get('kind', ''),
                        'etag': event.get('etag', ''),
                        'id': event.get('id', ''),
                        'status': event.get('status', ''),
                        'htmlLink': event.get('htmlLink', ''),
                        'created': event.get('created', ''),
                        'updated': event.get('updated', ''),
                        'summary': event.get('summary', ''),
                        'description': event.get('description', ''),
                        'location': event.get('location', ''),
                        'colorId': event.get('colorId', ''),
                        'creator': event.get('creator', {}),
                        'organizer': event.get('organizer', {}),
                        'start': event.get('start', {}),
                        'end': event.get('end', {}),
                        'endTimeUnspecified': event.get('endTimeUnspecified', False),
                        'recurrence': event.get('recurrence', []),
                        'recurringEventId': event.get('recurringEventId', ''),
                        'originalStartTime': event.get('originalStartTime', {}),
                        'transparency': event.get('transparency', ''),
                        'visibility': event.get('visibility', ''),
                        'iCalUID': event.get('iCalUID', ''),
                        'sequence': event.get('sequence', 0),
                        'attendees': event.get('attendees', []),
                        'attendeesOmitted': event.get('attendeesOmitted', False),
                        'hangoutLink': event.get('hangoutLink', ''),
                        'conferenceData': event.get('conferenceData', {}),
                        'gadget': event.get('gadget', {}),
                        'anyoneCanAddSelf': event.get('anyoneCanAddSelf', False),
                        'guestsCanInviteOthers': event.get('guestsCanInviteOthers', False),
                        'guestsCanModify': event.get('guestsCanModify', False),
                        'guestsCanSeeOtherGuests': event.get('guestsCanSeeOtherGuests', False),
                        'privateCopy': event.get('privateCopy', False),
                        'locked': event.get('locked', False),
                        'reminders': event.get('reminders', {}),
                        'source': event.get('source', {}),
                        'attachments': event.get('attachments', []),
                        'eventType': event.get('eventType', ''),
                        'workingLocationProperties': event.get('workingLocationProperties', {}),
                        'outOfOfficeProperties': event.get('outOfOfficeProperties', {}),
                        'focusTimeProperties': event.get('focusTimeProperties', {}),
                        'raw_event': event  # 生のイベントデータも保存
                    }
                    all_events.append(event_info)
                
            except Exception as e:
                print(f"{Colors.RED}❌ 検索エラー: {e}{Colors.END}")
        
        # 重複を除去
        unique_events = []
        seen_ids = set()
        for event in all_events:
            if event['id'] not in seen_ids:
                unique_events.append(event)
                seen_ids.add(event['id'])
        
        print(f"{Colors.GREEN}✨ 合計 {len(unique_events)}件のユニークなイベントを発見{Colors.END}")
        return unique_events
    
    def display_events(self, events):
        """イベントを詳細表示"""
        if not events:
            print(f"{Colors.YELLOW}⚠️  イベントが見つかりませんでした{Colors.END}")
            return
        
        print(f"{Colors.BLUE}📅 発見されたイベント: {len(events)}件{Colors.END}")
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        
        for i, event in enumerate(events, 1):
            print(f"{Colors.CYAN}{i}. {event['title']}{Colors.END}")
            print(f"   ID: {event['id']}")
            print(f"   開始: {event['start']}")
            print(f"   終了: {event['end']}")
            print(f"   ステータス: {event['status']}")
            print(f"   作成者: {event['creator']}")
            print(f"   主催者: {event['organizer']}")
            print(f"   作成日時: {event['created']}")
            print(f"   更新日時: {event['updated']}")
            print(f"   説明: {event['description'][:100]}..." if len(event['description']) > 100 else f"   説明: {event['description']}")
            print(f"   場所: {event['location']}")
            print(f"   可視性: {event['visibility']}")
            print(f"   透明度: {event['transparency']}")
            print(f"   繰り返しID: {event['recurringEventId']}")
            print(f"   元の開始時刻: {event['originalStartTime']}")
            print(f"   iCalUID: {event['iCalUID']}")
            print(f"   シーケンス: {event['sequence']}")
            print(f"   参加者数: {len(event['attendees'])}")
            print(f"   リマインダー: {event['reminders']}")
            print(f"   添付ファイル数: {len(event['attachments'])}")
            print(f"   イベントタイプ: {event['eventType']}")
            print(f"   ロック状態: {event['locked']}")
            print(f"   プライベートコピー: {event['privateCopy']}")
            print(f"   誰でも追加可能: {event['anyoneCanAddSelf']}")
            print(f"   ゲストが招待可能: {event['guestsCanInviteOthers']}")
            print(f"   ゲストが変更可能: {event['guestsCanModify']}")
            print(f"   ゲストが他のゲストを見れる: {event['guestsCanSeeOtherGuests']}")
            print(f"   参加者省略: {event['attendeesOmitted']}")
            print(f"   終了時刻未指定: {event['endTimeUnspecified']}")
            print(f"   HTMLリンク: {event['htmlLink']}")
            print(f"   Hangoutリンク: {event['hangoutLink']}")
            print(f"   会議データ: {event['conferenceData']}")
            print(f"   ガジェット: {event['gadget']}")
            print(f"   ソース: {event['source']}")
            print(f"   拡張プロパティ: {event['extendedProperties']}")
            print(f"   作業場所プロパティ: {event['workingLocationProperties']}")
            print(f"   外出先プロパティ: {event['outOfOfficeProperties']}")
            print(f"   集中時間プロパティ: {event['focusTimeProperties']}")
            print(f"   色ID: {event['colorId']}")
            print(f"   種類: {event['kind']}")
            print(f"   ETag: {event['etag']}")
            print(f"   繰り返しルール: {event['recurrence']}")
            print(f"   添付ファイル: {event['attachments']}")
            print(f"   生データ: {event['raw_event']}")
            print(f"{Colors.BLUE}{'-'*80}{Colors.END}")

def main():
    """メイン処理"""
    import sys
    
    if len(sys.argv) < 2:
        print(f"{Colors.RED}❌ 検索する日付を指定してください{Colors.END}")
        print("使用例: python deep_search_calendar.py 2025-10-27")
        return 1
    
    target_date = sys.argv[1]
    print(f"{Colors.BOLD}{Colors.CYAN}🔍 Googleカレンダー詳細検索{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}検索対象日付: {target_date}{Colors.END}")
    
    # 詳細検索実行
    search = DeepCalendarSearch()
    if not search.service:
        return 1
    
    events = search.search_all_events(target_date)
    search.display_events(events)
    
    return 0

if __name__ == "__main__":
    exit(main())
