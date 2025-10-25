#!/usr/bin/env python3
"""
PRISM テスト実行スクリプト
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description):
    """コマンドを実行して結果を表示"""
    print(f"\n🔧 {description}")
    print(f"実行中: {command}")
    print("-" * 60)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - 成功")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - 失敗")
        if result.stderr:
            print(f"エラー: {result.stderr}")
        if result.stdout:
            print(f"出力: {result.stdout}")
    
    return result.returncode == 0

def run_tests(test_type="all", coverage=False, verbose=False):
    """テストを実行"""
    print("🧪 PRISM テストスイート実行")
    print("=" * 60)
    
    # テストディレクトリに移動
    os.chdir(Path(__file__).parent.parent)
    
    # pytestコマンドを構築
    pytest_cmd = "python -m pytest"
    
    if verbose:
        pytest_cmd += " -v"
    else:
        pytest_cmd += " -q"
    
    if coverage:
        pytest_cmd += " --cov=src --cov-report=html --cov-report=term"
    
    # テストタイプに応じてコマンドを調整
    if test_type == "unit":
        pytest_cmd += " tests/unit/"
    elif test_type == "integration":
        pytest_cmd += " tests/integration/"
    elif test_type == "async":
        pytest_cmd += " -m async"
    elif test_type == "performance":
        pytest_cmd += " -m performance"
    elif test_type == "api":
        pytest_cmd += " -m api"
    else:
        pytest_cmd += " tests/"
    
    # テスト実行
    success = run_command(pytest_cmd, f"{test_type}テストの実行")
    
    if coverage and success:
        print(f"\n📊 カバレッジレポートが生成されました: htmlcov/index.html")
    
    return success

def run_linting():
    """リンティングを実行"""
    print("\n🔍 コードリンティング実行")
    print("=" * 60)
    
    # flake8でリンティング
    flake8_cmd = "python -m flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503"
    success1 = run_command(flake8_cmd, "flake8リンティング")
    
    # mypyで型チェック
    mypy_cmd = "python -m mypy src/ --ignore-missing-imports"
    success2 = run_command(mypy_cmd, "mypy型チェック")
    
    return success1 and success2

def run_security_check():
    """セキュリティチェックを実行"""
    print("\n🔒 セキュリティチェック実行")
    print("=" * 60)
    
    # banditでセキュリティチェック
    bandit_cmd = "python -m bandit -r src/ -f json -o security_report.json"
    success1 = run_command(bandit_cmd, "banditセキュリティチェック")
    
    # safetyで依存関係チェック
    safety_cmd = "python -m safety check --json --output safety_report.json"
    success2 = run_command(safety_cmd, "safety依存関係チェック")
    
    return success1 and success2

def run_performance_test():
    """パフォーマンステストを実行"""
    print("\n⚡ パフォーマンステスト実行")
    print("=" * 60)
    
    # パフォーマンステストスクリプトを実行
    perf_cmd = "python tools/performance_test.py"
    success = run_command(perf_cmd, "パフォーマンステスト")
    
    return success

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="PRISM テストスイート")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "async", "performance", "api"],
        default="all",
        help="実行するテストのタイプ"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="カバレッジレポートを生成"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="詳細な出力"
    )
    parser.add_argument(
        "--lint", 
        action="store_true",
        help="リンティングも実行"
    )
    parser.add_argument(
        "--security", 
        action="store_true",
        help="セキュリティチェックも実行"
    )
    parser.add_argument(
        "--performance", 
        action="store_true",
        help="パフォーマンステストも実行"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="すべてのチェックを実行"
    )
    
    args = parser.parse_args()
    
    # すべてのチェックを実行する場合
    if args.all:
        print("🚀 全チェック実行モード")
        print("=" * 60)
        
        # テスト実行
        test_success = run_tests(args.type, args.coverage, args.verbose)
        
        # リンティング
        lint_success = run_linting()
        
        # セキュリティチェック
        security_success = run_security_check()
        
        # パフォーマンステスト
        perf_success = run_performance_test()
        
        # 結果サマリー
        print("\n📋 実行結果サマリー")
        print("=" * 60)
        print(f"テスト: {'✅ 成功' if test_success else '❌ 失敗'}")
        print(f"リンティング: {'✅ 成功' if lint_success else '❌ 失敗'}")
        print(f"セキュリティ: {'✅ 成功' if security_success else '❌ 失敗'}")
        print(f"パフォーマンス: {'✅ 成功' if perf_success else '❌ 失敗'}")
        
        overall_success = test_success and lint_success and security_success and perf_success
        print(f"\n🎯 全体結果: {'✅ すべて成功' if overall_success else '❌ 一部失敗'}")
        
        return 0 if overall_success else 1
    
    # 個別実行
    success = True
    
    # テスト実行
    if not run_tests(args.type, args.coverage, args.verbose):
        success = False
    
    # リンティング
    if args.lint and not run_linting():
        success = False
    
    # セキュリティチェック
    if args.security and not run_security_check():
        success = False
    
    # パフォーマンステスト
    if args.performance and not run_performance_test():
        success = False
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
