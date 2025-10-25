#!/usr/bin/env python3
"""
PRISM Monitoring and Logging API
監視・ログAPI
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# FastAPI関連のインポート
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.core.security import verify_api_key
from src.api.core.logging import get_logger
from src.api.core.system_monitoring import (
    system_health_monitor, 
    ComponentType, 
    HealthStatus
)
from src.api.core.log_management import (
    log_manager, 
    LogLevel, 
    LogCategory,
    LogStats
)

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Pydanticモデル
class HealthCheckRequest(BaseModel):
    """ヘルスチェックリクエスト"""
    components: Optional[List[str]] = Field(default=None, description="チェックするコンポーネント")
    include_metrics: bool = Field(default=True, description="システムメトリクスを含める")

class LogSearchRequest(BaseModel):
    """ログ検索リクエスト"""
    query: Optional[str] = Field(default=None, description="検索クエリ")
    category: Optional[str] = Field(default=None, description="ログカテゴリ")
    level: Optional[str] = Field(default=None, description="ログレベル")
    component: Optional[str] = Field(default=None, description="コンポーネント")
    start_time: Optional[datetime] = Field(default=None, description="開始時刻")
    end_time: Optional[datetime] = Field(default=None, description="終了時刻")
    limit: int = Field(default=100, ge=1, le=1000, description="取得件数")

class LogExportRequest(BaseModel):
    """ログエクスポートリクエスト"""
    category: Optional[str] = Field(default=None, description="ログカテゴリ")
    level: Optional[str] = Field(default=None, description="ログレベル")
    start_time: Optional[datetime] = Field(default=None, description="開始時刻")
    end_time: Optional[datetime] = Field(default=None, description="終了時刻")
    format: str = Field(default="json", description="エクスポート形式: json, csv")

# システム監視エンドポイント
@router.get("/health")
async def get_system_health(
    api_key: str = Depends(verify_api_key)
):
    """システムヘルスチェックを実行"""
    try:
        health_data = await system_health_monitor.run_comprehensive_health_check()
        return {
            "status": "success",
            "data": health_data
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )

@router.post("/health/check")
async def run_health_check(
    request: HealthCheckRequest,
    api_key: str = Depends(verify_api_key)
):
    """指定されたコンポーネントのヘルスチェックを実行"""
    try:
        components_to_check = request.components or [comp.value for comp in ComponentType]
        
        health_checks = []
        for comp_name in components_to_check:
            try:
                component = ComponentType(comp_name)
                health_check = await system_health_monitor.check_component_health(component)
                health_checks.append({
                    "component": health_check.component,
                    "status": health_check.status.value,
                    "message": health_check.message,
                    "response_time": health_check.response_time,
                    "details": health_check.details
                })
            except ValueError:
                health_checks.append({
                    "component": comp_name,
                    "status": "unknown",
                    "message": f"Unknown component: {comp_name}",
                    "response_time": 0.0,
                    "details": {}
                })
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "components": health_checks,
            "overall_status": "healthy" if all(hc["status"] == "healthy" for hc in health_checks) else "warning"
        }
        
        if request.include_metrics:
            system_metrics = system_health_monitor.get_system_metrics()
            result["system_metrics"] = {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "disk_percent": system_metrics.disk_percent,
                "process_count": system_metrics.process_count,
                "uptime_hours": system_metrics.uptime / 3600
            }
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error running health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run health check: {str(e)}"
        )

@router.get("/metrics")
async def get_system_metrics(
    api_key: str = Depends(verify_api_key)
):
    """システムメトリクスを取得"""
    try:
        metrics = system_health_monitor.get_system_metrics()
        
        return {
            "status": "success",
            "data": {
                "timestamp": metrics.timestamp.isoformat(),
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_percent": metrics.disk_percent,
                "network_io": metrics.network_io,
                "process_count": metrics.process_count,
                "load_average": metrics.load_average,
                "uptime_hours": metrics.uptime / 3600
            }
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )

# ログ管理エンドポイント
@router.get("/logs")
async def get_logs(
    category: Optional[str] = Query(default=None),
    level: Optional[str] = Query(default=None),
    component: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    api_key: str = Depends(verify_api_key)
):
    """ログエントリを取得"""
    try:
        # パラメータを変換
        log_category = LogCategory(category) if category else None
        log_level = LogLevel(level) if level else None
        
        logs = log_manager.get_logs(
            category=log_category,
            level=log_level,
            component=component,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "status": "success",
            "data": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level.value,
                    "category": log.category.value,
                    "component": log.component,
                    "message": log.message,
                    "details": log.details,
                    "user_id": log.user_id,
                    "session_id": log.session_id,
                    "request_id": log.request_id
                }
                for log in logs
            ],
            "total": len(logs)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )

@router.post("/logs/search")
async def search_logs(
    request: LogSearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """ログを検索"""
    try:
        # パラメータを変換
        log_category = LogCategory(request.category) if request.category else None
        log_level = LogLevel(request.level) if request.level else None
        
        logs = log_manager.search_logs(
            query=request.query or "",
            category=log_category,
            level=log_level,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit
        )
        
        return {
            "status": "success",
            "data": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level.value,
                    "category": log.category.value,
                    "component": log.component,
                    "message": log.message,
                    "details": log.details,
                    "user_id": log.user_id,
                    "session_id": log.session_id,
                    "request_id": log.request_id
                }
                for log in logs
            ],
            "total": len(logs),
            "query": request.query
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )

@router.get("/logs/stats")
async def get_log_stats(
    hours: int = Query(default=24, ge=1, le=168),
    api_key: str = Depends(verify_api_key)
):
    """ログ統計を取得"""
    try:
        start_time = datetime.now() - timedelta(hours=hours)
        end_time = datetime.now()
        
        stats = log_manager.get_log_stats(start_time, end_time)
        
        return {
            "status": "success",
            "data": {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": hours
                },
                "total_entries": stats.total_entries,
                "entries_by_level": stats.entries_by_level,
                "entries_by_category": stats.entries_by_category,
                "entries_by_component": stats.entries_by_component,
                "error_rate": stats.error_rate
            }
        }
    except Exception as e:
        logger.error(f"Error getting log stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log stats: {str(e)}"
        )

@router.post("/logs/export")
async def export_logs(
    request: LogExportRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """ログをエクスポート"""
    try:
        # パラメータを変換
        log_category = LogCategory(request.category) if request.category else None
        log_level = LogLevel(request.level) if request.level else None
        
        # エクスポートファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs_export_{timestamp}.{request.format}"
        output_path = f"/tmp/{filename}"
        
        # エクスポートを実行
        success = log_manager.export_logs(
            output_file=output_path,
            category=log_category,
            level=log_level,
            start_time=request.start_time,
            end_time=request.end_time,
            format=request.format
        )
        
        if success:
            # バックグラウンドでファイルをクリーンアップ
            background_tasks.add_task(lambda: os.remove(output_path) if os.path.exists(output_path) else None)
            
            return FileResponse(
                path=output_path,
                filename=filename,
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export logs"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error exporting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export logs: {str(e)}"
        )

@router.post("/logs/archive")
async def archive_logs(
    days_old: int = Query(default=30, ge=1, le=365),
    api_key: str = Depends(verify_api_key)
):
    """古いログをアーカイブ"""
    try:
        log_manager.archive_logs(days_old)
        return {
            "status": "success",
            "message": f"Archived logs older than {days_old} days",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error archiving logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive logs: {str(e)}"
        )

@router.post("/logs/cleanup")
async def cleanup_logs(
    days_old: int = Query(default=90, ge=1, le=365),
    api_key: str = Depends(verify_api_key)
):
    """古いアーカイブログを削除"""
    try:
        log_manager.cleanup_archived_logs(days_old)
        return {
            "status": "success",
            "message": f"Cleaned up archived logs older than {days_old} days",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup logs: {str(e)}"
        )

@router.get("/dashboard")
async def get_monitoring_dashboard(
    api_key: str = Depends(verify_api_key)
):
    """監視ダッシュボードデータを取得"""
    try:
        # システムヘルス
        health_data = await system_health_monitor.run_comprehensive_health_check()
        
        # システムメトリクス
        metrics = system_health_monitor.get_system_metrics()
        
        # ログ統計（過去24時間）
        start_time = datetime.now() - timedelta(hours=24)
        log_stats = log_manager.get_log_stats(start_time)
        
        # 最近のエラーログ
        error_logs = log_manager.get_logs(
            level=LogLevel.ERROR,
            start_time=start_time,
            limit=10
        )
        
        return {
            "status": "success",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "health": {
                    "overall_status": health_data["overall_status"],
                    "health_score": health_data["health_score"],
                    "components": health_data["components"]
                },
                "metrics": {
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "disk_percent": metrics.disk_percent,
                    "process_count": metrics.process_count,
                    "uptime_hours": metrics.uptime / 3600
                },
                "logs": {
                    "total_entries_24h": log_stats.total_entries,
                    "error_rate": log_stats.error_rate,
                    "entries_by_level": log_stats.entries_by_level,
                    "entries_by_category": log_stats.entries_by_category,
                    "recent_errors": [
                        {
                            "timestamp": log.timestamp.isoformat(),
                            "component": log.component,
                            "message": log.message,
                            "details": log.details
                        }
                        for log in error_logs
                    ]
                },
                "recommendations": health_data["recommendations"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring dashboard: {str(e)}"
        )
