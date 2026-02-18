import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * クローラー対策: よくあるボットのUser-Agentを検出してブロック or X-Robots-Tag 付与
 * マナー良く従うボットは通過させ、全レスポンスに noindex を付与
 */
const CRAWLER_UA_PATTERNS = [
  /googlebot/i,
  /bingbot/i,
  /slurp/i, // Yahoo
  /duckduckbot/i,
  /baiduspider/i,
  /yandexbot/i,
  /facebookexternalhit/i,
  /twitterbot/i,
  /rogerbot/i, // Moz
  /linkedinbot/i,
  /embedly/i,
  /quora link preview/i,
  /showyoubot/i,
  /outbrain/i,
  /pinterest/i,
  /slackbot/i,
  /vkshare/i,
  /w3c_validator/i,
  /crawler/i,
  /spider/i,
  /bot\b/i,
  /scraper/i,
  /curl/i,
  /wget/i,
  /python-requests/i,
  /go-http-client/i,
  /java\s*\d*/i, // Java HTTP clients
  /petalbot/i,
  /ahrefsbot/i,
  /semrushbot/i,
  /dotbot/i,
  /mj12bot/i,
];

function isCrawlerUserAgent(ua: string | null): boolean {
  if (!ua) return false;
  return CRAWLER_UA_PATTERNS.some((re) => re.test(ua));
}

export function middleware(request: NextRequest) {
  const ua = request.headers.get("user-agent") ?? "";
  const response = NextResponse.next();

  // 全レスポンスにクローラー向けヘッダを付与（インデックスさせない）
  response.headers.set("X-Robots-Tag", "noindex, nofollow, noarchive, nosnippet");

  // 明らかなクローラー/スクレイパーは 403 で弾く（サーバー負荷軽減）
  if (isCrawlerUserAgent(ua)) {
    return new NextResponse("Forbidden", { status: 403 });
  }

  return response;
}

export const config = {
  // 全パスで実行（path-to-regexp 形式。静的も通過させるだけなので問題なし）
  matcher: ["/", "/:path*"],
};
