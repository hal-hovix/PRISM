#!/usr/bin/env python3
"""
報告用メール機能
環境変数から設定を読み込んでメールを送信
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# 環境変数から設定を読み込み
REPORT_EMAIL_ENABLED = os.getenv("REPORT_EMAIL_ENABLED", "false").lower() == "true"
REPORT_EMAIL_SMTP_HOST = os.getenv("REPORT_EMAIL_SMTP_HOST", "smtp.gmail.com")
REPORT_EMAIL_SMTP_PORT = int(os.getenv("REPORT_EMAIL_SMTP_PORT", "587"))
REPORT_EMAIL_SMTP_USER = os.getenv("REPORT_EMAIL_SMTP_USER", "")
REPORT_EMAIL_SMTP_PASSWORD = os.getenv("REPORT_EMAIL_SMTP_PASSWORD", "")
REPORT_EMAIL_FROM = os.getenv("REPORT_EMAIL_FROM", "")
REPORT_EMAIL_TO = os.getenv("REPORT_EMAIL_TO", "")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def check_email_config():
    """メール設定の確認"""
    if not REPORT_EMAIL_ENABLED:
        print(f"{Colors.YELLOW}⚠️  報告用メールが無効になっています{Colors.END}")
        print("REPORT_EMAIL_ENABLED=true に設定してください")
        return False
    
    if not all([REPORT_EMAIL_SMTP_USER, REPORT_EMAIL_SMTP_PASSWORD, REPORT_EMAIL_FROM, REPORT_EMAIL_TO]):
        print(f"{Colors.RED}❌ メール設定が不完全です{Colors.END}")
        print("以下の環境変数を設定してください:")
        print("- REPORT_EMAIL_SMTP_USER")
        print("- REPORT_EMAIL_SMTP_PASSWORD")
        print("- REPORT_EMAIL_FROM")
        print("- REPORT_EMAIL_TO")
        return False
    
    return True

def get_system_status():
    """システムの状態を取得"""
    status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "services": [],
        "logs": []
    }
    
    # サービス状態を確認
    import subprocess
    try:
        result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'prism' in line:
                status["services"].append(line.strip())
    except Exception as e:
        status["services"].append(f"サービス状態取得エラー: {e}")
    
    # ログファイルの確認
    log_dir = "/Users/hal1956/development/PRISM/logs"
    if os.path.exists(log_dir):
        for log_file in os.listdir(log_dir):
            if log_file.endswith('.log'):
                log_path = os.path.join(log_dir, log_file)
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            status["logs"].append(f"{log_file}: {len(lines)}行")
                except Exception as e:
                    status["logs"].append(f"{log_file}: 読み込みエラー")
    
    return status

def create_email_content(status):
    """メール内容を作成"""
    content = f"""
PRISM システムレポート
====================

日時: {status['timestamp']}

サービス状態:
"""
    
    if status['services']:
        for service in status['services']:
            content += f"- {service}\n"
    else:
        content += "- サービス情報なし\n"
    
    content += "\nログファイル:\n"
    if status['logs']:
        for log in status['logs']:
            content += f"- {log}\n"
    else:
        content += "- ログファイルなし\n"
    
    content += f"""
システム情報:
- ホスト名: {os.uname().nodename}
- ユーザー: {os.getenv('USER', 'unknown')}
- 作業ディレクトリ: {os.getcwd()}

---
PRISM 自動化システム
"""
    
    return content

def send_email(subject, content):
    """メールを送信"""
    try:
        # メッセージを作成
        msg = MIMEMultipart()
        msg['From'] = REPORT_EMAIL_FROM
        msg['To'] = REPORT_EMAIL_TO
        msg['Subject'] = subject
        
        # 本文を追加
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        # SMTPサーバーに接続
        context = ssl.create_default_context()
        
        # ポート465の場合はSSL接続、587の場合はTLS接続
        if REPORT_EMAIL_SMTP_PORT == 465:
            with smtplib.SMTP_SSL(REPORT_EMAIL_SMTP_HOST, REPORT_EMAIL_SMTP_PORT, context=context) as server:
                server.login(REPORT_EMAIL_SMTP_USER, REPORT_EMAIL_SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(REPORT_EMAIL_SMTP_HOST, REPORT_EMAIL_SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(REPORT_EMAIL_SMTP_USER, REPORT_EMAIL_SMTP_PASSWORD)
                server.send_message(msg)
        
        print(f"{Colors.GREEN}✅ メール送信成功{Colors.END}")
        print(f"送信先: {REPORT_EMAIL_TO}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ メール送信エラー: {e}{Colors.END}")
        return False

def main():
    """メイン処理"""
    print(f"{Colors.BOLD}{Colors.BLUE}📧 PRISM 報告用メール{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    
    # メール設定の確認
    if not check_email_config():
        return 1
    
    print(f"{Colors.CYAN}📋 メール設定:{Colors.END}")
    print(f"  SMTPホスト: {REPORT_EMAIL_SMTP_HOST}:{REPORT_EMAIL_SMTP_PORT}")
    print(f"  送信者: {REPORT_EMAIL_FROM}")
    print(f"  宛先: {REPORT_EMAIL_TO}")
    print()
    
    # システム状態を取得
    print(f"{Colors.CYAN}📊 システム状態を取得中...{Colors.END}")
    status = get_system_status()
    
    # メール内容を作成
    subject = f"PRISM システムレポート - {status['timestamp']}"
    content = create_email_content(status)
    
    # メールを送信
    print(f"{Colors.CYAN}📧 メール送信中...{Colors.END}")
    success = send_email(subject, content)
    
    if success:
        print(f"{Colors.GREEN}✨ 報告メール送信完了！{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}❌ 報告メール送信失敗{Colors.END}")
        return 1

if __name__ == "__main__":
    exit(main())
