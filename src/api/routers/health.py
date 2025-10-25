
import time
import psutil
from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..core.logging import get_logger
from ..core.security import verify_api_key
from ..core.performance import performance_timer

logger = get_logger(__name__)

router = APIRouter()

@router.get("/healthz")
@performance_timer("health.healthz")
def health_check():
    """基本的なヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "prism-api",
        "version": "1.0.0"
    }

@router.get("/healthz/detailed")
@performance_timer("health.detailed")
def detailed_health_check(_=Depends(verify_api_key)):
    """詳細なヘルスチェック（認証必須）"""
    try:
        # システムリソースの確認
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # ヘルスステータスの判定
        health_status = "healthy"
        issues = []
        
        # メモリ使用率が90%以上の場合
        if memory.percent > 90:
            health_status = "warning"
            issues.append(f"High memory usage: {memory.percent}%")
        
        # ディスク使用率が90%以上の場合
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > 90:
            health_status = "warning"
            issues.append(f"High disk usage: {disk_percent:.1f}%")
        
        # CPU使用率が95%以上の場合
        if cpu_percent > 95:
            health_status = "critical"
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        return {
            "status": health_status,
            "timestamp": time.time(),
            "service": "prism-api",
            "version": "1.0.0",
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
                    "percent": disk_percent
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                }
            },
            "issues": issues
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "service": "prism-api",
            "version": "1.0.0",
            "error": str(e)
        }

@router.get("/healthz/ready")
def readiness_check():
    """Readinessチェック（Kubernetes用）"""
    try:
        # 必要なサービスが利用可能かチェック
        # ここでは基本的なチェックのみ実装
        
        return {
            "status": "ready",
            "timestamp": time.time(),
            "service": "prism-api"
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "timestamp": time.time(),
            "service": "prism-api",
            "error": str(e)
        }

@router.get("/healthz/live")
def liveness_check():
    """Livenessチェック（Kubernetes用）"""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "service": "prism-api"
    }

