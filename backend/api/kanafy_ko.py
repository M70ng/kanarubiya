# backend/api/kanafy_ko.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, List, Optional
import sys
import os

# バックエンドのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.korean_to_kana import KoreanToKanaConverter

router = APIRouter(prefix="/api", tags=["korean-conversion"])

# リクエストサイズ制限（DoS・負荷対策）
MAX_TEXT_LENGTH = 10_000
MAX_BATCH_ITEMS = 10
MAX_BATCH_TOTAL_LENGTH = 20_000

# リクエストモデル
class KoreanTextRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)
    use_g2pk: bool = True
    convert_numbers: bool = False

class KoreanBatchRequest(BaseModel):
    texts: List[Annotated[str, Field(max_length=MAX_TEXT_LENGTH)]] = Field(..., max_length=MAX_BATCH_ITEMS)
    use_g2pk: bool = True
    convert_numbers: bool = False

    @model_validator(mode="after")
    def limit_total_length(self):
        if sum(map(len, self.texts)) > MAX_BATCH_TOTAL_LENGTH:
            raise ValueError("一括変換の合計は20,000文字以内にしてください")
        return self

# レスポンスモデル
class KoreanTextResponse(BaseModel):
    original: str
    phonetic_hangul: str
    kana: str
    use_g2pk: bool
    convert_numbers: Optional[bool] = None
    error: Optional[str] = None

class KoreanBatchResponse(BaseModel):
    results: List[KoreanTextResponse]

# 変換器のインスタンス
converter = KoreanToKanaConverter()

@router.post("/kanafy-ko", response_model=KoreanTextResponse)
async def convert_korean_to_kana(request: KoreanTextRequest):
    """
    韓国語テキストを日本語カナに変換
    
    - **text**: 変換する韓国語テキスト
    - **use_g2pk**: g2pkを使用するかどうか（デフォルト: True）
    - **convert_numbers**: 数字を韓国語読みでカナ変換するか（デフォルト: False）
    """
    try:
        result = converter.convert_with_details(
            request.text, request.use_g2pk, request.convert_numbers
        )
        return KoreanTextResponse(**result)
    except Exception:
        raise HTTPException(status_code=500, detail="変換に失敗しました。")

@router.post("/kanafy-ko/batch", response_model=KoreanBatchResponse)
async def convert_korean_batch_to_kana(request: KoreanBatchRequest):
    """
    複数の韓国語テキストを一括で日本語カナに変換
    
    - **texts**: 変換する韓国語テキストのリスト
    - **use_g2pk**: g2pkを使用するかどうか（デフォルト: True）
    """
    try:
        results = []
        for text in request.texts:
            result = converter.convert_with_details(
                text, request.use_g2pk, request.convert_numbers
            )
            results.append(KoreanTextResponse(**result))
        
        return KoreanBatchResponse(results=results)
    except Exception:
        raise HTTPException(status_code=500, detail="一括変換に失敗しました。")

@router.get("/kanafy-ko/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {
        "status": "healthy",
        "service": "Korean to Kana Converter",
        "version": "1.0.0"
    }

# テスト用エンドポイント
@router.get("/kanafy-ko/test")
async def test_conversion():
    """
    テスト用エンドポイント
    """
    test_cases = [
        "한글",
        "내 손을 잡아",
        "파닭",
        "한국어",
        "걱정?! 하지 마."
    ]
    
    results = []
    for text in test_cases:
        result = converter.convert_with_details(text, use_g2pk=True)
        results.append(KoreanTextResponse(**result))
    
    return KoreanBatchResponse(results=results)
