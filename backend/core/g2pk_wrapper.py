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
        韓国語テキストをg2pkで処理して発音に近いハングルに変換。
        全文を1回g2pに渡し、文脈を考慮した発音・MeCab呼び出し回数の削減を行う。

        Args:
            text: 韓国語テキスト（英語・記号・数字・カナ混じり可。例外辞書適用後の想定）
            descriptive: 実際の発音モード（True推奨）

        Returns:
            発音に近いハングル文字列（非ハングルはそのまま維持）
        """
        try:
            # 全文を1回だけg2pに渡す（g2pk設計に沿った使い方）
            result = self.g2p(text, descriptive=descriptive)
            return self._clean_result(result)
        except Exception as e:
            print(f"g2pk処理エラー: {e}")
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