#!/usr/bin/env python3
"""
システム状態取得テスト
メール送信なしでシステム状態を確認
"""

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

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
        "logs": [],
        "env_vars": {}
    }
    
    # 環境変数の確認
    env_vars = [
        "AUTO_CLASSIFY_INTERVAL",
        "AUTO_CLASSIFY_ENABLED", 
        "DAILY_SUMMARY_ENABLED",
        "DAILY_SUMMARY_TIME",
        "DAILY_REFLECTION_ENABLED",
        "DAILY_REFLECTION_TIME",
        "REPORT_EMAIL_ENABLED"
    ]
    
    for var in env_vars:
        status["env_vars"][var] = os.getenv(var, "未設定")
    
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

def print_system_status(status):
    """システム状態を表示"""
    print(f"{Colors.BOLD}{Colors.BLUE}📊 PRISM システム状態{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}日時: {status['timestamp']}{Colors.END}")
    print()
    
    # 環境変数
    print(f"{Colors.BOLD}{Colors.GREEN}🔧 環境変数設定{Colors.END}")
    print(f"{Colors.GREEN}{'='*40}{Colors.END}")
    for var, value in status["env_vars"].items():
        color = Colors.GREEN if value != "未設定" else Colors.YELLOW
        print(f"  {var}: {color}{value}{Colors.END}")
    print()
    
    # サービス状態
    print(f"{Colors.BOLD}{Colors.BLUE}⚙️  サービス状態{Colors.END}")
    print(f"{Colors.BLUE}{'='*40}{Colors.END}")
    if status["services"]:
        for service in status["services"]:
            print(f"  • {service}")
    else:
        print(f"  {Colors.YELLOW}サービス情報なし{Colors.END}")
    print()
    
    # ログファイル
    print(f"{Colors.BOLD}{Colors.MAGENTA}📝 ログファイル{Colors.END}")
    print(f"{Colors.MAGENTA}{'='*40}{Colors.END}")
    if status["logs"]:
        for log in status["logs"]:
            print(f"  • {log}")
    else:
        print(f"  {Colors.YELLOW}ログファイルなし{Colors.END}")
    print()
    
    # システム情報
    print(f"{Colors.BOLD}{Colors.CYAN}💻 システム情報{Colors.END}")
    print(f"{Colors.CYAN}{'='*40}{Colors.END}")
    print(f"  ホスト名: {os.uname().nodename}")
    print(f"  ユーザー: {os.getenv('USER', 'unknown')}")
    print(f"  作業ディレクトリ: {os.getcwd()}")
    print()

def main():
    """メイン処理"""
    print(f"{Colors.BOLD}{Colors.BLUE}🔍 PRISM システム状態確認{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # システム状態を取得
    print(f"{Colors.CYAN}📊 システム状態を取得中...{Colors.END}")
    status = get_system_status()
    
    # システム状態を表示
    print_system_status(status)
    
    print(f"{Colors.GREEN}✨ システム状態確認完了！{Colors.END}")
    return 0

if __name__ == "__main__":
    exit(main())

