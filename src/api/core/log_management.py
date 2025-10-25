#!/usr/bin/env python3
"""
PRISM Log Management Module
ログ管理システム
"""

import os
import json
import logging
import logging.handlers
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import gzip
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """ログカテゴリ"""
    SYSTEM = "system"
    API = "api"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    CACHE = "cache"
    WORKER = "worker"
    NOTIFICATION = "notification"
    CLASSIFICATION = "classification"
    USER_ACTION = "user_action"

@dataclass
class LogEntry:
    """ログエントリ"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

@dataclass
class LogStats:
    """ログ統計"""
    total_entries: int
    entries_by_level: Dict[str, int]
    entries_by_category: Dict[str, int]
    entries_by_component: Dict[str, int]
    error_rate: float
    time_range: Dict[str, datetime]

class LogManager:
    """ログマネージャー"""
    
    def __init__(self, log_dir: str = "/tmp/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # ログファイル設定
        self.log_files = {
            LogCategory.SYSTEM: self.log_dir / "system.log",
            LogCategory.API: self.log_dir / "api.log",
            LogCategory.SECURITY: self.log_dir / "security.log",
            LogCategory.PERFORMANCE: self.log_dir / "performance.log",
            LogCategory.DATABASE: self.log_dir / "database.log",
            LogCategory.CACHE: self.log_dir / "cache.log",
            LogCategory.WORKER: self.log_dir / "worker.log",
            LogCategory.NOTIFICATION: self.log_dir / "notification.log",
            LogCategory.CLASSIFICATION: self.log_dir / "classification.log",
            LogCategory.USER_ACTION: self.log_dir / "user_action.log"
        }
        
        # ログローテーション設定
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
        # ログハンドラーを設定
        self._setup_log_handlers()
        
        # ログエントリの保存
        self.log_entries: List[LogEntry] = []
        self.max_memory_entries = 1000
    
    def _setup_log_handlers(self):
        """ログハンドラーを設定"""
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 各カテゴリのログハンドラーを設定
        for category, log_file in self.log_files.items():
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            handler.setFormatter(formatter)
            
            # カテゴリ別のロガーを作成
            category_logger = logging.getLogger(f"prism.{category.value}")
            category_logger.setLevel(logging.DEBUG)
            category_logger.addHandler(handler)
            category_logger.propagate = False
    
    def log(self, 
            level: LogLevel, 
            category: LogCategory, 
            component: str, 
            message: str,
            details: Dict[str, Any] = None,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            request_id: Optional[str] = None):
        """ログエントリを作成"""
        
        # ログエントリを作成
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            component=component,
            message=message,
            details=details or {},
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        
        # メモリに保存
        self.log_entries.append(log_entry)
        if len(self.log_entries) > self.max_memory_entries:
            self.log_entries = self.log_entries[-self.max_memory_entries:]
        
        # ファイルに書き込み
        self._write_to_file(log_entry)
        
        # 標準ログにも出力
        category_logger = logging.getLogger(f"prism.{category.value}")
        log_message = f"[{component}] {message}"
        if details:
            log_message += f" | Details: {json.dumps(details)}"
        
        if level == LogLevel.DEBUG:
            category_logger.debug(log_message)
        elif level == LogLevel.INFO:
            category_logger.info(log_message)
        elif level == LogLevel.WARNING:
            category_logger.warning(log_message)
        elif level == LogLevel.ERROR:
            category_logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            category_logger.critical(log_message)
    
    def _write_to_file(self, log_entry: LogEntry):
        """ログエントリをファイルに書き込み"""
        try:
            log_file = self.log_files[log_entry.category]
            
            # JSON形式でログを書き込み
            log_data = {
                "timestamp": log_entry.timestamp.isoformat(),
                "level": log_entry.level.value,
                "category": log_entry.category.value,
                "component": log_entry.component,
                "message": log_entry.message,
                "details": log_entry.details,
                "user_id": log_entry.user_id,
                "session_id": log_entry.session_id,
                "request_id": log_entry.request_id
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write log entry to file: {e}")
    
    def get_logs(self, 
                 category: Optional[LogCategory] = None,
                 level: Optional[LogLevel] = None,
                 component: Optional[str] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 limit: int = 100) -> List[LogEntry]:
        """ログエントリを取得"""
        
        filtered_logs = self.log_entries
        
        # フィルタリング
        if category:
            filtered_logs = [log for log in filtered_logs if log.category == category]
        
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        if component:
            filtered_logs = [log for log in filtered_logs if log.component == component]
        
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        
        # 最新順にソート
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 制限
        return filtered_logs[:limit]
    
    def get_log_stats(self, 
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> LogStats:
        """ログ統計を取得"""
        
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()
        
        # 時間範囲内のログを取得
        logs = [log for log in self.log_entries 
                if start_time <= log.timestamp <= end_time]
        
        # 統計を計算
        total_entries = len(logs)
        
        entries_by_level = {}
        entries_by_category = {}
        entries_by_component = {}
        
        error_count = 0
        
        for log in logs:
            # レベル別統計
            level_key = log.level.value
            entries_by_level[level_key] = entries_by_level.get(level_key, 0) + 1
            
            # カテゴリ別統計
            category_key = log.category.value
            entries_by_category[category_key] = entries_by_category.get(category_key, 0) + 1
            
            # コンポーネント別統計
            entries_by_component[log.component] = entries_by_component.get(log.component, 0) + 1
            
            # エラーカウント
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_count += 1
        
        error_rate = (error_count / total_entries * 100) if total_entries > 0 else 0
        
        return LogStats(
            total_entries=total_entries,
            entries_by_level=entries_by_level,
            entries_by_category=entries_by_category,
            entries_by_component=entries_by_component,
            error_rate=error_rate,
            time_range={
                "start": start_time,
                "end": end_time
            }
        )
    
    def search_logs(self, 
                   query: str,
                   category: Optional[LogCategory] = None,
                   level: Optional[LogLevel] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[LogEntry]:
        """ログを検索"""
        
        # 基本フィルタリング
        logs = self.get_logs(category, level, None, start_time, end_time, limit * 2)
        
        # テキスト検索
        query_lower = query.lower()
        filtered_logs = []
        
        for log in logs:
            # メッセージと詳細で検索
            if (query_lower in log.message.lower() or
                any(query_lower in str(value).lower() for value in log.details.values())):
                filtered_logs.append(log)
        
        return filtered_logs[:limit]
    
    def archive_logs(self, days_old: int = 30):
        """古いログをアーカイブ"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for category, log_file in self.log_files.items():
                if log_file.exists():
                    # ログファイルを読み込み
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 新しいログと古いログを分離
                    new_lines = []
                    old_lines = []
                    
                    for line in lines:
                        try:
                            log_data = json.loads(line.strip())
                            log_time = datetime.fromisoformat(log_data['timestamp'])
                            
                            if log_time >= cutoff_date:
                                new_lines.append(line)
                            else:
                                old_lines.append(line)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            # 無効なログ行は新しいログとして保持
                            new_lines.append(line)
                    
                    # 古いログをアーカイブ
                    if old_lines:
                        archive_file = log_file.with_suffix(f'.{cutoff_date.strftime("%Y%m%d")}.gz')
                        with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                            f.writelines(old_lines)
                    
                    # 新しいログでファイルを更新
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    
                    logger.info(f"Archived {len(old_lines)} old log entries for {category.value}")
                    
        except Exception as e:
            logger.error(f"Failed to archive logs: {e}")
    
    def cleanup_archived_logs(self, days_old: int = 90):
        """古いアーカイブログを削除"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for log_file in self.log_dir.glob("*.gz"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"Deleted archived log file: {log_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup archived logs: {e}")
    
    def export_logs(self, 
                   output_file: str,
                   category: Optional[LogCategory] = None,
                   level: Optional[LogLevel] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   format: str = "json") -> bool:
        """ログをエクスポート"""
        try:
            logs = self.get_logs(category, level, None, start_time, end_time, 10000)
            
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump([
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
                    ], f, ensure_ascii=False, indent=2)
            
            elif format == "csv":
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "level", "category", "component", 
                        "message", "details", "user_id", "session_id", "request_id"
                    ])
                    
                    for log in logs:
                        writer.writerow([
                            log.timestamp.isoformat(),
                            log.level.value,
                            log.category.value,
                            log.component,
                            log.message,
                            json.dumps(log.details),
                            log.user_id,
                            log.session_id,
                            log.request_id
                        ])
            
            logger.info(f"Exported {len(logs)} log entries to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return False

# グローバルログマネージャー
log_manager = LogManager()

# 便利な関数
def log_system_event(component: str, message: str, details: Dict[str, Any] = None):
    """システムイベントをログ"""
    log_manager.log(LogLevel.INFO, LogCategory.SYSTEM, component, message, details)

def log_api_request(endpoint: str, method: str, status_code: int, response_time: float, user_id: str = None):
    """APIリクエストをログ"""
    details = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time": response_time
    }
    level = LogLevel.ERROR if status_code >= 400 else LogLevel.INFO
    log_manager.log(level, LogCategory.API, "api", f"{method} {endpoint} - {status_code}", details, user_id)

def log_security_event(event_type: str, client_id: str, details: Dict[str, Any] = None):
    """セキュリティイベントをログ"""
    log_manager.log(LogLevel.WARNING, LogCategory.SECURITY, "security", f"Security event: {event_type}", details)

def log_performance_metric(component: str, metric_name: str, value: float, unit: str = ""):
    """パフォーマンスメトリクスをログ"""
    details = {"metric_name": metric_name, "value": value, "unit": unit}
    log_manager.log(LogLevel.INFO, LogCategory.PERFORMANCE, component, f"Performance metric: {metric_name}", details)

def log_error(component: str, message: str, error: Exception, details: Dict[str, Any] = None):
    """エラーをログ"""
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        **(details or {})
    }
    log_manager.log(LogLevel.ERROR, LogCategory.SYSTEM, component, message, error_details)
