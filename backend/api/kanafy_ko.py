# backend/api/kanafy_ko.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional
import sys
import os

# バックエンドのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.korean_to_kana import KoreanToKanaConverter
from core.lrc_processor import LrcProcessor
from core.hangul2kana import add_user_exception

router = APIRouter(prefix="/api", tags=["korean-conversion"])

# リクエストサイズ制限（DoS・負荷対策）
MAX_TEXT_LENGTH = 50_000
MAX_BATCH_ITEMS = 100
MAX_LRC_CONTENT_LENGTH = 500_000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB

# リクエストモデル
class KoreanTextRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)
    use_g2pk: bool = True

class KoreanBatchRequest(BaseModel):
    texts: List[Annotated[str, Field(max_length=MAX_TEXT_LENGTH)]] = Field(..., max_length=MAX_BATCH_ITEMS)
    use_g2pk: bool = True

class LrcContentRequest(BaseModel):
    content: str = Field(..., max_length=MAX_LRC_CONTENT_LENGTH)
    use_g2pk: bool = True

class DictionaryAddRequest(BaseModel):
    hangul: str = Field(..., max_length=200)
    kana: str = Field(..., max_length=500)

# レスポンスモデル
class KoreanTextResponse(BaseModel):
    original: str
    phonetic_hangul: str
    kana: str
    use_g2pk: bool
    error: Optional[str] = None

class KoreanBatchResponse(BaseModel):
    results: List[KoreanTextResponse]

class LrcLineDetail(BaseModel):
    line_number: int
    original: str
    processed: str
    type: str
    timestamp: str
    original_lyrics: str
    converted_lyrics: str
    error: Optional[str] = None

class LrcResponse(BaseModel):
    original_content: str
    processed_content: str
    line_details: List[LrcLineDetail]
    use_g2pk: bool
    total_lines: int
    lyrics_lines: int
    metadata_lines: int

# 変換器のインスタンス
converter = KoreanToKanaConverter()
lrc_processor = LrcProcessor()

@router.post("/kanafy-ko", response_model=KoreanTextResponse)
async def convert_korean_to_kana(request: KoreanTextRequest):
    """
    韓国語テキストを日本語カナに変換
    
    - **text**: 変換する韓国語テキスト
    - **use_g2pk**: g2pkを使用するかどうか（デフォルト: True）
    """
    try:
        result = converter.convert_with_details(request.text, request.use_g2pk)
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
            result = converter.convert_with_details(text, request.use_g2pk)
            results.append(KoreanTextResponse(**result))
        
        return KoreanBatchResponse(results=results)
    except Exception:
        raise HTTPException(status_code=500, detail="一括変換に失敗しました。")

@router.post("/kanafy-ko/lrc", response_model=LrcResponse)
async def convert_lrc_content(request: LrcContentRequest):
    """
    LRCファイルの内容を処理して韓国語歌詞をカナに変換
    
    - **content**: LRCファイルの内容
    - **use_g2pk**: g2pkを使用するかどうか（デフォルト: True）
    """
    try:
        result = lrc_processor.process_lrc_with_details(request.content, request.use_g2pk)
        return LrcResponse(**result)
    except Exception:
        raise HTTPException(status_code=500, detail="LRCの変換に失敗しました。")

@router.post("/kanafy-ko/lrc/upload")
async def upload_and_convert_lrc(
    file: UploadFile = File(...),
    use_g2pk: bool = True
):
    """
    LRCファイルをアップロードして変換
    
    - **file**: アップロードするLRCファイル
    - **use_g2pk**: g2pkを使用するかどうか（デフォルト: True）
    """
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズは {MAX_UPLOAD_BYTES // (1024*1024)}MB 以内にしてください。",
            )
        content_str = content.decode("utf-8", errors="replace")
        
        # 処理
        result = lrc_processor.process_lrc_with_details(content_str, use_g2pk)
        
        return {
            'success': True,
            'original_filename': file.filename,
            'processed_content': result['processed_content'],
            'line_details': result['line_details'],
            'total_lines': result['total_lines'],
            'lyrics_lines': result['lyrics_lines'],
            'metadata_lines': result['metadata_lines'],
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="ファイルの処理に失敗しました。")

@router.post("/kanafy-ko/dictionary")
async def add_dictionary_entry(request: DictionaryAddRequest):
    """
    変換漏れ報告: ハングルと読みをユーザー辞書に追加する。
    次回以降の変換でこのエントリが使われます。
    """
    try:
        add_user_exception(request.hangul, request.kana)
        return {"success": True, "hangul": request.hangul, "kana": request.kana}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))  # バリデーション理由はユーザーに返してよい
    except Exception:
        raise HTTPException(status_code=500, detail="辞書の追加に失敗しました。")

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

@router.get("/kanafy-ko/test/lrc")
async def test_lrc_conversion():
    """
    LRC変換テスト用エンドポイント
    """
    test_lrc = """[ti:テスト曲]
[ar:テストアーティスト]
[al:テストアルバム]

[00:00.00]오늘의 Color
[00:03.45]전화가 울렸어요
[00:07.12]한국어 노래
[00:10.30]Let's go! 라는 노래야
[00:13.45]배터리 battery"""
    
    result = lrc_processor.process_lrc_with_details(test_lrc, use_g2pk=True)
    return LrcResponse(**result)
