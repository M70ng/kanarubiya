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
import ipaddress
from collections import deque

# 制限はワーカー単位。複数台構成では外部の共有レート制限も必要。
RATE_LIMIT_PER_MINUTE = max(1, int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20")))
GLOBAL_RATE_LIMIT_PER_MINUTE = max(1, int(os.environ.get("GLOBAL_RATE_LIMIT_PER_MINUTE", "600")))
RATE_LIMIT_WINDOW_SEC = 60
MAX_RATE_LIMIT_CLIENTS = 10000
MAX_REQUEST_BYTES = 128 * 1024
_rate_limit_store: dict[str, deque[float]] = {}
_global_requests: deque[float] = deque()
_rate_limit_lock = asyncio.Lock()
# 接続元プロキシのCIDRだけを明示する。未設定時は転送ヘッダーを信用しない。
TRUSTED_PROXY_NETWORKS = tuple(
    ipaddress.ip_network(value.strip(), strict=False)
    for value in os.environ.get("TRUSTED_PROXY_CIDRS", "").split(",")
    if value.strip()
)


class RequestSizeLimitMiddleware:
    """Content-Length の有無に関係なく、JSON解析前に本文を制限する。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await Response("Invalid Content-Length", status_code=400)(scope, receive, send)
        if length < 0 or length > MAX_REQUEST_BYTES:
            return await Response("Request too large", status_code=413)(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > MAX_REQUEST_BYTES:
                return await Response("Request too large", status_code=413)(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


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
    """信頼済みプロキシからの場合だけ、右から順に転送元を確認する。"""
    peer = request.client.host if request.client else "unknown"
    # Render public web-service ingress provides CF-Connecting-IP. Private-network
    # callers must be trusted; they do not pass through this ingress.
    if os.environ.get("RENDER") == "true":
        connecting_ip = request.headers.get("cf-connecting-ip", "")
        try:
            return str(ipaddress.ip_address(connecting_ip))
        except ValueError:
            pass
    try:
        current = ipaddress.ip_address(peer)
        if not any(current in network for network in TRUSTED_PROXY_NETWORKS):
            return str(current)
        forwarded = request.headers.get("x-forwarded-for", "")
        hops = forwarded.split(",") if forwarded else []
        if len(hops) > 20:
            return str(current)
        for hop in reversed(hops):
            if not any(current in network for network in TRUSTED_PROXY_NETWORKS):
                break
            current = ipaddress.ip_address(hop.strip())
        return str(current)
    except ValueError:
        return peer


class RateLimitMiddleware(BaseHTTPMiddleware):
    """クライアント別と全体の両方に1分間の上限を設ける。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.rstrip("/") in ("/health", "/api/kanafy-ko/health"):
            return await call_next(request)
        ip = _client_ip(request)
        now = time.monotonic()
        cutoff = now - RATE_LIMIT_WINDOW_SEC
        async with _rate_limit_lock:
            while _global_requests and _global_requests[0] <= cutoff:
                _global_requests.popleft()
            if len(_global_requests) >= GLOBAL_RATE_LIMIT_PER_MINUTE:
                return Response("Too Many Requests", status_code=429, headers={"Retry-After": "60"})
            _global_requests.append(now)
            # 古いクライアントを削除し、偽装IP等で無制限に増えないようにする。
            for key in list(_rate_limit_store):
                times = _rate_limit_store[key]
                while times and times[0] <= cutoff:
                    times.popleft()
                if not times:
                    del _rate_limit_store[key]
            if ip not in _rate_limit_store and len(_rate_limit_store) >= MAX_RATE_LIMIT_CLIENTS:
                return Response("Too Many Requests", status_code=429, headers={"Retry-After": "60"})
            times = _rate_limit_store.setdefault(ip, deque())
            if len(times) >= RATE_LIMIT_PER_MINUTE:
                return Response("Too Many Requests", status_code=429, headers={"Retry-After": "60"})
            times.append(now)
            remaining = RATE_LIMIT_PER_MINUTE - len(times)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

# 本番で Swagger/ReDoc を無効化（DISABLE_DOCS=1 で /docs, /redoc, /openapi.json を無効）
DISABLE_DOCS = os.environ.get("DISABLE_DOCS", "").lower() in ("1", "true", "yes")

# FastAPIアプリケーションの作成（メインは歌詞→かな読み変換API）
app = FastAPI(
    title="歌詞→かな読み変換 API",
    description="歌詞・韓国語テキストを日本語かな読みに変換するAPI。メイン: POST /api/kanafy-ko。バッチ変換対応。",
    version="2.0.0",
    docs_url=None if DISABLE_DOCS else "/docs",
    redoc_url=None if DISABLE_DOCS else "/redoc",
    openapi_url=None if DISABLE_DOCS else "/openapi.json",
)

# セキュリティヘッダー（X-Content-Type-Options, X-Frame-Options 等）
app.add_middleware(SecurityHeadersMiddleware)

# レート制限（IP あたり 1 分間のリクエスト数制限）
app.add_middleware(RateLimitMiddleware)

app.add_middleware(RequestSizeLimitMiddleware)

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
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload, proxy_headers=False)
