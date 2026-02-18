**カナルビ屋** — 歌詞・韓国語を入力してかな読みに変換するアプリです。

## バックエンド（変換API）の起動

`ModuleNotFoundError: No module named 'g2pk'` や `mecab-config not found` が出る場合は、**先に MeCab をシステムにインストール**してから仮想環境で依存関係を入れます。

**macOS（Homebrew）:**

```bash
brew install mecab mecab-ipadic
```

その後:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-convert.txt   # 変換API（g2pk 必須）
python main.py
```

g2pk は MeCab に依存するため、上記の MeCab インストールを先に行ってください。

- **変換APIのみ**: `python main.py`（デフォルト）
- **自動LRC生成も使う**: `python main.py --with-lrc-generator`

## フロントエンド

**「辞書に追加」や変換を使うには、上記のバックエンドを先に起動してください。**  
開発時はフロントが `http://localhost:3000` で `/api/*` を `http://localhost:8000` に転送します。

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## デプロイ時のセキュリティ・設定

- **CORS**: バックエンドの本番ドメインを許可するため、環境変数 `CORS_ORIGINS` にフロントのオリジン（例: `https://your-app.vercel.app`）をカンマ区切りで設定してください。
- **API の URL**: フロントから別ホストの API を叩く場合は `NEXT_PUBLIC_API_BASE_URL` にバックエンドの URL を設定してください。
- クローラー対策（robots.txt / メタ / User-Agent ブロック）、リクエストサイズ制限、セキュリティヘッダー（X-Content-Type-Options 等）、エラー内容の非開示は実装済みです。本番では HTTPS 化を推奨します。

### レート制限（バックエンド）

IP あたり「1 分間に N 回まで」の制限が入っています。超過すると **429 Too Many Requests** を返し、レスポンスに `Retry-After: 60` が付きます。

| 環境変数 | 説明 | 例 |
|----------|------|-----|
| `RATE_LIMIT_PER_MINUTE` | 1 分あたりの最大リクエスト数。`0` で無効 | `60`（デフォルト） |

**手順（本番で変更する場合）:**

```bash
# 例: 1 分あたり 120 回までに緩和
export RATE_LIMIT_PER_MINUTE=120
python main.py

# レート制限を無効にする（非推奨）
export RATE_LIMIT_PER_MINUTE=0
```

- `/health` と `/api/kanafy-ko/health` は制限対象外です（ロードバランサのヘルスチェックが 429 にならないように）。
- プロキシやロードバランサ経由の場合は、バックエンドに `X-Forwarded-For` が渡るようにしてください。渡らないと全クライアントが同一 IP とみなされます。

### 本番で /docs（Swagger）・/redoc を無効化

API 仕様の Swagger UI（`/docs`）と ReDoc（`/redoc`）、および `/openapi.json` を本番では出したくない場合に使います。

**手順:**

1. バックエンドの環境変数で **`DISABLE_DOCS=1`**（または `true` / `yes`）を設定する。

```bash
# 本番起動例
export DISABLE_DOCS=1
python main.py
```

2. デプロイ先（Docker / systemd / クラウドの設定）でも同じ変数を設定する。

- 設定後は `/docs`・`/redoc`・`/openapi.json` にアクセスしても **404** になります。
- 開発時は環境変数を設定しなければ従来どおり `/docs` が利用できます。

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
