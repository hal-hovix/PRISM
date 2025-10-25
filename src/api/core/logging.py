
import json
import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict


class SecureJsonFormatter(logging.Formatter):
    """機密情報をマスキングするJSONログフォーマッター"""
    
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        log: Dict[str, Any] = {
            "timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)
        
        # 機密情報をマスキング
        message = log["message"]
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), "***MASKED***"), message)
        log["message"] = message
        
        return json.dumps(log, ensure_ascii=False)


class SecureHumanFormatter(logging.Formatter):
    """機密情報をマスキングする人間可読ログフォーマッター"""
    
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        
        # 機密情報をマスキング
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), "***MASKED***"), message)
        
        return message


def configure_logging() -> None:
    """セキュアなログ設定を構成"""
    
    # ログディレクトリの作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # ログ設定の取得
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    human = os.getenv("LOG_HUMAN", "1") == "1"
    log_file = os.getenv("LOG_FILE", "logs/prism.log")
    max_bytes = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # ルートロガーの設定
    root = logging.getLogger()
    root.setLevel(getattr(logging, level, logging.INFO))
    root.handlers.clear()
    
    # コンソールハンドラー
    stream_handler = logging.StreamHandler()
    if human:
        stream_handler.setFormatter(SecureHumanFormatter("[%(levelname)s] %(name)s: %(message)s"))
    else:
        stream_handler.setFormatter(SecureJsonFormatter())
    root.addHandler(stream_handler)
    
    # ファイルハンドラー（ローテーション付き）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    if human:
        file_handler.setFormatter(SecureHumanFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    else:
        file_handler.setFormatter(SecureJsonFormatter())
    root.addHandler(file_handler)
    
    # 特定のライブラリのログレベルを調整
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # ログ設定完了の通知
    logger = logging.getLogger(__name__)
    logger.info(f"Secure logging configured - Level: {level}, File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得"""
    return logging.getLogger(name)


class LoggerMixin:
    """ログ機能を提供するMixinクラス"""
    
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)


