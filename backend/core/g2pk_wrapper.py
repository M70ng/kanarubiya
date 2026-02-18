from g2pk import G2p
import re

class G2pkWrapper:
    def __init__(self):
        """g2pkの初期化"""
        self.g2p = G2p()
    
    def is_hangul(self, token: str) -> bool:
        """
        トークンがハングルのみで構成されているかチェック
        
        Args:
            token: チェックする文字列
        
        Returns:
            ハングルのみの場合True
        """
        return bool(re.fullmatch(r"[가-힣]+", token))
    
    def split_mixed_text(self, text: str) -> list[str]:
        """
        ハングル、英数字、その他記号を区別して分割
        
        Args:
            text: 分割するテキスト
        
        Returns:
            分割されたトークンのリスト
        """
        # ハングル、英数字、その他記号、空白を区別して分割
        return re.findall(r"[가-힣]+|[a-zA-Z0-9'']+|[^\s가-힣a-zA-Z0-9]+|\s", text)
    
    def convert(self, text: str, descriptive: bool = True) -> str:
        """
        韓国語テキストをg2pkで処理して発音に近いハングルに変換
        ハングル部分のみを変換し、英語・記号・数字はそのまま残す
        
        Args:
            text: 韓国語テキスト
            descriptive: 実際の発音モード（True推奨）
        
        Returns:
            発音に近いハングル文字列（英語・記号はそのまま）
        """
        try:
            # テキストをトークンに分割
            tokens = self.split_mixed_text(text)
            result_tokens = []
            
            for token in tokens:
                if self.is_hangul(token):
                    # ハングルの場合のみg2pkで処理
                    pron = self.g2p(token, descriptive=descriptive)
                    result_tokens.append(pron)
                else:
                    # 英語・記号・空白はそのまま
                    result_tokens.append(token)
            
            # 結果を結合
            result = ''.join(result_tokens)
            
            # 結果をクリーンアップ（余分な空白を整理）
            cleaned = self._clean_result(result)
            
            return cleaned
        except Exception as e:
            print(f"g2pk処理エラー: {e}")
            # エラーの場合は元のテキストを返す
            return text
    
    def _clean_result(self, result: str) -> str:
        """
        g2pkの結果をクリーンアップ
        
        Args:
            result: g2pkの出力結果
        
        Returns:
            クリーンアップされた文字列
        """
        # 余分な空白を整理
        cleaned = re.sub(r'\s+', ' ', result.strip())
        
        # 特殊文字や記号を保持（句読点など）
        # 必要に応じて追加のクリーンアップ処理
        
        return cleaned