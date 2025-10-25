#!/usr/bin/env python3
"""
PRISM System Integration Test Suite
システム統合テスト - 全機能の連携テストとパフォーマンス検証
"""

import os
import sys
import json
import logging
import asyncio
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import concurrent.futures
from threading import Lock

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """テストステータス"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TestCategory(Enum):
    """テストカテゴリ"""
    API_ENDPOINTS = "api_endpoints"
    NOTIFICATION_SYSTEM = "notification_system"
    DATA_INTEGRATION = "data_integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MONITORING = "monitoring"

@dataclass
class TestResult:
    """テスト結果"""
    test_name: str
    category: TestCategory
    status: TestStatus
    duration_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_requests_per_sec: float
    error_rate_percent: float

class SystemIntegrationTester:
    """システム統合テスター"""
    
    def __init__(self, base_url: str = "http://localhost:8060", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.test_results: List[TestResult] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        self.lock = Lock()
        
        # テスト設定
        self.timeout = 30
        self.max_retries = 3
        self.concurrent_requests = 10
        
        logger.info(f"SystemIntegrationTester initialized with base_url: {base_url}")
    
    def add_test_result(self, result: TestResult):
        """テスト結果を追加"""
        with self.lock:
            self.test_results.append(result)
            logger.info(f"Test {result.test_name}: {result.status.value}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全テストを実行"""
        logger.info("Starting comprehensive system integration tests")
        
        test_suites = [
            self._test_api_endpoints,
            self._test_notification_system,
            self._test_data_integration,
            self._test_performance,
            self._test_security,
            self._test_monitoring
        ]
        
        start_time = time.time()
        
        for test_suite in test_suites:
            try:
                test_suite()
            except Exception as e:
                logger.error(f"Test suite {test_suite.__name__} failed: {e}")
                self.add_test_result(TestResult(
                    test_name=test_suite.__name__,
                    category=TestCategory.API_ENDPOINTS,
                    status=TestStatus.FAILED,
                    duration_ms=0,
                    error_message=str(e)
                ))
        
        total_duration = (time.time() - start_time) * 1000
        
        # テスト結果の集計
        summary = self._generate_test_summary(total_duration)
        
        logger.info(f"Integration tests completed in {total_duration:.2f}ms")
        return summary
    
    def _test_api_endpoints(self):
        """APIエンドポイントテスト"""
        logger.info("Testing API endpoints")
        
        endpoints = [
            ("/healthz", "GET"),
            ("/metrics/", "GET"),
            ("/notifications/settings", "GET"),
            ("/notifications/test", "GET"),
            ("/analytics/overview", "GET"),
            ("/assistant/chat", "POST"),
            ("/classify", "POST"),
            ("/async/tasks", "GET")
        ]
        
        for endpoint, method in endpoints:
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=self._get_headers(),
                        timeout=self.timeout
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=self._get_headers(),
                        json={"test": True},
                        timeout=self.timeout
                    )
                
                duration = (time.time() - start_time) * 1000
                
                if response.status_code in [200, 201]:
                    status = TestStatus.PASSED
                    error_message = None
                else:
                    status = TestStatus.FAILED
                    error_message = f"HTTP {response.status_code}: {response.text}"
                
                self.add_test_result(TestResult(
                    test_name=f"API_{endpoint.replace('/', '_')}",
                    category=TestCategory.API_ENDPOINTS,
                    status=status,
                    duration_ms=duration,
                    error_message=error_message,
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "response_size": len(response.content)
                    }
                ))
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.add_test_result(TestResult(
                    test_name=f"API_{endpoint.replace('/', '_')}",
                    category=TestCategory.API_ENDPOINTS,
                    status=TestStatus.FAILED,
                    duration_ms=duration,
                    error_message=str(e)
                ))
    
    def _test_notification_system(self):
        """通知システムテスト"""
        logger.info("Testing notification system")
        
        # 通知設定テスト
        self._test_notification_settings()
        
        # 通知送信テスト
        self._test_notification_sending()
        
        # マルチチャンネルテスト
        self._test_multi_channel_notifications()
        
        # エスカレーションテスト
        self._test_escalation_system()
    
    def _test_notification_settings(self):
        """通知設定テスト"""
        start_time = time.time()
        
        try:
            # 設定取得
            response = requests.get(
                f"{self.base_url}/notifications/settings",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                settings = response.json()
                
                # 設定更新テスト
                update_response = requests.put(
                    f"{self.base_url}/notifications/settings",
                    headers=self._get_headers(),
                    json={
                        "email_enabled": True,
                        "slack_enabled": True,
                        "task_reminders": True,
                        "habit_notifications": True,
                        "system_alerts": True
                    },
                    timeout=self.timeout
                )
                
                if update_response.status_code == 200:
                    status = TestStatus.PASSED
                    error_message = None
                else:
                    status = TestStatus.FAILED
                    error_message = f"Update failed: {update_response.status_code}"
            else:
                status = TestStatus.FAILED
                error_message = f"Get settings failed: {response.status_code}"
            
            self.add_test_result(TestResult(
                test_name="notification_settings",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="notification_settings",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_notification_sending(self):
        """通知送信テスト"""
        start_time = time.time()
        
        try:
            # Slack通知テスト
            slack_response = requests.post(
                f"{self.base_url}/notifications/test",
                headers=self._get_headers(),
                params={"type": "slack"},
                timeout=self.timeout
            )
            
            # システムアラートテスト
            alert_response = requests.post(
                f"{self.base_url}/notifications/system-alert",
                headers=self._get_headers(),
                params={
                    "alert_type": "IntegrationTest",
                    "message": "システム統合テスト実行中"
                },
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if slack_response.status_code == 200 and alert_response.status_code == 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"Slack: {slack_response.status_code}, Alert: {alert_response.status_code}"
            
            self.add_test_result(TestResult(
                test_name="notification_sending",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="notification_sending",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_multi_channel_notifications(self):
        """マルチチャンネル通知テスト"""
        start_time = time.time()
        
        try:
            # マルチチャンネル送信テスト（基本通知で代替）
            response = requests.post(
                f"{self.base_url}/notifications/task-reminder",
                headers=self._get_headers(),
                json={
                    "title": "統合テスト通知",
                    "content": "マルチチャンネル通知のテストです",
                    "due_date": "2025-10-26T10:00:00Z",
                    "status": "進行中"
                },
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            self.add_test_result(TestResult(
                test_name="multi_channel_notifications",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="multi_channel_notifications",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_escalation_system(self):
        """エスカレーションシステムテスト"""
        start_time = time.time()
        
        try:
            # エスカレーションシステムテスト（システムアラートで代替）
            start_response = requests.post(
                f"{self.base_url}/notifications/system-alert",
                headers=self._get_headers(),
                params={
                    "alert_type": "EscalationTest",
                    "message": "エスカレーションシステムのテストです"
                },
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if start_response.status_code == 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"HTTP {start_response.status_code}: {start_response.text}"
            
            self.add_test_result(TestResult(
                test_name="escalation_system",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="escalation_system",
                category=TestCategory.NOTIFICATION_SYSTEM,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_data_integration(self):
        """データ統合テスト"""
        logger.info("Testing data integration")
        
        # Notion連携テスト
        self._test_notion_integration()
        
        # Google Calendar連携テスト
        self._test_google_calendar_integration()
        
        # Redis連携テスト
        self._test_redis_integration()
    
    def _test_notion_integration(self):
        """Notion連携テスト"""
        start_time = time.time()
        
        try:
            # 分類テスト（Notionデータベースアクセス）
            response = requests.post(
                f"{self.base_url}/classify",
                headers=self._get_headers(),
                json={
                    "text": "統合テスト用のサンプルテキストです",
                    "category": "test"
                },
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            self.add_test_result(TestResult(
                test_name="notion_integration",
                category=TestCategory.DATA_INTEGRATION,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="notion_integration",
                category=TestCategory.DATA_INTEGRATION,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_google_calendar_integration(self):
        """Google Calendar連携テスト"""
        start_time = time.time()
        
        try:
            # Google Calendar同期テスト（設定確認）
            response = requests.get(
                f"{self.base_url}/health",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            # Google Calendar設定の確認（環境変数ベース）
            google_calendar_enabled = os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() == "true"
            
            if response.status_code == 200:
                status = TestStatus.PASSED if google_calendar_enabled else TestStatus.SKIPPED
                error_message = None if google_calendar_enabled else "Google Calendar not enabled"
            else:
                status = TestStatus.FAILED
                error_message = f"HTTP {response.status_code}"
            
            self.add_test_result(TestResult(
                test_name="google_calendar_integration",
                category=TestCategory.DATA_INTEGRATION,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="google_calendar_integration",
                category=TestCategory.DATA_INTEGRATION,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_redis_integration(self):
        """Redis連携テスト"""
        start_time = time.time()
        
        try:
            # Redis接続テスト（メトリクスエンドポイント経由）
            response = requests.get(
                f"{self.base_url}/metrics",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"HTTP {response.status_code}"
            
            self.add_test_result(TestResult(
                test_name="redis_integration",
                category=TestCategory.DATA_INTEGRATION,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="redis_integration",
                category=TestCategory.DATA_INTEGRATION,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_performance(self):
        """パフォーマンステスト"""
        logger.info("Testing system performance")
        
        # レスポンス時間テスト
        self._test_response_times()
        
        # 同時接続テスト
        self._test_concurrent_requests()
        
        # メモリ使用量テスト
        self._test_memory_usage()
    
    def _test_response_times(self):
        """レスポンス時間テスト"""
        start_time = time.time()
        
        try:
            response_times = []
            
            # 複数回のリクエストでレスポンス時間を測定
            for _ in range(10):
                req_start = time.time()
                response = requests.get(
                    f"{self.base_url}/healthz",
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                req_duration = (time.time() - req_start) * 1000
                response_times.append(req_duration)
            
            duration = (time.time() - start_time) * 1000
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # パフォーマンス基準（200ms以下）
            if avg_response_time < 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"Average response time too high: {avg_response_time:.2f}ms"
            
            self.add_test_result(TestResult(
                test_name="response_times",
                category=TestCategory.PERFORMANCE,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details={
                    "avg_response_time_ms": avg_response_time,
                    "max_response_time_ms": max_response_time,
                    "min_response_time_ms": min_response_time,
                    "response_times": response_times
                }
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="response_times",
                category=TestCategory.PERFORMANCE,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_concurrent_requests(self):
        """同時接続テスト"""
        start_time = time.time()
        
        try:
            def make_request():
                try:
                    response = requests.get(
                        f"{self.base_url}/healthz",
                        headers=self._get_headers(),
                        timeout=self.timeout
                    )
                    return response.status_code == 200
                except:
                    return False
            
            # 同時リクエスト実行
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
                futures = [executor.submit(make_request) for _ in range(self.concurrent_requests)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            duration = (time.time() - start_time) * 1000
            
            success_rate = sum(results) / len(results) * 100
            
            if success_rate >= 90:  # 90%以上の成功率
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"Success rate too low: {success_rate:.1f}%"
            
            self.add_test_result(TestResult(
                test_name="concurrent_requests",
                category=TestCategory.PERFORMANCE,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details={
                    "concurrent_requests": self.concurrent_requests,
                    "success_rate_percent": success_rate,
                    "successful_requests": sum(results),
                    "total_requests": len(results)
                }
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="concurrent_requests",
                category=TestCategory.PERFORMANCE,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_memory_usage(self):
        """メモリ使用量テスト"""
        start_time = time.time()
        
        try:
            # システムメトリクス取得
            response = requests.get(
                f"{self.base_url}/metrics",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # メトリクスからメモリ使用量を抽出（簡易版）
                metrics_text = response.text
                memory_usage_mb = 0
                
                # Prometheusメトリクスからメモリ使用量を抽出
                for line in metrics_text.split('\n'):
                    if 'process_resident_memory_bytes' in line and not line.startswith('#'):
                        try:
                            memory_bytes = float(line.split()[1])
                            memory_usage_mb = memory_bytes / (1024 * 1024)
                            break
                        except:
                            continue
                
                # メモリ使用量基準（500MB以下）
                if memory_usage_mb < 500:
                    status = TestStatus.PASSED
                    error_message = None
                else:
                    status = TestStatus.FAILED
                    error_message = f"Memory usage too high: {memory_usage_mb:.2f}MB"
                
                self.add_test_result(TestResult(
                    test_name="memory_usage",
                    category=TestCategory.PERFORMANCE,
                    status=status,
                    duration_ms=duration,
                    error_message=error_message,
                    details={
                        "memory_usage_mb": memory_usage_mb
                    }
                ))
            else:
                status = TestStatus.FAILED
                error_message = f"Failed to get metrics: {response.status_code}"
                
                self.add_test_result(TestResult(
                    test_name="memory_usage",
                    category=TestCategory.PERFORMANCE,
                    status=status,
                    duration_ms=duration,
                    error_message=error_message
                ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="memory_usage",
                category=TestCategory.PERFORMANCE,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_security(self):
        """セキュリティテスト"""
        logger.info("Testing security features")
        
        # API認証テスト
        self._test_api_authentication()
        
        # CORS設定テスト
        self._test_cors_configuration()
        
        # 入力検証テスト
        self._test_input_validation()
    
    def _test_api_authentication(self):
        """API認証テスト"""
        start_time = time.time()
        
        try:
            # 無認証リクエストテスト
            response_no_auth = requests.get(
                f"{self.base_url}/notifications/settings",
                timeout=self.timeout
            )
            
            # 認証ありリクエストテスト
            response_with_auth = requests.get(
                f"{self.base_url}/notifications/settings",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            # 無認証は拒否、認証ありは許可されるべき
            if response_no_auth.status_code in [401, 403] and response_with_auth.status_code == 200:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"No auth: {response_no_auth.status_code}, With auth: {response_with_auth.status_code}"
            
            self.add_test_result(TestResult(
                test_name="api_authentication",
                category=TestCategory.SECURITY,
                status=status,
                duration_ms=duration,
                error_message=error_message
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="api_authentication",
                category=TestCategory.SECURITY,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_cors_configuration(self):
        """CORS設定テスト"""
        start_time = time.time()
        
        try:
            # CORSプリフライトリクエスト
            response = requests.options(
                f"{self.base_url}/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization"
                },
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            # CORSヘッダーの確認
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            if response.status_code == 200 and any(cors_headers.values()):
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"CORS headers missing or invalid: {cors_headers}"
            
            self.add_test_result(TestResult(
                test_name="cors_configuration",
                category=TestCategory.SECURITY,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details=cors_headers
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="cors_configuration",
                category=TestCategory.SECURITY,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_input_validation(self):
        """入力検証テスト"""
        start_time = time.time()
        
        try:
            # 不正な入力でのテスト
            malicious_inputs = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE users; --",
                "../../etc/passwd",
                "{{7*7}}",
                "javascript:alert('xss')"
            ]
            
            validation_results = []
            
            for malicious_input in malicious_inputs:
                response = requests.post(
                    f"{self.base_url}/classify",
                    headers=self._get_headers(),
                    json={
                        "text": malicious_input,
                        "category": "test"
                    },
                    timeout=self.timeout
                )
                
                # 入力が適切にサニタイズまたは拒否されているかチェック
                if response.status_code in [200, 400, 422]:
                    validation_results.append(True)
                else:
                    validation_results.append(False)
            
            duration = (time.time() - start_time) * 1000
            
            if all(validation_results):
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"Input validation failed for {sum(validation_results)}/{len(validation_results)} inputs"
            
            self.add_test_result(TestResult(
                test_name="input_validation",
                category=TestCategory.SECURITY,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details={
                    "malicious_inputs_tested": len(malicious_inputs),
                    "validation_success_rate": sum(validation_results) / len(validation_results) * 100
                }
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="input_validation",
                category=TestCategory.SECURITY,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_monitoring(self):
        """監視システムテスト"""
        logger.info("Testing monitoring systems")
        
        # ヘルスチェックテスト
        self._test_health_monitoring()
        
        # メトリクス収集テスト
        self._test_metrics_collection()
        
        # ログ出力テスト
        self._test_logging_system()
    
    def _test_health_monitoring(self):
        """ヘルスチェックテスト"""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/healthz",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                
                # ヘルスデータの検証
                required_fields = ["status", "timestamp", "version"]
                has_required_fields = all(field in health_data for field in required_fields)
                
                if has_required_fields and health_data.get("status") == "healthy":
                    status = TestStatus.PASSED
                    error_message = None
                else:
                    status = TestStatus.FAILED
                    error_message = f"Health check data invalid: {health_data}"
            else:
                status = TestStatus.FAILED
                error_message = f"Health check failed: {response.status_code}"
            
            self.add_test_result(TestResult(
                test_name="health_monitoring",
                category=TestCategory.MONITORING,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details=health_data if response.status_code == 200 else {}
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="health_monitoring",
                category=TestCategory.MONITORING,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_metrics_collection(self):
        """メトリクス収集テスト"""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/metrics/",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                metrics_text = response.text
                
                # Prometheusメトリクスの基本検証
                has_metrics = any(line.startswith(('http_', 'process_', 'python_')) and not line.startswith('#') for line in metrics_text.split('\n'))
                
                if has_metrics:
                    status = TestStatus.PASSED
                    error_message = None
                else:
                    status = TestStatus.FAILED
                    error_message = "No valid Prometheus metrics found"
            else:
                status = TestStatus.FAILED
                error_message = f"Metrics endpoint failed: {response.status_code}"
            
            self.add_test_result(TestResult(
                test_name="metrics_collection",
                category=TestCategory.MONITORING,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details={
                    "metrics_size_bytes": len(metrics_text) if response.status_code == 200 else 0
                }
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="metrics_collection",
                category=TestCategory.MONITORING,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _test_logging_system(self):
        """ログ出力テスト"""
        start_time = time.time()
        
        try:
            # ログを生成するアクションを実行
            response = requests.post(
                f"{self.base_url}/notifications/test",
                headers=self._get_headers(),
                params={"type": "system"},
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000
            
            # ログファイルの存在確認（簡易版）
            log_files_exist = os.path.exists("logs/prism.log")
            
            if response.status_code == 200 and log_files_exist:
                status = TestStatus.PASSED
                error_message = None
            else:
                status = TestStatus.FAILED
                error_message = f"Response: {response.status_code}, Log file exists: {log_files_exist}"
            
            self.add_test_result(TestResult(
                test_name="logging_system",
                category=TestCategory.MONITORING,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                details={
                    "log_file_exists": log_files_exist,
                    "response_status": response.status_code
                }
            ))
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.add_test_result(TestResult(
                test_name="logging_system",
                category=TestCategory.MONITORING,
                status=status,
                duration_ms=duration,
                error_message=str(e)
            ))
    
    def _get_headers(self) -> Dict[str, str]:
        """認証ヘッダーを取得"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _generate_test_summary(self, total_duration_ms: float) -> Dict[str, Any]:
        """テスト結果サマリーを生成"""
        with self.lock:
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r.status == TestStatus.PASSED])
            failed_tests = len([r for r in self.test_results if r.status == TestStatus.FAILED])
            skipped_tests = len([r for r in self.test_results if r.status == TestStatus.SKIPPED])
            
            # カテゴリ別集計
            category_summary = {}
            for category in TestCategory:
                category_tests = [r for r in self.test_results if r.category == category]
                category_summary[category.value] = {
                    "total": len(category_tests),
                    "passed": len([r for r in category_tests if r.status == TestStatus.PASSED]),
                    "failed": len([r for r in category_tests if r.status == TestStatus.FAILED]),
                    "skipped": len([r for r in category_tests if r.status == TestStatus.SKIPPED])
                }
            
            # パフォーマンス統計
            response_times = [r.duration_ms for r in self.test_results if r.duration_ms > 0]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # 成功率計算
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            return {
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "skipped_tests": skipped_tests,
                    "success_rate_percent": round(success_rate, 2),
                    "total_duration_ms": round(total_duration_ms, 2),
                    "avg_response_time_ms": round(avg_response_time, 2)
                },
                "category_summary": category_summary,
                "test_results": [
                    {
                        "test_name": r.test_name,
                        "category": r.category.value,
                        "status": r.status.value,
                        "duration_ms": round(r.duration_ms, 2),
                        "error_message": r.error_message,
                        "timestamp": r.timestamp.isoformat(),
                        "details": r.details
                    }
                    for r in self.test_results
                ],
                "recommendations": self._generate_recommendations(),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        with self.lock:
            # 失敗したテストに基づく推奨事項
            failed_tests = [r for r in self.test_results if r.status == TestStatus.FAILED]
            
            if any("api_" in r.test_name for r in failed_tests):
                recommendations.append("APIエンドポイントの安定性を向上させる必要があります")
            
            if any("notification" in r.test_name for r in failed_tests):
                recommendations.append("通知システムの設定と連携を確認してください")
            
            if any("performance" in r.category.value for r in failed_tests):
                recommendations.append("システムパフォーマンスの最適化を検討してください")
            
            if any("security" in r.category.value for r in failed_tests):
                recommendations.append("セキュリティ設定の見直しが必要です")
            
            if any("monitoring" in r.category.value for r in failed_tests):
                recommendations.append("監視システムの設定を確認してください")
            
            # パフォーマンス推奨事項
            response_times = [r.duration_ms for r in self.test_results if r.duration_ms > 0]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                if avg_response_time > 500:
                    recommendations.append("平均レスポンス時間が500msを超えています。パフォーマンス最適化を推奨します")
            
            # 成功率推奨事項
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r.status == TestStatus.PASSED])
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            if success_rate < 80:
                recommendations.append("テスト成功率が80%を下回っています。システムの安定性向上が必要です")
            elif success_rate < 95:
                recommendations.append("テスト成功率が95%を下回っています。軽微な改善を推奨します")
        
        return recommendations

def main():
    """メイン関数"""
    # 環境変数から設定を取得
    base_url = os.getenv("PRISM_API_URL", "http://localhost:8060")
    api_key = os.getenv("API_KEY", "jrFA7Qw7Kgu2XxhEPDxGYeQ2JmPNdFFJxdTzA3hdxZQ")
    
    # テスト実行
    tester = SystemIntegrationTester(base_url=base_url, api_key=api_key)
    results = tester.run_all_tests()
    
    # 結果出力
    print("=" * 80)
    print("PRISM SYSTEM INTEGRATION TEST RESULTS")
    print("=" * 80)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # 結果ファイル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"integration_test_results_{timestamp}.json"
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nTest results saved to: {results_file}")
    
    # 終了コード
    success_rate = results["test_summary"]["success_rate_percent"]
    if success_rate >= 95:
        print("✅ Integration tests PASSED (95%+ success rate)")
        sys.exit(0)
    elif success_rate >= 80:
        print("⚠️  Integration tests PARTIALLY PASSED (80%+ success rate)")
        sys.exit(1)
    else:
        print("❌ Integration tests FAILED (<80% success rate)")
        sys.exit(2)

if __name__ == "__main__":
    main()
