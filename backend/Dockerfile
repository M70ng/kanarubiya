# 歌詞→かな読み変換 API（g2pk 用に MeCab をインストール）
FROM python:3.11-slim

WORKDIR /app

# MeCab と辞書（g2pk の依存）
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    libmecab-dev \
    mecab-ipadic \
    mecab-ipadic-utf8 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

# Render は PORT 環境変数でポートを指定する
# Render は実行時に PORT を渡すためシェルで展開
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
