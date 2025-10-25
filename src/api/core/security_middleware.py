#!/usr/bin/env python3
"""
PRISM Security Middleware
セキュリティミドルウェア
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.core.rate_limiting import rate_limiter, get_client_id
from src.api.core.input_validation import input_validator
from src.api.core.security_monitoring import (
    security_monitor,
    SecurityEventType,
    SecurityLevel,
    log_security_event
)

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """セキュリティミドルウェア"""
    
    def __init__(self, app, enable_rate_limiting: bool = True, enable_monitoring: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_monitoring = enable_monitoring
        
        # 除外するエンドポイント
        self.excluded_endpoints = {
            "/healthz",
            "/docs",
            "/openapi.json",
            "/metrics/"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理"""
        start_time = time.time()
        
        # クライアント情報を取得
        client_id = get_client_id(request)
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        endpoint = str(request.url.path)
        method = request.method
        
        # 除外エンドポイントのチェック
        if endpoint in self.excluded_endpoints:
            return await call_next(request)
        
        try:
            # IPアドレスチェック
            if security_monitor.is_ip_blocked(ip_address):
                await self._log_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    SecurityLevel.HIGH,
                    client_id, ip_address, user_agent, endpoint, method,
                    {"reason": "IP address blocked"}
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Access denied", "reason": "IP address blocked"}
                )
            
            # ホワイトリストチェック（ホワイトリストに登録されている場合はスキップ）
            if security_monitor.is_ip_whitelisted(ip_address):
                return await call_next(request)
            
            # クライアントブロックチェック
            if security_monitor.is_client_blocked(client_id):
                await self._log_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    SecurityLevel.MEDIUM,
                    client_id, ip_address, user_agent, endpoint, method,
                    {"reason": "Client blocked"}
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Access denied", "reason": "Client blocked"}
                )
            
            # レート制限チェック
            if self.enable_rate_limiting:
                allowed, rate_limit_info = rate_limiter.check_rate_limit(client_id, endpoint)
                if not allowed:
                    await self._log_security_event(
                        SecurityEventType.RATE_LIMIT_EXCEEDED,
                        SecurityLevel.MEDIUM,
                        client_id, ip_address, user_agent, endpoint, method,
                        rate_limit_info
                    )
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "details": rate_limit_info
                        }
                    )
            
            # リクエストボディの検証（POST/PUT/PATCHリクエスト）
            if method in ["POST", "PUT", "PATCH"] and request.headers.get("content-type", "").startswith("application/json"):
                try:
                    # リクエストボディを読み取り
                    body = await request.body()
                    if body:
                        # 基本的な入力検証
                        body_str = body.decode("utf-8")
                        
                        # SQLインジェクション検出
                        if input_validator.detect_sql_injection(body_str):
                            await self._log_security_event(
                                SecurityEventType.SQL_INJECTION_ATTEMPT,
                                SecurityLevel.CRITICAL,
                                client_id, ip_address, user_agent, endpoint, method,
                                {"payload": body_str[:200]}  # 最初の200文字のみ
                            )
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "Invalid request data"}
                            )
                        
                        # XSS検出
                        if input_validator.detect_xss(body_str):
                            await self._log_security_event(
                                SecurityEventType.XSS_ATTEMPT,
                                SecurityLevel.CRITICAL,
                                client_id, ip_address, user_agent, endpoint, method,
                                {"payload": body_str[:200]}  # 最初の200文字のみ
                            )
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"error": "Invalid request data"}
                            )
                
                except Exception as e:
                    logger.warning(f"Error validating request body: {e}")
            
            # 疑わしいリクエストパターンの検出
            if self._is_suspicious_request(request):
                await self._log_security_event(
                    SecurityEventType.SUSPICIOUS_REQUEST,
                    SecurityLevel.MEDIUM,
                    client_id, ip_address, user_agent, endpoint, method,
                    {"reason": "Suspicious request pattern"}
                )
            
            # リクエストを処理
            response = await call_next(request)
            
            # レスポンス時間を記録
            process_time = time.time() - start_time
            
            # セキュリティ監視
            if self.enable_monitoring:
                await self._log_request_success(client_id, ip_address, user_agent, endpoint, method, process_time)
            
            return response
            
        except HTTPException as e:
            # HTTP例外の場合はセキュリティログを記録
            if e.status_code in [401, 403, 429]:
                await self._log_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    SecurityLevel.MEDIUM,
                    client_id, ip_address, user_agent, endpoint, method,
                    {"status_code": e.status_code, "detail": str(e.detail)}
                )
            
            raise e
        
        except Exception as e:
            # 予期しないエラーの場合はセキュリティログを記録
            await self._log_security_event(
                SecurityEventType.SUSPICIOUS_REQUEST,
                SecurityLevel.HIGH,
                client_id, ip_address, user_agent, endpoint, method,
                {"error": str(e)}
            )
            
            logger.error(f"Unexpected error in security middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """疑わしいリクエストパターンを検出"""
        # 異常に長いURL
        if len(str(request.url)) > 2000:
            return True
        
        # 異常に多いヘッダー
        if len(request.headers) > 50:
            return True
        
        # 疑わしいヘッダー
        suspicious_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-originating-ip",
            "x-remote-ip",
            "x-remote-addr"
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                # 複数のIPアドレスが含まれている場合
                if "," in value and len(value.split(",")) > 3:
                    return True
        
        # 異常なUser-Agent
        user_agent = request.headers.get("User-Agent", "")
        if len(user_agent) > 500:
            return True
        
        # スクリプト実行を試みる疑わしいパターン
        suspicious_patterns = [
            "script",
            "javascript",
            "vbscript",
            "onload",
            "onerror",
            "eval(",
            "exec(",
            "system(",
            "cmd",
            "powershell"
        ]
        
        url_str = str(request.url).lower()
        for pattern in suspicious_patterns:
            if pattern in url_str:
                return True
        
        return False
    
    async def _log_security_event(
        self,
        event_type: SecurityEventType,
        level: SecurityLevel,
        client_id: str,
        ip_address: str,
        user_agent: str,
        endpoint: str,
        method: str,
        details: dict
    ):
        """セキュリティイベントをログ"""
        try:
            log_security_event(
                event_type=event_type,
                level=level,
                client_id=client_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                details=details
            )
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    async def _log_request_success(
        self,
        client_id: str,
        ip_address: str,
        user_agent: str,
        endpoint: str,
        method: str,
        process_time: float
    ):
        """成功したリクエストをログ"""
        try:
            # 正常なリクエストとして記録（レベルは低く設定）
            log_security_event(
                event_type=SecurityEventType.LOGIN_SUCCESS,  # 成功イベントとして記録
                level=SecurityLevel.LOW,
                client_id=client_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                details={"process_time": process_time}
            )
        except Exception as e:
            logger.error(f"Error logging successful request: {e}")
