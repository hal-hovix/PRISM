#!/usr/bin/env python3
"""
NotionDBの内容を確認するツール
"""

import os
import requests
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# 環境変数から設定を読み込み
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
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

class NotionDBChecker:
    def __init__(self):
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def get_database_items(self, database_id, database_name):
        """データベースのアイテムを取得（全件取得）"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        items = []
        has_more = True
        start_cursor = None
        
        while has_more:
            query_data = {}
            if start_cursor:
                query_data["start_cursor"] = start_cursor
            
            response = requests.post(url, headers=self.notion_headers, json=query_data)
            if response.status_code != 200:
                print(f"{Colors.RED}❌ {database_name}取得エラー: {response.status_code}{Colors.END}")
                break
            
            data = response.json()
            
            for page in data.get('results', []):
                item = {
                    'id': page['id'],
                    'title': self.extract_title(page, database_name),
                    'date': self.extract_date(page, database_name),
                    'status': self.extract_status(page),
                    'created_time': page.get('created_time', '')
                }
                items.append(item)
            
            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')
        
        return items
    
    def extract_title(self, page, database_name):
        """ページからタイトルを抽出"""
        properties = page.get('properties', {})
        
        if database_name == "Task":
            if 'タスク名' in properties:
                title_prop = properties['タスク名']
                if title_prop['type'] == 'title' and title_prop['title']:
                    return title_prop['title'][0]['text']['content']
        else:  # ToDo
            if 'ToDo名' in properties:
                title_prop = properties['ToDo名']
                if title_prop['type'] == 'title' and title_prop['title']:
                    return title_prop['title'][0]['text']['content']
        
        return "タイトルなし"
    
    def extract_date(self, page, database_name):
        """ページから日付を抽出"""
        properties = page.get('properties', {})
        
        if database_name == "Task":
            if '期日' in properties:
                date_prop = properties['期日']
                if date_prop['type'] == 'date' and date_prop['date']:
                    return date_prop['date']['start']
        else:  # ToDo
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
    
    def find_duplicates(self, items):
        """重複アイテムを検出"""
        title_count = {}
        duplicates = []
        
        for item in items:
            title = item['title']
            if title in title_count:
                title_count[title].append(item)
            else:
                title_count[title] = [item]
        
        for title, items_list in title_count.items():
            if len(items_list) > 1:
                duplicates.append({
                    'title': title,
                    'count': len(items_list),
                    'items': items_list
                })
        
        return duplicates
    
    def delete_item(self, item_id):
        """アイテムを削除"""
        url = f"https://api.notion.com/v1/pages/{item_id}"
        
        data = {
            "archived": True
        }
        
        response = requests.patch(url, headers=self.notion_headers, json=data)
        if response.status_code == 200:
            return True
        else:
            print(f"{Colors.RED}❌ 削除エラー: {response.status_code}{Colors.END}")
            return False
    
    def cleanup_duplicates(self, duplicates):
        """重複アイテムをクリーンアップ（最初の1つ以外を削除）"""
        deleted_count = 0
        
        for duplicate in duplicates:
            print(f"{Colors.YELLOW}重複発見: {duplicate['title']} ({duplicate['count']}件){Colors.END}")
            
            # 最初の1つ以外を削除
            items_to_delete = duplicate['items'][1:]
            
            for item in items_to_delete:
                print(f"  削除中: {item['id']}")
                if self.delete_item(item['id']):
                    deleted_count += 1
                    print(f"  {Colors.GREEN}✅ 削除完了{Colors.END}")
                else:
                    print(f"  {Colors.RED}❌ 削除失敗{Colors.END}")
        
        return deleted_count

def main():
    """メイン処理"""
    import sys
    
    print(f"{Colors.BOLD}{Colors.BLUE}📊 NotionDB データベース確認ツール{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 設定確認
    if not NOTION_API_KEY:
        print(f"{Colors.RED}❌ Notion APIキーが設定されていません{Colors.END}")
        return 1
    
    checker = NotionDBChecker()
    
    # Taskデータベースを確認
    if TASK_DATABASE_ID:
        print(f"{Colors.CYAN}📋 Taskデータベース確認中...{Colors.END}")
        task_items = checker.get_database_items(TASK_DATABASE_ID, "Task")
        print(f"{Colors.BLUE}Taskデータベース: {len(task_items)}件{Colors.END}")
        
        # 重複チェック
        task_duplicates = checker.find_duplicates(task_items)
        if task_duplicates:
            print(f"{Colors.YELLOW}⚠️  Taskデータベースに重複: {len(task_duplicates)}種類{Colors.END}")
            
            for duplicate in task_duplicates:
                print(f"  - {duplicate['title']}: {duplicate['count']}件")
            
            # コマンドライン引数でクリーンアップ実行
            if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
                print(f"{Colors.CYAN}🧹 重複データをクリーンアップ中...{Colors.END}")
                deleted_count = checker.cleanup_duplicates(task_duplicates)
                print(f"{Colors.GREEN}✨ クリーンアップ完了: {deleted_count}件削除{Colors.END}")
        else:
            print(f"{Colors.GREEN}✅ Taskデータベースに重複なし{Colors.END}")
    
    # ToDoデータベースを確認
    if TODO_DATABASE_ID:
        print(f"{Colors.CYAN}📝 ToDoデータベース確認中...{Colors.END}")
        todo_items = checker.get_database_items(TODO_DATABASE_ID, "ToDo")
        print(f"{Colors.BLUE}ToDoデータベース: {len(todo_items)}件{Colors.END}")
        
        # 重複チェック
        todo_duplicates = checker.find_duplicates(todo_items)
        if todo_duplicates:
            print(f"{Colors.YELLOW}⚠️  ToDoデータベースに重複: {len(todo_duplicates)}種類{Colors.END}")
            
            for duplicate in todo_duplicates:
                print(f"  - {duplicate['title']}: {duplicate['count']}件")
            
            # コマンドライン引数でクリーンアップ実行
            if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
                print(f"{Colors.CYAN}🧹 重複データをクリーンアップ中...{Colors.END}")
                deleted_count = checker.cleanup_duplicates(todo_duplicates)
                print(f"{Colors.GREEN}✨ クリーンアップ完了: {deleted_count}件削除{Colors.END}")
        else:
            print(f"{Colors.GREEN}✅ ToDoデータベースに重複なし{Colors.END}")
    
    return 0

if __name__ == "__main__":
    exit(main())
