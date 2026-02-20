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

        Args:
            text: 韓国語テキスト（英語・記号・数字・カナ混じり可。例外辞書適用後のテキスト）
            descriptive: 実際の発音モード（True推奨）

        Returns:
            発音に近いハングル表記の文字列（非ハングルはそのまま維持）
        """
        try:
            # 全文を1回だけg2pに渡す
            result = self.g2p(text, descriptive=descriptive)
            return self._clean_result(result)
        except Exception as e:
            print(f"g2pk処理エラー: {e}")
            return text
    
    def _clean_result(self, result: str) -> str:
        """
        g2pkの結果をクリーンアップ。
        改行は維持し、行内の連続スペース・タブのみを1つにまとめる。

        Args:
            result: g2pkの出力結果

        Returns:
            クリーンアップされた文字列（改行は維持）
        """
        lines = result.splitlines(keepends=False)
        cleaned_lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in lines]
        return '\n'.join(cleaned_lines)