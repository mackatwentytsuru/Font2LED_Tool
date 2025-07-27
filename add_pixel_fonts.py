#!/usr/bin/env python3
"""
ピクセルフォント追加ガイド
Font2LED GUIにピクセルフォントを追加する方法
"""

def show_font_add_guide():
    """ピクセルフォント追加方法を表示"""
    
    print("=== Font2LED ピクセルフォント追加ガイド ===\n")
    
    print("【推奨ピクセルフォント】")
    print("1. JF-Dot系列:")
    print("   - JF-Dot-k12x10 (現在使用中)")
    print("   - JF-Dot-Shinonome12")
    print("   - JF-Dot-Shinonome14")
    print("   - JF-Dot-Shinonome16")
    
    print("\n2. 美咲フォント:")
    print("   - misaki_gothic.ttf")
    print("   - misaki_mincho.ttf")
    
    print("\n3. PixelMplus:")
    print("   - PixelMplus10-Regular.ttf")
    print("   - PixelMplus12-Regular.ttf")
    
    print("\n【フォント追加方法】")
    print("font2led_gui.py の font_configs に以下の形式で追加:")
    print("""
self.font_configs = {
    "JF-Dot-k12x10 (推奨)": {
        "path": r"C:\\path\\to\\JF-Dot-k12x10.ttf",
        "size": (12, 10),
        "description": "日本語対応12x10ピクセルフォント"
    },
    "美咲ゴシック": {
        "path": r"C:\\path\\to\\misaki_gothic.ttf",
        "size": (8, 8),
        "description": "8x8ピクセル日本語フォント"
    },
    # 新しいフォントをここに追加
}
    """)
    
    print("\n【注意事項】")
    print("- ピクセルフォント（ビットマップフォント）のみ使用してください")
    print("- 通常のフォントは10×12サイズでは文字が潰れます")
    print("- size: (幅, 高さ) はフォントの推奨ピクセルサイズです")
    print("- LED表示に最適化されたフォントを選びましょう")
    
    print("\n【ダウンロード先】")
    print("- JFドットフォント: http://jikasei.me/font/jf-dotfont/")
    print("- 美咲フォント: https://littlelimit.net/misaki.htm")
    print("- PixelMplus: http://itouhiro.hatenablog.com/entry/20130602/font")

if __name__ == "__main__":
    show_font_add_guide()