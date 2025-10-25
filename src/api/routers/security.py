#!/usr/bin/env python3
"""
PRISM Security API
セキュリティ監視・管理API
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# FastAPI関連のインポート
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.core.security import verify_api_key
from src.api.core.logging import get_logger
from src.api.core.rate_limiting import rate_limiter, get_client_id
from src.api.core.input_validation import input_validator, validate_and_sanitize
from src.api.core.security_monitoring import (
    security_monitor, 
    SecurityEventType, 
    SecurityLevel,
    log_security_event
)

logger = get_logger(__name__)
router = APIRouter(prefix="/security", tags=["security"])

# Pydanticモデル
class SecuritySummary(BaseModel):
    """セキュリティサマリー"""
    timestamp: datetime
    summary: Dict[str, Any]
    event_breakdown: Dict[str, int]
    level_breakdown: Dict[str, int]
    top_risky_clients: List[List[Any]]
    recent_alerts: List[Dict[str, Any]]

class RateLimitConfig(BaseModel):
    """レート制限設定"""
    requests_per_minute: int = Field(default=60, ge=1, le=1000)
    burst_limit: int = Field(default=10, ge=1, le=100)
    window_size: int = Field(default=60, ge=10, le=3600)

class ClientAction(BaseModel):
    """クライアントアクション"""
    client_id: str
    action: str = Field(..., description="Action: block, unblock, reset, whitelist, blacklist")
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=1440)

class IPAction(BaseModel):
    """IPアクション"""
    ip_address: str
    action: str = Field(..., description="Action: blacklist, whitelist, remove")

class ValidationRequest(BaseModel):
    """検証リクエスト"""
    data: Dict[str, Any]
    schema: Dict[str, str]

# セキュリティ監視エンドポイント
@router.get("/summary", response_model=SecuritySummary)
async def get_security_summary(
    api_key: str = Depends(verify_api_key)
):
    """セキュリティサマリーを取得"""
    try:
        summary_data = security_monitor.get_security_summary()
        
        return SecuritySummary(
            timestamp=datetime.now(),
            **summary_data
        )
    except Exception as e:
        logger.error(f"Error getting security summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security summary: {str(e)}"
        )

@router.get("/events")
async def get_security_events(
    limit: int = Query(default=100, ge=1, le=1000),
    event_type: Optional[str] = Query(default=None),
    level: Optional[str] = Query(default=None),
    client_id: Optional[str] = Query(default=None),
    api_key: str = Depends(verify_api_key)
):
    """セキュリティイベントを取得"""
    try:
        events = list(security_monitor.events)
        
        # フィルタリング
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        if level:
            events = [e for e in events if e.level.value == level]
        if client_id:
            events = [e for e in events if e.client_id == client_id]
        
        # 最新順にソート
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 制限
        events = events[:limit]
        
        return {
            "status": "success",
            "events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type.value,
                    "level": e.level.value,
                    "client_id": e.client_id,
                    "ip_address": e.ip_address,
                    "endpoint": e.endpoint,
                    "method": e.method,
                    "risk_score": e.risk_score,
                    "details": e.details
                }
                for e in events
            ],
            "total": len(events)
        }
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security events: {str(e)}"
        )

@router.get("/alerts")
async def get_security_alerts(
    resolved: Optional[bool] = Query(default=None),
    level: Optional[str] = Query(default=None),
    api_key: str = Depends(verify_api_key)
):
    """セキュリティアラートを取得"""
    try:
        alerts = security_monitor.alerts
        
        # フィルタリング
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        if level:
            alerts = [a for a in alerts if a.level.value == level]
        
        # 最新順にソート
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return {
            "status": "success",
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "event_type": a.event_type.value,
                    "level": a.level.value,
                    "client_id": a.client_id,
                    "ip_address": a.ip_address,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat(),
                    "resolved": a.resolved,
                    "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                    "details": a.details
                }
                for a in alerts
            ],
            "total": len(alerts)
        }
    except Exception as e:
        logger.error(f"Error getting security alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security alerts: {str(e)}"
        )

@router.post("/alerts/{alert_id}/resolve")
async def resolve_security_alert(
    alert_id: str,
    api_key: str = Depends(verify_api_key)
):
    """セキュリティアラートを解決"""
    try:
        security_monitor.resolve_alert(alert_id)
        return {
            "status": "success",
            "message": f"Alert {alert_id} resolved",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resolving security alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}"
        )

# レート制限管理エンドポイント
@router.get("/rate-limits")
async def get_rate_limit_stats(
    client_id: Optional[str] = Query(default=None),
    api_key: str = Depends(verify_api_key)
):
    """レート制限統計を取得"""
    try:
        if client_id:
            stats = rate_limiter.get_client_stats(client_id)
            return {
                "status": "success",
                "client_stats": stats
            }
        else:
            stats = rate_limiter.get_global_stats()
            return {
                "status": "success",
                "global_stats": stats
            }
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit stats: {str(e)}"
        )

@router.post("/rate-limits/reset")
async def reset_rate_limit(
    client_id: str,
    api_key: str = Depends(verify_api_key)
):
    """クライアントのレート制限をリセット"""
    try:
        rate_limiter.reset_client(client_id)
        return {
            "status": "success",
            "message": f"Rate limit reset for client {client_id}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limit: {str(e)}"
        )

# クライアント管理エンドポイント
@router.post("/clients/action")
async def client_action(
    request: ClientAction,
    api_key: str = Depends(verify_api_key)
):
    """クライアントアクションを実行"""
    try:
        client_id = request.client_id
        action = request.action
        
        if action == "block":
            duration = request.duration_minutes or 15
            security_monitor._block_client(client_id, duration)
            message = f"Client {client_id} blocked for {duration} minutes"
        elif action == "unblock":
            if client_id in security_monitor.client_stats:
                security_monitor.client_stats[client_id]["blocked"] = False
                security_monitor.client_stats[client_id]["blocked_until"] = None
            message = f"Client {client_id} unblocked"
        elif action == "reset":
            if client_id in security_monitor.client_stats:
                security_monitor.client_stats[client_id]["risk_score"] = 0
                security_monitor.client_stats[client_id]["suspicious_requests"] = 0
            message = f"Client {client_id} risk score reset"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )
        
        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing client action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute client action: {str(e)}"
        )

# IP管理エンドポイント
@router.post("/ips/action")
async def ip_action(
    request: IPAction,
    api_key: str = Depends(verify_api_key)
):
    """IPアクションを実行"""
    try:
        ip_address = request.ip_address
        action = request.action
        
        if action == "blacklist":
            security_monitor.add_to_blacklist(ip_address)
            message = f"IP {ip_address} added to blacklist"
        elif action == "whitelist":
            security_monitor.add_to_whitelist(ip_address)
            message = f"IP {ip_address} added to whitelist"
        elif action == "remove":
            security_monitor.ip_blacklist.discard(ip_address)
            security_monitor.ip_whitelist.discard(ip_address)
            message = f"IP {ip_address} removed from blacklist/whitelist"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )
        
        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing IP action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute IP action: {str(e)}"
        )

# 入力検証エンドポイント
@router.post("/validate")
async def validate_input(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    """入力を検証・サニタイズ"""
    try:
        result = validate_and_sanitize(request.data, request.schema)
        
        return {
            "status": "success",
            "validation_result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error validating input: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate input: {str(e)}"
        )

@router.get("/health")
async def security_health_check(
    api_key: str = Depends(verify_api_key)
):
    """セキュリティヘルスチェック"""
    try:
        summary = security_monitor.get_security_summary()
        
        # ヘルススコアを計算
        health_score = 100
        
        # アクティブなアラートによる減点
        active_alerts = summary["summary"]["active_alerts"]
        health_score -= active_alerts * 10
        
        # ブロックされたクライアントによる減点
        blocked_clients = summary["summary"]["blocked_clients"]
        health_score -= blocked_clients * 5
        
        # 重大なイベントによる減点
        critical_events = summary["level_breakdown"].get("critical", 0)
        health_score -= critical_events * 20
        
        health_score = max(0, health_score)
        
        status_level = "healthy"
        if health_score < 70:
            status_level = "warning"
        if health_score < 50:
            status_level = "critical"
        
        return {
            "status": status_level,
            "health_score": health_score,
            "summary": summary["summary"],
            "recommendations": [
                "Monitor active alerts regularly",
                "Review blocked clients periodically",
                "Update security rules as needed"
            ] if active_alerts > 0 else [],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in security health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security health check failed: {str(e)}"
        )
