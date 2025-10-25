"""
セキュアなAPI認証機能
"""
import os
import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import jwt

# セキュリティ設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class SecurityManager:
    """セキュリティ管理クラス"""
    
    @staticmethod
    def generate_api_key() -> str:
        """新しいAPIキーを生成"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """APIキーをハッシュ化"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """APIキーを検証"""
        return SecurityManager.hash_api_key(api_key) == hashed_key
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """JWTアクセストークンを作成"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """JWTトークンを検証"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """APIキーを検証する依存関数"""
    api_key = credentials.credentials
    expected_key = os.getenv("API_KEY")
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    if not SecurityManager.verify_api_key(api_key, SecurityManager.hash_api_key(expected_key)):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key

def verify_token_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWTトークンを検証する依存関数"""
    token = credentials.credentials
    payload = SecurityManager.verify_token(token)
    return payload

def get_current_user(token: str = Depends(verify_token_auth)):
    """現在のユーザー情報を取得"""
    return token
