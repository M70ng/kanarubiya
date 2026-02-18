#!/usr/bin/env python3
"""
APIテストスクリプト - ローカルでAPIをたくさん叩いてテストする
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# User-Agentを設定してクローラーブロックを回避
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def print_response(title, response):
    """レスポンスを整形して表示"""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except:
        print(f"Response: {response.text[:500]}")

def test_health():
    """ヘルスチェック"""
    print_response("ヘルスチェック", requests.get(f"{BASE_URL}/health", headers=HEADERS))
    print_response("変換API ヘルスチェック", requests.get(f"{BASE_URL}/api/kanafy-ko/health", headers=HEADERS))

def test_root():
    """ルートエンドポイント"""
    print_response("ルートエンドポイント", requests.get(f"{BASE_URL}/", headers=HEADERS))

def test_convert_single():
    """単一テキスト変換"""
    test_cases = [
        {"text": "한글", "use_g2pk": True},
        {"text": "내 손을 잡아", "use_g2pk": True},
        {"text": "파닭", "use_g2pk": True},
        {"text": "한국어", "use_g2pk": False},
        {"text": "걱정?! 하지 마.", "use_g2pk": True},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print_response(f"単一変換 {i}: {test_case['text']}", 
                      requests.post(f"{BASE_URL}/api/kanafy-ko", json=test_case, headers=HEADERS))

def test_convert_batch():
    """バッチ変換"""
    batch_data = {
        "texts": [
            "한글",
            "내 손을 잡아",
            "파닭",
            "한국어",
            "걱정?! 하지 마."
        ],
        "use_g2pk": True
    }
    print_response("バッチ変換", requests.post(f"{BASE_URL}/api/kanafy-ko/batch", json=batch_data, headers=HEADERS))

def test_dictionary_add():
    """辞書追加"""
    test_entries = [
        {"hangul": "테스트", "kana": "テスト"},
        {"hangul": "한글", "kana": "ハングル"},
    ]
    
    for entry in test_entries:
        print_response(f"辞書追加: {entry['hangul']} -> {entry['kana']}", 
                      requests.post(f"{BASE_URL}/api/kanafy-ko/dictionary", json=entry, headers=HEADERS))

def test_test_endpoints():
    """テスト用エンドポイント"""
    print_response("テスト変換", requests.get(f"{BASE_URL}/api/kanafy-ko/test", headers=HEADERS))

def test_automated_lrc_health():
    """自動LRC生成APIのヘルスチェック"""
    print_response("自動LRC生成 ヘルスチェック", 
                  requests.get(f"{BASE_URL}/api/automated-lrc/health", headers=HEADERS))

def test_automated_lrc_models():
    """利用可能なモデル取得"""
    print_response("利用可能なモデル", 
                  requests.get(f"{BASE_URL}/api/automated-lrc/models", headers=HEADERS))

def main():
    """メイン実行"""
    print("🚀 APIテスト開始")
    print(f"📍 Base URL: {BASE_URL}")
    
    try:
        # 基本エンドポイント
        test_root()
        test_health()
        
        # 変換API
        test_convert_single()
        test_convert_batch()
        test_dictionary_add()
        test_test_endpoints()
        
        # 自動LRC生成API（オプション）
        try:
            test_automated_lrc_health()
            test_automated_lrc_models()
        except requests.exceptions.RequestException as e:
            print(f"\n⚠️  自動LRC生成APIは利用できません: {e}")
        
        print("\n" + "="*60)
        print("✅ テスト完了")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ エラー: {BASE_URL} に接続できません")
        print("   バックエンドサーバーが起動しているか確認してください:")
        print("   cd backend && python main.py")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
