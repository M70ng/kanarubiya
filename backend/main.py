from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from api.kanafy_ko import router as korean_router
import os
import re
import time
import asyncio
import argparse

# レート制限: 1分あたりのリクエスト数（環境変数 RATE_LIMIT_PER_MINUTE で上書き可、0 で無効）
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_WINDOW_SEC = 60
_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_lock = asyncio.Lock()

# クローラー・スクレイパーとみなす User-Agent パターン（API を叩かせない）
CRAWLER_UA_PATTERNS = [
    re.compile(r"googlebot", re.I),
    re.compile(r"bingbot", re.I),
    re.compile(r"slurp|duckduckbot|baiduspider|yandexbot", re.I),
    re.compile(r"facebookexternalhit|twitterbot|linkedinbot", re.I),
    re.compile(r"crawler|spider|scraper", re.I),
    re.compile(r"bot\b", re.I),
    re.compile(r"curl|wget|python-requests|go-http-client", re.I),
    re.compile(r"petalbot|ahrefsbot|semrushbot|mj12bot", re.I),
]


class CrawlerBlockMiddleware(BaseHTTPMiddleware):
    """クローラーと判断したリクエストを 403 で弾く"""

    async def dispatch(self, request: Request, call_next) -> Response:
        ua = request.headers.get("user-agent") or ""
        if any(p.search(ua) for p in CRAWLER_UA_PATTERNS):
            return Response(content="Forbidden", status_code=403)
        response = await call_next(request)
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティ関連ヘッダーを付与"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def _client_ip(request: Request) -> str:
    """プロキシ経由の場合は X-Forwarded-For の先頭、それ以外は client.host"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP ごとに 1 分あたり N リクエストを制限（超過時 429）"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if RATE_LIMIT_PER_MINUTE <= 0:
            return await call_next(request)
        # ヘルスチェックは制限対象外（LB が 429 を受けないように）
        if request.url.path.rstrip("/") in ("/health", "/api/kanafy-ko/health"):
            return await call_next(request)
        ip = _client_ip(request)
        now = time.monotonic()
        async with _rate_limit_lock:
            if ip not in _rate_limit_store:
                _rate_limit_store[ip] = []
            times = _rate_limit_store[ip]
            # 窓より古いものを削除
            cutoff = now - RATE_LIMIT_WINDOW_SEC
            while times and times[0] < cutoff:
                times.pop(0)
            if len(times) >= RATE_LIMIT_PER_MINUTE:
                return Response(
                    content="Too Many Requests",
                    status_code=429,
                    headers={"Retry-After": str(RATE_LIMIT_WINDOW_SEC)},
                )
            times.append(now)
        return await call_next(request)

# 本番で Swagger/ReDoc を無効化（DISABLE_DOCS=1 で /docs, /redoc, /openapi.json を無効）
DISABLE_DOCS = os.environ.get("DISABLE_DOCS", "").lower() in ("1", "true", "yes")

# FastAPIアプリケーションの作成（メインは歌詞→かな読み変換API）
app = FastAPI(
    title="歌詞→かな読み変換 API",
    description="歌詞・韓国語テキストを日本語かな読みに変換するAPI。メイン: POST /api/kanafy-ko。LRC貼り付け・バッチ変換対応。",
    version="2.0.0",
    docs_url=None if DISABLE_DOCS else "/docs",
    redoc_url=None if DISABLE_DOCS else "/redoc",
    openapi_url=None if DISABLE_DOCS else "/openapi.json",
)

# セキュリティヘッダー（X-Content-Type-Options, X-Frame-Options 等）
app.add_middleware(SecurityHeadersMiddleware)

# レート制限（IP あたり 1 分間のリクエスト数制限、RATE_LIMIT_PER_MINUTE=0 で無効）
app.add_middleware(RateLimitMiddleware)

# クローラー対策（User-Agent でボットを 403、全レスポンスに X-Robots-Tag 付与）
app.add_middleware(CrawlerBlockMiddleware)

# CORS（本番は CORS_ORIGINS に https://あなたのドメイン を設定）
# 末尾スラッシュを削除（ブラウザの Origin ヘッダーは通常スラッシュなし）
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(korean_router)

# ルートエンドポイント（メインは変換API）
@app.get("/")
async def root():
    endpoints = {
        "conversion": {
            "description": "歌詞・韓国語→かな読み変換（メイン）",
            "convert": "POST /api/kanafy-ko",
            "batch_convert": "POST /api/kanafy-ko/batch",
            "lrc_paste": "POST /api/kanafy-ko/lrc",
            "lrc_upload": "POST /api/kanafy-ko/lrc/upload",
            "dictionary_add": "POST /api/kanafy-ko/dictionary",
            "health": "GET /api/kanafy-ko/health",
            "test": "GET /api/kanafy-ko/test",
        },
    }
    if not DISABLE_DOCS:
        endpoints["docs"] = "/docs"
    return {
        "message": "歌詞→かな読み変換 API",
        "version": "2.0.0",
        "endpoints": endpoints,
    }

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="歌詞→かな読み変換 API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
