#!/usr/bin/env python3
"""
Font2LED Tool ビットマップフォント統合スクリプト
自動生成日: 2025-07-27 14:04:14
"""

import os
import shutil
from pathlib import Path

# 統合対象フォント（上位5フォント）
INTEGRATION_FONTS = [
    {
        "rank": 1,
        "filename": "gn12bitmap.ttf",
        "source_path": r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts\gn12bitmap.ttf",
        "score": 11.00,
        "category": "specialized_bitmap"
    },
    {
        "rank": 2,
        "filename": "HiraKakuStd-W8.otf",
        "source_path": r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts\HiraKakuStd-W8.otf",
        "score": 5.50,
        "category": "hiragino"
    },
    {
        "rank": 3,
        "filename": "MSMINCHO.TTF",
        "source_path": r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts\MSMINCHO.TTF",
        "score": 5.00,
        "category": "microsoft_standard"
    },
    {
        "rank": 4,
        "filename": "MSPRGOT.TTF",
        "source_path": r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts\MSPRGOT.TTF",
        "score": 5.00,
        "category": "microsoft_standard"
    },
    {
        "rank": 5,
        "filename": "HiraKakuPro-W3.otf",
        "source_path": r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts\HiraKakuPro-W3.otf",
        "score": 4.00,
        "category": "hiragino"
    },
]

def integrate_fonts():
    """フォントをFont2LED Toolに統合"""
    print("Integrating bitmap fonts into Font2LED Tool...")
    
    base_dir = Path(__file__).parent
    
    for font_info in INTEGRATION_FONTS:
        source_path = font_info["source_path"]
        filename = font_info["filename"]
        target_path = base_dir / filename
        
        print(f"Copying {filename}...")
        
        try:
            if Path(source_path).exists():
                shutil.copy2(source_path, target_path)
                print(f"  ✅ Success: {filename}")
            else:
                print(f"  ❌ Source not found: {source_path}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\nFont integration completed!")
    print("Next steps:")
    print("1. Update font2led_gui.py font_configs")
    print("2. Test font rendering")
    print("3. Validate LED display output")

if __name__ == "__main__":
    integrate_fonts()
