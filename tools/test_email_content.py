#!/usr/bin/env python3
"""
メール送信テスト（システム状態取得のみ）
メール送信なしでシステム状態を確認
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import subprocess
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

def get_system_status():
    """システムの状態を取得"""
    status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "services": [],
        "logs": []
    }
    
    # サービス状態を確認
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

def test_email_content(status):
    """メール内容をテスト（送信なし）"""
    print(f"{Colors.BOLD}{Colors.BLUE}📧 メール内容テスト{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    
    # メール内容を作成
    subject = f"PRISM システムレポート - {status['timestamp']}"
    content = create_email_content(status)
    
    print(f"{Colors.CYAN}件名: {subject}{Colors.END}")
    print()
    print(f"{Colors.CYAN}内容:{Colors.END}")
    print(content)
    
    return subject, content

def main():
    """メイン処理"""
    print(f"{Colors.BOLD}{Colors.BLUE}📧 PRISM メール送信テスト{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # メール設定の確認
    print(f"{Colors.CYAN}📋 メール設定:{Colors.END}")
    print(f"  有効: {Colors.GREEN if REPORT_EMAIL_ENABLED else Colors.RED}{REPORT_EMAIL_ENABLED}{Colors.END}")
    print(f"  SMTPホスト: {REPORT_EMAIL_SMTP_HOST}:{REPORT_EMAIL_SMTP_PORT}")
    print(f"  送信者: {REPORT_EMAIL_FROM}")
    print(f"  宛先: {REPORT_EMAIL_TO}")
    print()
    
    # システム状態を取得
    print(f"{Colors.CYAN}📊 システム状態を取得中...{Colors.END}")
    status = get_system_status()
    
    # メール内容をテスト
    subject, content = test_email_content(status)
    
    print()
    print(f"{Colors.GREEN}✨ メール内容テスト完了！{Colors.END}")
    print(f"{Colors.YELLOW}注意: 実際のメール送信はGmailのアプリパスワードが必要です{Colors.END}")
    return 0

if __name__ == "__main__":
    exit(main())

