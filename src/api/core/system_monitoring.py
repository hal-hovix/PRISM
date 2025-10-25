#!/usr/bin/env python3
"""
PRISM System Health Monitoring Module
システムヘルス監視モジュール
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """ヘルスステータス"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentType(Enum):
    """コンポーネントタイプ"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    WORKER = "worker"
    NOTIFIER = "notifier"
    WEB = "web"
    MCP = "mcp"

@dataclass
class HealthCheck:
    """ヘルスチェック結果"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """システムメトリクス"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    uptime: float

class SystemHealthMonitor:
    """システムヘルス監視器"""
    
    def __init__(self):
        self.health_checks: List[HealthCheck] = []
        self.system_metrics: List[SystemMetrics] = []
        self.component_endpoints = {
            ComponentType.API: "http://localhost:8060/healthz",
            ComponentType.WEB: "http://localhost:8061",
            ComponentType.MCP: "http://localhost:8062/health",
            ComponentType.WORKER: None,  # プロセス監視
            ComponentType.NOTIFIER: None,  # プロセス監視
            ComponentType.DATABASE: "redis://localhost:6379",
            ComponentType.CACHE: "redis://localhost:6379"
        }
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "response_time_warning": 1.0,
            "response_time_critical": 5.0
        }
    
    async def check_component_health(self, component: ComponentType) -> HealthCheck:
        """コンポーネントのヘルスチェック"""
        start_time = time.time()
        
        try:
            if component == ComponentType.API:
                return await self._check_api_health()
            elif component == ComponentType.WEB:
                return await self._check_web_health()
            elif component == ComponentType.MCP:
                return await self._check_mcp_health()
            elif component == ComponentType.WORKER:
                return await self._check_worker_health()
            elif component == ComponentType.NOTIFIER:
                return await self._check_notifier_health()
            elif component == ComponentType.DATABASE:
                return await self._check_database_health()
            elif component == ComponentType.CACHE:
                return await self._check_cache_health()
            else:
                return HealthCheck(
                    component=component.value,
                    status=HealthStatus.UNKNOWN,
                    message=f"Unknown component: {component.value}",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
        except Exception as e:
            logger.error(f"Health check failed for {component.value}: {e}")
            return HealthCheck(
                component=component.value,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    async def _check_api_health(self) -> HealthCheck:
        """APIヘルスチェック"""
        import aiohttp
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8060/healthz", timeout=5) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthCheck(
                            component="api",
                            status=HealthStatus.HEALTHY,
                            message="API is healthy",
                            timestamp=datetime.now(),
                            response_time=response_time,
                            details=data
                        )
                    else:
                        return HealthCheck(
                            component="api",
                            status=HealthStatus.CRITICAL,
                            message=f"API returned status {response.status}",
                            timestamp=datetime.now(),
                            response_time=response_time
                        )
        except Exception as e:
            return HealthCheck(
                component="api",
                status=HealthStatus.CRITICAL,
                message=f"API connection failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    async def _check_web_health(self) -> HealthCheck:
        """Web UIヘルスチェック"""
        import aiohttp
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8061", timeout=5) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return HealthCheck(
                            component="web",
                            status=HealthStatus.HEALTHY,
                            message="Web UI is accessible",
                            timestamp=datetime.now(),
                            response_time=response_time
                        )
                    else:
                        return HealthCheck(
                            component="web",
                            status=HealthStatus.WARNING,
                            message=f"Web UI returned status {response.status}",
                            timestamp=datetime.now(),
                            response_time=response_time
                        )
        except Exception as e:
            return HealthCheck(
                component="web",
                status=HealthStatus.CRITICAL,
                message=f"Web UI connection failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    async def _check_mcp_health(self) -> HealthCheck:
        """MCPサーバーヘルスチェック"""
        import aiohttp
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8062/health", timeout=5) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return HealthCheck(
                            component="mcp",
                            status=HealthStatus.HEALTHY,
                            message="MCP server is healthy",
                            timestamp=datetime.now(),
                            response_time=response_time
                        )
                    else:
                        return HealthCheck(
                            component="mcp",
                            status=HealthStatus.WARNING,
                            message=f"MCP server returned status {response.status}",
                            timestamp=datetime.now(),
                            response_time=response_time
                        )
        except Exception as e:
            return HealthCheck(
                component="mcp",
                status=HealthStatus.CRITICAL,
                message=f"MCP server connection failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    async def _check_worker_health(self) -> HealthCheck:
        """Workerプロセスのヘルスチェック"""
        try:
            # Dockerコンテナのプロセスをチェック
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=PRISM-WORKER", "--format", "{{.Status}}"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and "Up" in result.stdout:
                return HealthCheck(
                    component="worker",
                    status=HealthStatus.HEALTHY,
                    message="Worker process is running",
                    timestamp=datetime.now(),
                    details={"status": result.stdout.strip()}
                )
            else:
                return HealthCheck(
                    component="worker",
                    status=HealthStatus.CRITICAL,
                    message="Worker process is not running",
                    timestamp=datetime.now()
                )
        except Exception as e:
            return HealthCheck(
                component="worker",
                status=HealthStatus.CRITICAL,
                message=f"Worker health check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _check_notifier_health(self) -> HealthCheck:
        """Notifierプロセスのヘルスチェック"""
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=PRISM-NOTIFIER", "--format", "{{.Status}}"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and "Up" in result.stdout:
                return HealthCheck(
                    component="notifier",
                    status=HealthStatus.HEALTHY,
                    message="Notifier process is running",
                    timestamp=datetime.now(),
                    details={"status": result.stdout.strip()}
                )
            else:
                return HealthCheck(
                    component="notifier",
                    status=HealthStatus.CRITICAL,
                    message="Notifier process is not running",
                    timestamp=datetime.now()
                )
        except Exception as e:
            return HealthCheck(
                component="notifier",
                status=HealthStatus.CRITICAL,
                message=f"Notifier health check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _check_database_health(self) -> HealthCheck:
        """データベース（Redis）ヘルスチェック"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            start_time = time.time()
            # Pingテスト
            pong = r.ping()
            response_time = time.time() - start_time
            
            if pong:
                # メモリ使用量を取得
                info = r.info('memory')
                memory_used = info.get('used_memory', 0)
                memory_max = info.get('maxmemory', 0)
                
                return HealthCheck(
                    component="database",
                    status=HealthStatus.HEALTHY,
                    message="Database is healthy",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={
                        "memory_used": memory_used,
                        "memory_max": memory_max,
                        "connected_clients": r.info('clients').get('connected_clients', 0)
                    }
                )
            else:
                return HealthCheck(
                    component="database",
                    status=HealthStatus.CRITICAL,
                    message="Database ping failed",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
        except Exception as e:
            return HealthCheck(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _check_cache_health(self) -> HealthCheck:
        """キャッシュ（Redis）ヘルスチェック"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            start_time = time.time()
            # キャッシュテスト
            test_key = "health_check_test"
            r.set(test_key, "test", ex=10)
            value = r.get(test_key)
            r.delete(test_key)
            response_time = time.time() - start_time
            
            if value == "test":
                return HealthCheck(
                    component="cache",
                    status=HealthStatus.HEALTHY,
                    message="Cache is healthy",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    details={
                        "keyspace": r.info('keyspace'),
                        "hit_rate": r.info('stats').get('keyspace_hits', 0) / max(1, r.info('stats').get('keyspace_hits', 0) + r.info('stats').get('keyspace_misses', 0))
                    }
                )
            else:
                return HealthCheck(
                    component="cache",
                    status=HealthStatus.CRITICAL,
                    message="Cache read/write test failed",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
        except Exception as e:
            return HealthCheck(
                component="cache",
                status=HealthStatus.CRITICAL,
                message=f"Cache connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """システムメトリクスを取得"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # ネットワークI/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # プロセス数
            process_count = len(psutil.pids())
            
            # ロードアベレージ（Unix系OS）
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]
            
            # システムアップタイム
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average,
                uptime=uptime
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={},
                process_count=0,
                load_average=[0.0, 0.0, 0.0],
                uptime=0.0
            )
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """包括的なヘルスチェックを実行"""
        logger.info("Running comprehensive health check...")
        
        # 全コンポーネントのヘルスチェック
        health_checks = []
        for component in ComponentType:
            health_check = await self.check_component_health(component)
            health_checks.append(health_check)
        
        # システムメトリクス取得
        system_metrics = self.get_system_metrics()
        
        # ヘルススコア計算
        health_score = self._calculate_health_score(health_checks, system_metrics)
        
        # 結果を保存
        self.health_checks.extend(health_checks)
        self.system_metrics.append(system_metrics)
        
        # 古いデータをクリーンアップ（最新100件を保持）
        if len(self.health_checks) > 100:
            self.health_checks = self.health_checks[-100:]
        if len(self.system_metrics) > 100:
            self.system_metrics = self.system_metrics[-100:]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": health_score,
            "overall_status": self._get_overall_status(health_score),
            "components": [
                {
                    "name": hc.component,
                    "status": hc.status.value,
                    "message": hc.message,
                    "response_time": hc.response_time,
                    "details": hc.details
                }
                for hc in health_checks
            ],
            "system_metrics": {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_percent": system_metrics.disk_percent,
                "process_count": system_metrics.process_count,
                "uptime_hours": system_metrics.uptime / 3600
            },
            "recommendations": self._get_recommendations(health_checks, system_metrics)
        }
    
    def _calculate_health_score(self, health_checks: List[HealthCheck], system_metrics: SystemMetrics) -> int:
        """ヘルススコアを計算（0-100）"""
        score = 100
        
        # コンポーネントステータスによる減点
        for hc in health_checks:
            if hc.status == HealthStatus.CRITICAL:
                score -= 20
            elif hc.status == HealthStatus.WARNING:
                score -= 10
            elif hc.status == HealthStatus.UNKNOWN:
                score -= 5
        
        # システムリソースによる減点
        if system_metrics.cpu_percent > self.thresholds["cpu_critical"]:
            score -= 15
        elif system_metrics.cpu_percent > self.thresholds["cpu_warning"]:
            score -= 10
        
        if system_metrics.memory_percent > self.thresholds["memory_critical"]:
            score -= 15
        elif system_metrics.memory_percent > self.thresholds["memory_warning"]:
            score -= 10
        
        if system_metrics.disk_percent > self.thresholds["disk_critical"]:
            score -= 15
        elif system_metrics.disk_percent > self.thresholds["disk_warning"]:
            score -= 10
        
        # レスポンス時間による減点
        for hc in health_checks:
            if hc.response_time > self.thresholds["response_time_critical"]:
                score -= 5
            elif hc.response_time > self.thresholds["response_time_warning"]:
                score -= 2
        
        return max(0, score)
    
    def _get_overall_status(self, health_score: int) -> str:
        """全体ステータスを取得"""
        if health_score >= 90:
            return "healthy"
        elif health_score >= 70:
            return "warning"
        else:
            return "critical"
    
    def _get_recommendations(self, health_checks: List[HealthCheck], system_metrics: SystemMetrics) -> List[str]:
        """推奨事項を取得"""
        recommendations = []
        
        # コンポーネント関連の推奨事項
        for hc in health_checks:
            if hc.status == HealthStatus.CRITICAL:
                recommendations.append(f"Critical issue with {hc.component}: {hc.message}")
            elif hc.status == HealthStatus.WARNING:
                recommendations.append(f"Warning for {hc.component}: {hc.message}")
        
        # システムリソース関連の推奨事項
        if system_metrics.cpu_percent > self.thresholds["cpu_warning"]:
            recommendations.append(f"High CPU usage: {system_metrics.cpu_percent:.1f}%")
        
        if system_metrics.memory_percent > self.thresholds["memory_warning"]:
            recommendations.append(f"High memory usage: {system_metrics.memory_percent:.1f}%")
        
        if system_metrics.disk_percent > self.thresholds["disk_warning"]:
            recommendations.append(f"High disk usage: {system_metrics.disk_percent:.1f}%")
        
        return recommendations

# グローバルシステムヘルス監視器
system_health_monitor = SystemHealthMonitor()
