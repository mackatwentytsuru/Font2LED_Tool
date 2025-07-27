#!/usr/bin/env python3
"""
フォント選択機能の実装可能性をテスト
"""

import freetype
import os

def test_font_compatibility():
    """複数のフォントでLED表示テスト"""
    
    # テスト用フォントリスト
    test_fonts = [
        {
            "name": "JF-Dot-k12x10",
            "path": r"C:\Users\macka\Downloads\JF-Dot-k12x10\JF-Dot-k12x10.ttf",
            "pixel_size": (12, 10)
        },
        # 他のピクセルフォントがあれば追加
    ]
    
    # Windowsシステムフォントも試す
    windows_fonts = [
        {
            "name": "MS Gothic",
            "path": r"C:\Windows\Fonts\msgothic.ttc",
            "pixel_size": (10, 10)
        },
        {
            "name": "Arial",
            "path": r"C:\Windows\Fonts\arial.ttf",
            "pixel_size": (10, 10)
        }
    ]
    
    print("=== フォント互換性テスト ===\n")
    
    # ピクセルフォントのテスト
    for font_info in test_fonts:
        if os.path.exists(font_info["path"]):
            try:
                face = freetype.Face(font_info["path"])
                face.set_pixel_sizes(font_info["pixel_size"][0], font_info["pixel_size"][1])
                
                # テスト文字
                test_char = '小'
                face.load_char(test_char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_MONOCHROME)
                bitmap = face.glyph.bitmap
                
                print(f"✓ {font_info['name']}: OK")
                print(f"  サイズ: {bitmap.width}×{bitmap.rows}")
                print(f"  ピクセルサイズ設定: {font_info['pixel_size']}")
                print(f"  モノクロビットマップ: {'対応' if bitmap.pitch else '非対応'}")
                print()
                
            except Exception as e:
                print(f"✗ {font_info['name']}: エラー - {e}\n")
    
    print("\n=== 非ピクセルフォントのテスト ===\n")
    
    # 通常フォントのテスト（LED表示に向かない）
    for font_info in windows_fonts:
        if os.path.exists(font_info["path"]):
            try:
                face = freetype.Face(font_info["path"])
                face.set_pixel_sizes(font_info["pixel_size"][0], font_info["pixel_size"][1])
                
                # アンチエイリアスなしでレンダリング
                test_char = '小'
                face.load_char(test_char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_MONOCHROME)
                bitmap = face.glyph.bitmap
                
                print(f"? {font_info['name']}: 技術的には可能")
                print(f"  サイズ: {bitmap.width}×{bitmap.rows}")
                print(f"  注意: ピクセルフォントではないため、LED表示品質が低下")
                print()
                
            except Exception as e:
                print(f"✗ {font_info['name']}: エラー - {e}\n")
    
    print("\n=== 結論 ===")
    print("1. JF-Dot-k12x10のようなピクセルフォントが最適")
    print("2. 他のフォントも技術的には使用可能だが：")
    print("   - アンチエイリアスを無効化する必要がある")
    print("   - 10×12の小さなサイズでは文字が潰れる可能性")
    print("   - LED表示に最適化されていない")
    print("\n推奨: ピクセルフォントのみを選択肢として提供")

if __name__ == "__main__":
    test_font_compatibility()