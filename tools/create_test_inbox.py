#!/usr/bin/env python3
"""
テスト用のINBOXアイテムを作成するスクリプト
"""

import os
import requests
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# 環境変数から設定を読み込み
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
INBOX_DATABASE_ID = os.getenv("NOTION_TASK_DB_ID", "2935fbef07e28074bdf8f9c06755f45a")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def create_test_inbox_item(title, description=""):
    """テスト用のINBOXアイテムを作成"""
    url = f"https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": INBOX_DATABASE_ID},
        "properties": {
            "タスク名": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "説明": {
                "rich_text": [
                    {
                        "text": {
                            "content": description
                        }
                    }
                ]
            },
            "ステータス": {
                "select": {
                    "name": "INBOX"
                }
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ INBOXアイテム作成: {title}{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}❌ INBOXアイテム作成エラー: {response.status_code}{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ INBOXアイテム作成例外: {e}{Colors.END}")
        return False

def main():
    """メイン処理"""
    print(f"{Colors.CYAN}📝 テスト用INBOXアイテム作成{Colors.END}")
    
    test_items = [
        ("明日の会議 10:00", "プロジェクト会議の準備"),
        ("2025/10/26 病院受診", "定期健診"),
        ("来週のプレゼン準備", "資料作成"),
        ("明後日 歯医者", "定期検診"),
        ("2025-10-30 打ち合わせ", "クライアントとの打ち合わせ")
    ]
    
    created_count = 0
    for title, description in test_items:
        if create_test_inbox_item(title, description):
            created_count += 1
    
    print(f"{Colors.CYAN}📊 作成完了: {created_count}/{len(test_items)}件{Colors.END}")

if __name__ == "__main__":
    main()
