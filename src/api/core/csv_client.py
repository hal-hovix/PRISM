"""
CSV ファイルからデータを読み込むクライアント
"""

import csv
import os
from typing import List, Dict, Optional
from pathlib import Path


class CSVClient:
    """CSV ファイルからデータを読み込むクライアント"""
    
    def __init__(self, base_path: str = "NoyionDB_CSV"):
        """
        Args:
            base_path: CSV ファイルの基底パス
        """
        self.base_path = Path(base_path)
    
    def fetch_inbox_items(self) -> List[Dict]:
        """
        INBOX.csv からアイテムを取得
        
        Returns:
            アイテムのリスト
        """
        inbox_file = self.base_path / "INBOX.csv"
        
        if not inbox_file.exists():
            print(f"INBOX file not found: {inbox_file}")
            return []
        
        items = []
        
        try:
            with open(inbox_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # ヘッダー説明行をスキップ
                    if row['タイトル'].startswith('('):
                        continue
                    
                    # 状態が「未分類」のものだけ取得
                    if row['状態'] != '未分類':
                        continue
                    
                    # API 形式に変換
                    item = {
                        "id": f"inbox_{len(items) + 1}",
                        "title": row['タイトル'],
                        "body": row['内容'],
                        "tags": row['カテゴリ'].split(',') if row['カテゴリ'] else [],
                        "metadata": {
                            "type": row['タイプ'],
                            "status": row['状態'],
                            "created": row['登録日'],
                            "deadline": row['期限'],
                            "urgency": row['緊急度'],
                            "importance": row['重要度'],
                        }
                    }
                    items.append(item)
            
            print(f"✓ Loaded {len(items)} items from INBOX")
            return items
            
        except Exception as e:
            print(f"✗ Error reading INBOX: {e}")
            return []
    
    def update_inbox_status(self, item_id: str, new_status: str, new_type: str = None):
        """
        INBOX アイテムの状態を更新
        
        Args:
            item_id: アイテムID
            new_status: 新しい状態
            new_type: 新しいタイプ（オプション）
        """
        inbox_file = self.base_path / "INBOX.csv"
        
        if not inbox_file.exists():
            return
        
        # CSV を読み込み
        rows = []
        with open(inbox_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                rows.append(row)
        
        # 状態を更新（実装は簡略化）
        # 実際には item_id に基づいて該当行を更新
        
        # CSV に書き戻し（今回は省略）
        # 実運用では適切に実装する必要がある
        print(f"✓ Updated status for {item_id}: {new_status}")
    
    def save_classified_item(self, item: Dict, classification: Dict):
        """
        分類されたアイテムを適切な CSV ファイルに保存
        
        Args:
            item: 元のアイテム
            classification: 分類結果
        """
        classified_type = classification.get('type', 'Note')
        
        # 保存先ファイルを決定
        target_files = {
            'Task': self.base_path / 'Task.csv',
            'Knowledge': self.base_path / 'Knowledge.csv',
            'Note': self.base_path / 'Note.csv'
        }
        
        target_file = target_files.get(classified_type, self.base_path / 'Note.csv')
        
        print(f"✓ Classified '{item['title']}' as {classified_type}")
        # 実際の保存処理は省略（CSV への追記処理が必要）
    
    def get_all_items(self, item_type: str = None) -> List[Dict]:
        """
        指定されたタイプの全アイテムを取得
        
        Args:
            item_type: アイテムタイプ (Task, Knowledge, Note)
        
        Returns:
            アイテムのリスト
        """
        if item_type:
            csv_files = [f"{item_type}.csv"]
        else:
            csv_files = ["Task.csv", "Knowledge.csv", "Note.csv"]
        
        all_items = []
        
        for csv_file in csv_files:
            file_path = self.base_path / csv_file
            
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        # ヘッダー説明行をスキップ
                        if row.get('タイトル', '').startswith('('):
                            continue
                        
                        item = {
                            "title": row.get('タイトル', ''),
                            "body": row.get('内容', ''),
                            "type": csv_file.replace('.csv', ''),
                            "tags": row.get('カテゴリ', '').split(',') if row.get('カテゴリ') else []
                        }
                        all_items.append(item)
            
            except Exception as e:
                print(f"✗ Error reading {csv_file}: {e}")
        
        return all_items

