
import os
import secrets
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings


class SecurityConfig:
    """セキュリティ設定管理"""
    
    @staticmethod
    def generate_encryption_key() -> bytes:
        """暗号化キーを生成"""
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt_value(value: str, key: bytes) -> str:
        """値を暗号化"""
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()
    
    @staticmethod
    def decrypt_value(encrypted_value: str, key: bytes) -> str:
        """値を復号化"""
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()


class Settings(BaseSettings):
    # 基本設定
    prism_env: str = "development"
    api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    notion_api_key: Optional[str] = None
    mcp_base_url: Optional[str] = None
    
    # セキュリティ設定
    cors_origins: str = "http://localhost:8061,http://localhost:3000"
    jwt_your_notion_api_key_here: Optional[str] = None
    encryption_key: Optional[str] = None
    
    # パフォーマンス設定
    worker_interval: int = 60
    max_concurrent_requests: int = 10
    max_request_size: int = 1024 * 1024  # 1MB
    
    # ログ設定
    log_level: str = "INFO"
    log_file: str = "logs/prism.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # セキュリティキーの初期化
        if not self.jwt_your_notion_api_key_here:
            self.jwt_your_notion_api_key_here = secrets.token_urlsafe(32)
        
        if not self.encryption_key:
            self.encryption_key = SecurityConfig.generate_encryption_key().decode()
        
        # APIキーの検証
        if self.prism_env == "production" and not self.api_key:
            raise ValueError("API_KEY is required in production environment")
        
        if self.prism_env == "production" and self.api_key == "changeme-api-key":
            raise ValueError("Default API key is not allowed in production environment")


def load_config() -> Settings:
    """設定を読み込み"""
    config_path = Path("config/default.yaml")
    if config_path.exists():
        # YAML設定ファイルがある場合は読み込み（将来の拡張用）
        pass
    
    return Settings()


