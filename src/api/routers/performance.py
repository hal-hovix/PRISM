#!/usr/bin/env python3
"""
PRISM Performance API
パフォーマンス監視・最適化API
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# FastAPI関連のインポート
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.core.security import verify_api_key
from src.api.core.logging import get_logger
from src.api.core.performance import (
    performance_monitor, 
    MemoryOptimizer, 
    cache_manager,
    performance_timer
)

logger = get_logger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])

# Pydanticモデル
class PerformanceReport(BaseModel):
    """パフォーマンスレポート"""
    timestamp: datetime
    system_metrics: Dict[str, float]
    endpoint_metrics: Dict[str, Dict[str, Any]]
    recommendations: List[str]

class OptimizationRequest(BaseModel):
    """最適化リクエスト"""
    optimization_type: str = Field(..., description="最適化タイプ: memory, cache, gc")
    force: bool = Field(default=False, description="強制実行")

class CacheOperation(BaseModel):
    """キャッシュ操作"""
    operation: str = Field(..., description="操作: get, set, delete, clear")
    key: Optional[str] = None
    value: Optional[Any] = None
    ttl: Optional[int] = None

# パフォーマンス監視エンドポイント
@router.get("/metrics", response_model=Dict[str, Any])
@performance_timer("performance.metrics")
async def get_performance_metrics(
    api_key: str = Depends(verify_api_key)
):
    """パフォーマンスメトリクスを取得"""
    try:
        metrics = performance_monitor.get_all_metrics()
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.get("/report", response_model=PerformanceReport)
@performance_timer("performance.report")
async def get_performance_report(
    api_key: str = Depends(verify_api_key)
):
    """パフォーマンスレポートを生成"""
    try:
        system_metrics = performance_monitor.get_system_metrics()
        endpoint_metrics = {
            k: {
                "request_count": v.request_count,
                "avg_response_time": v.avg_response_time,
                "min_response_time": v.min_response_time,
                "max_response_time": v.max_response_time,
                "last_updated": v.last_updated.isoformat() if v.last_updated else None
            } for k, v in performance_monitor.metrics.items()
        }
        
        recommendations = MemoryOptimizer.get_memory_recommendations()
        
        return PerformanceReport(
            timestamp=datetime.now(),
            system_metrics=system_metrics,
            endpoint_metrics=endpoint_metrics,
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}"
        )

@router.post("/optimize")
@performance_timer("performance.optimize")
async def optimize_performance(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """パフォーマンス最適化を実行"""
    try:
        results = {}
        
        if request.optimization_type in ["memory", "gc"]:
            results["memory"] = MemoryOptimizer.optimize_memory()
        
        if request.optimization_type in ["cache", "gc"]:
            cache_manager.cleanup_expired()
            results["cache"] = {
                "cleaned": True,
                "cache_size": len(cache_manager.cache)
            }
        
        return {
            "status": "success",
            "optimization_type": request.optimization_type,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error optimizing performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize performance: {str(e)}"
        )

@router.post("/cache")
@performance_timer("performance.cache")
async def cache_operation(
    request: CacheOperation,
    api_key: str = Depends(verify_api_key)
):
    """キャッシュ操作を実行"""
    try:
        if request.operation == "get":
            if not request.key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Key is required for get operation"
                )
            value = cache_manager.get(request.key)
            return {
                "status": "success",
                "operation": "get",
                "key": request.key,
                "value": value,
                "found": value is not None
            }
        
        elif request.operation == "set":
            if not request.key or request.value is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Key and value are required for set operation"
                )
            cache_manager.set(request.key, request.value, request.ttl)
            return {
                "status": "success",
                "operation": "set",
                "key": request.key,
                "ttl": request.ttl
            }
        
        elif request.operation == "delete":
            if not request.key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Key is required for delete operation"
                )
            cache_manager.delete(request.key)
            return {
                "status": "success",
                "operation": "delete",
                "key": request.key
            }
        
        elif request.operation == "clear":
            cache_manager.clear()
            return {
                "status": "success",
                "operation": "clear"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {request.operation}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cache operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache operation failed: {str(e)}"
        )

@router.get("/health")
@performance_timer("performance.health")
async def performance_health_check(
    api_key: str = Depends(verify_api_key)
):
    """パフォーマンスヘルスチェック"""
    try:
        system_metrics = performance_monitor.get_system_metrics()
        recommendations = MemoryOptimizer.get_memory_recommendations()
        
        # ヘルススコアを計算
        health_score = 100
        
        # メモリ使用量による減点
        memory_percent = system_metrics.get("memory_percent", 0)
        if memory_percent > 90:
            health_score -= 30
        elif memory_percent > 80:
            health_score -= 20
        elif memory_percent > 70:
            health_score -= 10
        
        # CPU使用量による減点
        cpu_percent = system_metrics.get("cpu_percent", 0)
        if cpu_percent > 90:
            health_score -= 20
        elif cpu_percent > 80:
            health_score -= 10
        
        # 推奨事項による減点
        health_score -= len(recommendations) * 5
        
        health_score = max(0, health_score)
        
        status_level = "healthy"
        if health_score < 70:
            status_level = "warning"
        if health_score < 50:
            status_level = "critical"
        
        return {
            "status": status_level,
            "health_score": health_score,
            "system_metrics": system_metrics,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in performance health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance health check failed: {str(e)}"
        )

@router.get("/stats")
@performance_timer("performance.stats")
async def get_performance_stats(
    api_key: str = Depends(verify_api_key)
):
    """パフォーマンス統計を取得"""
    try:
        stats = {
            "uptime_seconds": performance_monitor.get_system_metrics().get("uptime_seconds", 0),
            "total_requests": sum(m.request_count for m in performance_monitor.metrics.values()),
            "endpoints_tracked": len(performance_monitor.metrics),
            "cache_size": len(cache_manager.cache),
            "memory_usage_mb": performance_monitor.get_system_metrics().get("memory_usage_mb", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance stats: {str(e)}"
        )
