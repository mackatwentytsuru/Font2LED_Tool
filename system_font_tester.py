#!/usr/bin/env python3
"""
システムフォントテストスクリプト
Windows標準フォントがFont2LED Toolで使用可能かテスト
"""

import os
import freetype
from pathlib import Path

class SystemFontTester:
    def __init__(self):
        self.system_font_paths = [
            # Windows標準フォント
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf", 
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/courier.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/verdana.ttf",
            
            # 日本語フォント
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/meiryob.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/msmincho.ttc",
            "C:/Windows/Fonts/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/YuGothM.ttc",
            "C:/Windows/Fonts/YuMinM.ttc",
        ]
        
        self.working_fonts = []
        self.japanese_fonts = []
        
    def test_font(self, font_path):
        """個別フォントテスト"""
        if not Path(font_path).exists():
            return None
            
        try:
            face = freetype.Face(font_path)
            
            result = {
                'path': font_path,
                'filename': Path(font_path).name,
                'family_name': face.family_name.decode('utf-8') if face.family_name else 'Unknown',
                'style_name': face.style_name.decode('utf-8') if face.style_name else 'Unknown',
                'freetype_compatible': True,
                'japanese_support': False
            }
            
            # 12ピクセルでテスト
            face.set_pixel_sizes(12, 12)
            
            # ASCII文字テスト
            ascii_chars = ['A', 'B', 'C', '1', '2', '3']
            ascii_success = 0
            
            for char in ascii_chars:
                try:
                    face.load_char(char)
                    if face.glyph.bitmap.buffer:
                        ascii_success += 1
                except:
                    pass
            
            # 日本語文字テスト
            japanese_chars = ['あ', 'ア', '日', '本']
            japanese_success = 0
            
            for char in japanese_chars:
                try:
                    face.load_char(char)
                    if face.glyph.bitmap.buffer:
                        japanese_success += 1
                        result['japanese_support'] = True
                except:
                    pass
            
            result['ascii_success'] = ascii_success
            result['japanese_success'] = japanese_success
            
            if ascii_success >= 3:  # 最低限のASCII文字
                self.working_fonts.append(result)
                
                if result['japanese_support']:
                    self.japanese_fonts.append(result)
                
                return result
                
        except Exception as e:
            return {
                'path': font_path,
                'filename': Path(font_path).name,
                'freetype_compatible': False,
                'error': str(e)
            }
        
        return None
    
    def test_all_system_fonts(self):
        """全システムフォントテスト"""
        print("Testing Windows System Fonts for Font2LED Tool compatibility...")
        print("="*80)
        
        for font_path in self.system_font_paths:
            print(f"Testing: {Path(font_path).name}")
            result = self.test_font(font_path)
            
            if result:
                if result.get('freetype_compatible'):
                    japanese_mark = "日本語OK" if result.get('japanese_support') else "ASCII"
                    print(f"  OK - {result['family_name']} ({japanese_mark})")
                else:
                    print(f"  ERROR - {result.get('error', 'Unknown error')}")
            else:
                print(f"  SKIP - File not found or no valid chars")
            print()
    
    def generate_recommended_config(self):
        """推奨フォント設定を生成"""
        print("\n" + "="*80)
        print("RECOMMENDED FONT CONFIGURATION FOR FONT2LED TOOL")
        print("="*80)
        
        if not self.working_fonts:
            print("ERROR: No working system fonts found!")
            return
        
        print(f"Found {len(self.working_fonts)} working fonts")
        print(f"Japanese compatible: {len(self.japanese_fonts)}")
        
        print("\nRecommended font_configs for font2led_gui.py:")
        print("-" * 60)
        print('        self.font_configs = {')
        
        # 最も確実なフォントを優先
        priority_fonts = []
        
        for font in self.working_fonts:
            if 'consola' in font['filename'].lower():
                priority_fonts.insert(0, font)  # Consolas最優先
            elif font['japanese_support']:
                priority_fonts.append(font)  # 日本語対応
            else:
                priority_fonts.append(font)  # その他
        
        for i, font in enumerate(priority_fonts[:10], 1):  # 上位10個
            font_name = f"{font['family_name']} ({font['style_name']})"
            if len(font_name) > 30:
                font_name = font_name[:30] + "..."
            
            print(f'            "{font_name}": {{')
            print(f'                "path": "{font["path"]}",')
            print(f'                "size": (12, 12),')
            description = "Japanese support" if font['japanese_support'] else "ASCII support"
            print(f'                "description": "{description}"')
            print(f'            }},')
        
        print('        }')
        
        # デフォルトフォント推奨
        if priority_fonts:
            best_font = priority_fonts[0]
            font_name = f"{best_font['family_name']} ({best_font['style_name']})"
            if len(font_name) > 30:
                font_name = font_name[:30] + "..."
            
            print(f'\nRecommended default font:')
            print(f'self.current_font = "{font_name}"')
        
        print(f"\nBEST FONTS FOR LED DISPLAY:")
        print("-" * 40)
        
        for font in priority_fonts[:5]:
            features = []
            if 'consola' in font['filename'].lower():
                features.append("Monospace")
            if font['japanese_support']:
                features.append("Japanese")
            features.append(f"ASCII:{font['ascii_success']}/6")
            
            print(f"✓ {font['family_name']}")
            print(f"  Features: {', '.join(features)}")
            print(f"  File: {font['filename']}")

def main():
    """メイン実行関数"""
    tester = SystemFontTester()
    
    # システムフォントテスト
    tester.test_all_system_fonts()
    
    # 推奨設定生成
    tester.generate_recommended_config()
    
    print("\nSystem font testing completed!")

if __name__ == "__main__":
    main()