#!/usr/bin/env python3
"""
セキュアなAPIキー生成ツール
"""
import secrets
import hashlib
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

def generate_secure_keys():
    """セキュアなキーを生成"""
    print("🔐 セキュアなキー生成ツール")
    print("=" * 50)
    
    # APIキーの生成
    api_key = secrets.token_urlsafe(32)
    print(f"🔑 API Key: {api_key}")
    
    # JWT秘密鍵の生成
    jwt_secret = secrets.token_urlsafe(32)
    print(f"🔐 JWT Secret: {jwt_secret}")
    
    # 暗号化キーの生成
    encryption_key = Fernet.generate_key().decode()
    print(f"🔒 Encryption Key: {encryption_key}")
    
    # ハッシュ化されたAPIキー
    hashed_api_key = hashlib.sha256(api_key.encode()).hexdigest()
    print(f"🔍 Hashed API Key: {hashed_api_key}")
    
    print("\n📝 .envファイルに追加する設定:")
    print("-" * 30)
    print(f"API_KEY={api_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    
    # .envファイルの更新
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"\n⚠️  {env_file}ファイルが存在します。")
        response = input("既存の設定を更新しますか？ (y/N): ")
        if response.lower() == 'y':
            update_env_file(env_file, api_key, jwt_secret, encryption_key)
            print("✅ .envファイルを更新しました。")
    else:
        print(f"\n📄 {env_file}ファイルが存在しません。")
        response = input("新しい.envファイルを作成しますか？ (y/N): ")
        if response.lower() == 'y':
            create_env_file(env_file, api_key, jwt_secret, encryption_key)
            print("✅ .envファイルを作成しました。")

def update_env_file(env_file, api_key, jwt_secret, encryption_key):
    """既存の.envファイルを更新"""
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # 既存の設定を更新
    updated_lines = []
    for line in lines:
        if line.startswith('API_KEY='):
            updated_lines.append(f'API_KEY={api_key}\n')
        elif line.startswith('JWT_SECRET_KEY='):
            updated_lines.append(f'JWT_SECRET_KEY={jwt_secret}\n')
        elif line.startswith('ENCRYPTION_KEY='):
            updated_lines.append(f'ENCRYPTION_KEY={encryption_key}\n')
        else:
            updated_lines.append(line)
    
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)

def create_env_file(env_file, api_key, jwt_secret, encryption_key):
    """新しい.envファイルを作成"""
    with open(env_file, 'w') as f:
        f.write(f"""# PRISM 環境変数
PRISM_ENV=development
API_KEY={api_key}
OPENAI_API_KEY=sk-your-openai-key
MCP_BASE_URL=http://localhost:8062

# セキュリティ設定
CORS_ORIGINS=http://localhost:8061,http://localhost:3000
JWT_SECRET_KEY={jwt_secret}
ENCRYPTION_KEY={encryption_key}

# ログ設定
LOG_LEVEL=INFO
LOG_HUMAN=1
LOG_FILE=logs/prism.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Notion
NOTION_API_KEY=your_notion_api_key_here
NOTION_TASK_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TODO_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 自動仕訳設定
AUTO_CLASSIFY_INTERVAL=120
AUTO_CLASSIFY_ENABLED=true

# 報告用メール設定
REPORT_EMAIL_ENABLED=false
REPORT_EMAIL_SMTP_HOST=smtp.gmail.com
REPORT_EMAIL_SMTP_PORT=587
REPORT_EMAIL_SMTP_USER=your-email@gmail.com
REPORT_EMAIL_SMTP_PASSWORD=your-app-password
REPORT_EMAIL_FROM=your-email@gmail.com
REPORT_EMAIL_TO=recipient@example.com

# 毎朝のタスク整理設定
DAILY_SUMMARY_ENABLED=true
DAILY_SUMMARY_TIME=08:00

# 毎夕の振り返り設定
DAILY_REFLECTION_ENABLED=true
DAILY_REFLECTION_TIME=18:00

# Google Calendar設定
GOOGLE_CALENDAR_ENABLED=false
GOOGLE_CALENDAR_SYNC_INTERVAL=300
GOOGLE_CALENDAR_ID=primary

# Worker設定
WORKER_INTERVAL=60
""")

if __name__ == "__main__":
    generate_secure_keys()
