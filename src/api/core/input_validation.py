#!/usr/bin/env python3
"""
PRISM Input Validation and Sanitization Module
入力検証・サニタイゼーション機能
"""

import re
import html
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import bleach

logger = logging.getLogger(__name__)

@dataclass
class ValidationRule:
    """検証ルール"""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    required: bool = True
    allowed_tags: List[str] = None
    allowed_attributes: Dict[str, List[str]] = None
    max_file_size: Optional[int] = None  # bytes
    allowed_extensions: List[str] = None

class InputValidator:
    """入力検証器"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """デフォルトルールを設定"""
        # テキスト入力の基本ルール
        self.rules["text"] = ValidationRule(
            min_length=1,
            max_length=1000,
            pattern=r"^[a-zA-Z0-9\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF.,!?\-_()]+$"
        )
        
        # タイトル用ルール
        self.rules["title"] = ValidationRule(
            min_length=1,
            max_length=200,
            pattern=r"^[a-zA-Z0-9\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF.,!?\-_()]+$"
        )
        
        # 内容用ルール（HTMLタグ許可）
        self.rules["content"] = ValidationRule(
            min_length=1,
            max_length=10000,
            allowed_tags=["p", "br", "strong", "em", "ul", "ol", "li", "a"],
            allowed_attributes={"a": ["href", "title"]}
        )
        
        # URL用ルール
        self.rules["url"] = ValidationRule(
            pattern=r"^https?://[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+$"
        )
        
        # メールアドレス用ルール
        self.rules["email"] = ValidationRule(
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        
        # 日付用ルール
        self.rules["date"] = ValidationRule(
            pattern=r"^\d{4}-\d{2}-\d{2}$"
        )
        
        # ファイル用ルール
        self.rules["file"] = ValidationRule(
            max_file_size=10 * 1024 * 1024,  # 10MB
            allowed_extensions=["txt", "md", "pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"]
        )
    
    def validate_text(self, value: Any, rule_name: str = "text") -> Dict[str, Any]:
        """テキストを検証"""
        if not isinstance(value, str):
            return {"valid": False, "error": "Value must be a string"}
        
        if rule_name not in self.rules:
            return {"valid": False, "error": f"Unknown rule: {rule_name}"}
        
        rule = self.rules[rule_name]
        
        # 必須チェック
        if rule.required and not value.strip():
            return {"valid": False, "error": "Value is required"}
        
        # 長さチェック
        if rule.min_length and len(value) < rule.min_length:
            return {"valid": False, "error": f"Value too short (minimum: {rule.min_length})"}
        
        if rule.max_length and len(value) > rule.max_length:
            return {"valid": False, "error": f"Value too long (maximum: {rule.max_length})"}
        
        # パターンチェック
        if rule.pattern and not re.match(rule.pattern, value):
            return {"valid": False, "error": "Value does not match required pattern"}
        
        return {"valid": True, "sanitized": value}
    
    def sanitize_html(self, value: str, rule_name: str = "content") -> str:
        """HTMLをサニタイズ"""
        if rule_name not in self.rules:
            return html.escape(value)
        
        rule = self.rules[rule_name]
        
        if rule.allowed_tags:
            # bleachを使用してHTMLをサニタイズ
            allowed_tags = rule.allowed_tags
            allowed_attributes = rule.allowed_attributes or {}
            
            return bleach.clean(
                value,
                tags=allowed_tags,
                attributes=allowed_attributes,
                strip=True
            )
        else:
            # HTMLタグをエスケープ
            return html.escape(value)
    
    def validate_json(self, value: str) -> Dict[str, Any]:
        """JSONを検証"""
        try:
            parsed = json.loads(value)
            return {"valid": True, "parsed": parsed}
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"Invalid JSON: {str(e)}"}
    
    def validate_file(self, filename: str, file_size: int) -> Dict[str, Any]:
        """ファイルを検証"""
        rule = self.rules.get("file")
        if not rule:
            return {"valid": False, "error": "File validation rule not found"}
        
        # ファイルサイズチェック
        if rule.max_file_size and file_size > rule.max_file_size:
            return {
                "valid": False,
                "error": f"File too large (maximum: {rule.max_file_size / 1024 / 1024:.1f}MB)"
            }
        
        # 拡張子チェック
        if rule.allowed_extensions:
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if file_ext not in rule.allowed_extensions:
                return {
                    "valid": False,
                    "error": f"File type not allowed. Allowed: {', '.join(rule.allowed_extensions)}"
                }
        
        return {"valid": True, "filename": filename, "size": file_size}
    
    def validate_request_data(self, data: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
        """リクエストデータを一括検証"""
        results = {}
        errors = []
        
        for field, rule_name in schema.items():
            if field not in data:
                if self.rules.get(rule_name, ValidationRule()).required:
                    errors.append(f"Required field '{field}' is missing")
                continue
            
            validation_result = self.validate_text(data[field], rule_name)
            if not validation_result["valid"]:
                errors.append(f"Field '{field}': {validation_result['error']}")
            else:
                results[field] = validation_result["sanitized"]
        
        return {
            "valid": len(errors) == 0,
            "data": results,
            "errors": errors
        }
    
    def detect_sql_injection(self, value: str) -> bool:
        """SQLインジェクション攻撃を検出"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
            r"(\b(OR|AND)\s+\".*\"\s*=\s*\".*\")",
            r"(\b(OR|AND)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*)",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(UNION|UNION ALL)\b)",
            r"(\b(EXEC|EXECUTE)\b)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def detect_xss(self, value: str) -> bool:
        """XSS攻撃を検出"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def sanitize_input(self, value: str, input_type: str = "text") -> str:
        """入力をサニタイズ"""
        if not isinstance(value, str):
            return str(value)
        
        # SQLインジェクション検出
        if self.detect_sql_injection(value):
            logger.warning(f"Potential SQL injection detected: {value[:100]}...")
            return ""
        
        # XSS検出
        if self.detect_xss(value):
            logger.warning(f"Potential XSS detected: {value[:100]}...")
            return html.escape(value)
        
        # HTMLサニタイゼーション
        if input_type == "html":
            return self.sanitize_html(value)
        else:
            return html.escape(value)

# グローバル入力検証器
input_validator = InputValidator()

def validate_and_sanitize(data: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
    """データを検証・サニタイズ"""
    return input_validator.validate_request_data(data, schema)

def sanitize_text(value: str, input_type: str = "text") -> str:
    """テキストをサニタイズ"""
    return input_validator.sanitize_input(value, input_type)
