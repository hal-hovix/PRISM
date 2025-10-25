"""
PRISM API用メトリクス収集機能
"""
import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, Depends
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from ..core.logging import get_logger
from ..core.security import verify_api_key

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Prometheusメトリクスの定義
REQUEST_COUNT = Counter('prism_requests_total', 'Total number of requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('prism_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('prism_active_connections', 'Number of active connections')
MEMORY_USAGE = Gauge('prism_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('prism_cpu_usage_percent', 'CPU usage percentage')
DISK_USAGE = Gauge('prism_disk_usage_bytes', 'Disk usage in bytes')

class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def collect_system_metrics(self):
        """システムメトリクスを収集"""
        try:
            # メモリ使用量
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # ディスク使用量
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.used)
            
            logger.debug(f"System metrics collected - Memory: {memory.used}, CPU: {cpu_percent}%, Disk: {disk.used}")
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """リクエストメトリクスを記録"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    def update_active_connections(self, count: int):
        """アクティブ接続数を更新"""
        ACTIVE_CONNECTIONS.set(count)

# グローバルメトリクス収集器
metrics_collector = MetricsCollector()

@router.get("/")
def get_metrics():
    """Prometheusメトリクスを取得"""
    try:
        # システムメトリクスを収集
        metrics_collector.collect_system_metrics()
        
        # メトリクスを生成
        metrics_data = generate_latest()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(
            content="Error generating metrics",
            status_code=500
        )

@router.get("/health")
def metrics_health():
    """メトリクスエンドポイントのヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - metrics_collector.start_time
    }

@router.get("/stats")
def get_stats(_=Depends(verify_api_key)):
    """詳細な統計情報を取得（認証必須）"""
    try:
        # システム情報
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # プロセス情報
        process = psutil.Process()
        
        stats = {
            "system": {
                "memory": {
                    "total": memory.total,
                    "used": memory.used,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                }
            },
            "process": {
                "pid": process.pid,
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": process.create_time()
            },
            "uptime": time.time() - metrics_collector.start_time
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": "Failed to get stats", "message": str(e)}
