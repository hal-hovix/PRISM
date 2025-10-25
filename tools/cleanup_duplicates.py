#!/usr/bin/env python3
"""
重複データクリーンアップスクリプト
Taskデータベースから重複項目を削除し、最新の1件のみを保持する
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Notion API設定
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
TASK_DB_ID = os.getenv('NOTION_TASK_DB_ID')

if not NOTION_API_KEY or not TASK_DB_ID:
    print("❌ 環境変数が設定されていません")
    print("NOTION_API_KEY と NOTION_TASK_DB_ID を確認してください")
    sys.exit(1)

# Notion API ヘッダー
headers = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

def get_all_tasks():
    """Taskデータベースから全項目を取得"""
    print("📋 Taskデータベースから全項目を取得中...")
    
    all_tasks = []
    has_more = True
    start_cursor = None
    
    while has_more:
        url = f"https://api.notion.com/v1/databases/{TASK_DB_ID}/query"
        
        payload = {
            "page_size": 100
        }
        
        if start_cursor:
            payload["start_cursor"] = start_cursor
            
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ API エラー: {response.status_code}")
            print(response.text)
            return []
            
        data = response.json()
        all_tasks.extend(data['results'])
        
        has_more = data['has_more']
        start_cursor = data.get('next_cursor')
        
    print(f"✅ 取得完了: {len(all_tasks)}件")
    return all_tasks

def group_by_title(tasks):
    """タイトル別にグループ化"""
    groups = {}
    
    for task in tasks:
        title_prop = task['properties'].get('タスク名', {})
        if title_prop.get('title') and len(title_prop['title']) > 0:
            title = title_prop['title'][0]['text']['content']
            
            if title not in groups:
                groups[title] = []
            
            groups[title].append({
                'id': task['id'],
                'title': title,
                'created_time': task['created_time'],
                'last_edited_time': task['last_edited_time']
            })
    
    return groups

def find_duplicates(groups):
    """重複項目を特定（2件以上あるもの）"""
    duplicates = {}
    
    for title, tasks in groups.items():
        if len(tasks) > 1:
            # 作成時間でソート（最新を保持）
            tasks.sort(key=lambda x: x['created_time'], reverse=True)
            duplicates[title] = {
                'keep': tasks[0],  # 最新の1件を保持
                'delete': tasks[1:]  # 残りを削除対象
            }
    
    return duplicates

def delete_tasks_by_ids(task_ids):
    """指定されたIDのタスクを削除"""
    deleted_count = 0
    
    for task_id in task_ids:
        url = f"https://api.notion.com/v1/pages/{task_id}"
        
        # ページをアーカイブ（削除）
        payload = {
            "archived": True
        }
        
        response = requests.patch(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            deleted_count += 1
            print(f"  ✅ 削除: {task_id}")
        else:
            print(f"  ❌ 削除失敗: {task_id} - {response.status_code}")
            print(f"     {response.text}")
    
    return deleted_count

def main():
    print("🧹 Taskデータベース重複クリーンアップ開始")
    print("=" * 50)
    
    # 全タスクを取得
    all_tasks = get_all_tasks()
    if not all_tasks:
        print("❌ タスクの取得に失敗しました")
        return
    
    # タイトル別にグループ化
    groups = group_by_title(all_tasks)
    print(f"📊 タイトル別グループ数: {len(groups)}")
    
    # 重複項目を特定
    duplicates = find_duplicates(groups)
    
    if not duplicates:
        print("✅ 重複項目は見つかりませんでした")
        return
    
    print(f"🚨 重複項目発見: {len(duplicates)}種類")
    print()
    
    total_deleted = 0
    
    for title, data in duplicates.items():
        keep_task = data['keep']
        delete_tasks = data['delete']
        
        print(f"📝 '{title}'")
        print(f"  保持: {keep_task['id']} (作成: {keep_task['created_time']})")
        print(f"  削除: {len(delete_tasks)}件")
        
        # 削除実行
        delete_ids = [task['id'] for task in delete_tasks]
        deleted_count = delete_tasks_by_ids(delete_ids)
        total_deleted += deleted_count
        
        print(f"  ✅ 削除完了: {deleted_count}/{len(delete_tasks)}件")
        print()
    
    print("=" * 50)
    print(f"🎉 クリーンアップ完了!")
    print(f"📊 削除件数: {total_deleted}件")
    print(f"📊 重複種類: {len(duplicates)}種類")

if __name__ == "__main__":
    main()
