import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, classify, query, metrics, async_endpoints, analytics, semantic_search, ai_assistant, auto_reports, notifications, advanced_notifications, performance, security, monitoring
from .core.logging import configure_logging
from .core.security_middleware import SecurityMiddleware


configure_logging()

app = FastAPI(title="PRISM API", version="1.0.0")

# セキュアなCORS設定
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8061,http://localhost:3000").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

app.include_router(health.router)
app.include_router(classify.router)
app.include_router(query.router)
app.include_router(metrics.router)
app.include_router(async_endpoints.router)
app.include_router(analytics.router)
app.include_router(semantic_search.router)
app.include_router(ai_assistant.router)
app.include_router(auto_reports.router)
app.include_router(notifications.router)
app.include_router(advanced_notifications.router)
app.include_router(performance.router)
app.include_router(security.router)
app.include_router(monitoring.router)

# セキュリティミドルウェアを追加
app.add_middleware(SecurityMiddleware, enable_rate_limiting=True, enable_monitoring=True)


@app.get("/")
def root():
    return {"ok": True, "service": "prism", "version": "1.0.0"}

