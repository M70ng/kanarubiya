# core/lrc_processor.py
import re
from typing import List, Tuple, Dict
from .korean_to_kana import KoreanToKanaConverter

class LrcProcessor:
    def __init__(self):
        """LRCファイル処理器の初期化"""
        self.converter = KoreanToKanaConverter()
    
    def parse_lrc_line(self, line: str) -> Tuple[str, str]:
        """
        LRC行を解析してタイムスタンプと歌詞を分離
        
        Args:
            line: LRC行（例: "[00:00.00]歌詞"）
        
        Returns:
            (タイムスタンプ, 歌詞) のタプル
        """
        # タイムスタンプのパターン: [mm:ss.xx] または [mm:ss:xx]
        timestamp_pattern = r'\[(\d{2}):(\d{2})[.:](\d{2})\]'
        match = re.match(timestamp_pattern, line)
        
        if match:
            minutes, seconds, centiseconds = match.groups()
            timestamp = f"[{minutes}:{seconds}.{centiseconds}]"
            lyrics = line[match.end():].strip()
            return timestamp, lyrics
        else:
            # タイムスタンプがない場合は空文字列として扱う
            return "", line.strip()
    
    def is_metadata_line(self, line: str) -> bool:
        """
        メタデータ行かどうかを判定
        
        Args:
            line: チェックする行
        
        Returns:
            メタデータ行の場合True
        """
        # メタデータのパターン: [ti:タイトル], [ar:アーティスト], [al:アルバム] など
        metadata_patterns = [
            r'^\[ti:',  # タイトル
            r'^\[ar:',  # アーティスト
            r'^\[al:',  # アルバム
            r'^\[by:',  # 作成者
            r'^\[offset:',  # オフセット
            r'^\[length:',  # 長さ
        ]
        
        return any(re.match(pattern, line) for pattern in metadata_patterns)
    
    def process_lrc_content(self, content: str, use_g2pk: bool = True) -> str:
        """
        LRCファイルの内容を処理して韓国語歌詞をカナに変換
        
        Args:
            content: LRCファイルの内容
            use_g2pk: g2pkを使用するかどうか
        
        Returns:
            変換されたLRC内容
        """
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # 空行はそのまま保持
                processed_lines.append(line)
                continue
            
            if self.is_metadata_line(line):
                # メタデータ行はそのまま保持
                processed_lines.append(line)
                continue
            
            # タイムスタンプと歌詞を分離
            timestamp, lyrics = self.parse_lrc_line(line)
            
            if timestamp and lyrics:
                # 歌詞部分を変換
                converted_lyrics = self.converter.convert(lyrics, use_g2pk)
                processed_line = f"{timestamp}{converted_lyrics}"
            elif lyrics:
                # タイムスタンプがない歌詞行
                converted_lyrics = self.converter.convert(lyrics, use_g2pk)
                processed_line = converted_lyrics
            else:
                # タイムスタンプのみの行はそのまま保持
                processed_line = line
            
            processed_lines.append(processed_line)
        
        return '\n'.join(processed_lines)
    
    def process_lrc_with_details(self, content: str, use_g2pk: bool = True) -> Dict:
        """
        LRC内容を詳細情報付きで処理
        
        Args:
            content: LRCファイルの内容
            use_g2pk: g2pkを使用するかどうか
        
        Returns:
            詳細な処理結果
        """
        lines = content.split('\n')
        processed_lines = []
        line_details = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            line_info = {
                'line_number': i + 1,
                'original': line,
                'processed': line,
                'type': 'empty' if not line else 'metadata' if self.is_metadata_line(line) else 'lyrics',
                'timestamp': '',
                'original_lyrics': '',
                'converted_lyrics': '',
                'error': None
            }
            
            if not line:
                # 空行
                processed_lines.append(line)
            elif self.is_metadata_line(line):
                # メタデータ行
                processed_lines.append(line)
            else:
                # 歌詞行
                try:
                    timestamp, lyrics = self.parse_lrc_line(line)
                    line_info['timestamp'] = timestamp
                    line_info['original_lyrics'] = lyrics
                    
                    if lyrics:
                        # 歌詞部分を変換
                        converted_lyrics = self.converter.convert(lyrics, use_g2pk)
                        line_info['converted_lyrics'] = converted_lyrics
                        
                        if timestamp:
                            processed_line = f"{timestamp}{converted_lyrics}"
                        else:
                            processed_line = converted_lyrics
                    else:
                        # タイムスタンプのみの行
                        processed_line = line
                    
                    line_info['processed'] = processed_line
                    processed_lines.append(processed_line)
                    
                except Exception as e:
                    line_info['error'] = str(e)
                    processed_lines.append(line)  # エラーの場合は元の行を保持
            
            line_details.append(line_info)
        
        return {
            'original_content': content,
            'processed_content': '\n'.join(processed_lines),
            'line_details': line_details,
            'use_g2pk': use_g2pk,
            'total_lines': len(lines),
            'lyrics_lines': len([l for l in line_details if l['type'] == 'lyrics']),
            'metadata_lines': len([l for l in line_details if l['type'] == 'metadata'])
        } 