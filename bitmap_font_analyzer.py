#!/usr/bin/env python3
"""
検出されたビットマップフォントの詳細解析ツール
LED表示に最適なフォントを特定する
"""

import json
import freetype
import numpy as np
from pathlib import Path

class BitmapFontAnalyzer:
    def __init__(self, results_file):
        self.results_file = results_file
        self.bitmap_fonts = []
        self.analysis_results = []
        
        # LED表示適性の評価基準
        self.ideal_sizes = [(12, 10), (16, 16), (8, 12), (12, 12)]  # LED表示に適したサイズ
        
    def load_detection_results(self):
        """検出結果を読み込み"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.bitmap_fonts = data.get('bitmap_fonts', [])
            print(f"Loaded {len(self.bitmap_fonts)} bitmap fonts for analysis")
        except Exception as e:
            print(f"Error loading results: {e}")
            return False
        return True
    
    def test_font_rendering(self, font_path, font_name):
        """フォントのレンダリングテスト"""
        test_results = {
            'font_name': font_name,
            'font_path': font_path,
            'renders_successfully': False,
            'japanese_support': False,
            'led_suitability_score': 0,
            'recommended_size': None,
            'sample_renders': {}
        }
        
        try:
            face = freetype.Face(font_path)
            test_results['renders_successfully'] = True
            
            # 基本情報
            family_name = face.family_name.decode('utf-8') if face.family_name else 'Unknown'
            style_name = face.style_name.decode('utf-8') if face.style_name else 'Unknown'
            test_results['family_name'] = family_name
            test_results['style_name'] = style_name
            
            print(f"\n--- Testing: {font_name} ---")
            print(f"Family: {family_name}")
            print(f"Style: {style_name}")
            
            # 複数のサイズでテスト
            size_scores = []
            
            for test_size in [8, 10, 12, 14, 16, 20]:
                try:
                    face.set_pixel_sizes(test_size, test_size)
                    
                    # ASCII文字テスト
                    ascii_score = self.test_character_set(face, 'ASCII', ['A', 'B', '1', '2'])
                    
                    # 日本語文字テスト
                    japanese_score = self.test_character_set(face, 'Japanese', ['あ', 'か', 'ア', 'カ'])
                    
                    if japanese_score > 0:
                        test_results['japanese_support'] = True
                    
                    # LED適性スコア計算
                    led_score = self.calculate_led_suitability(face, test_size, ascii_score, japanese_score)
                    
                    size_scores.append({
                        'size': test_size,
                        'ascii_score': ascii_score,
                        'japanese_score': japanese_score,
                        'led_score': led_score
                    })
                    
                    print(f"  Size {test_size}px: ASCII={ascii_score:.2f}, Japanese={japanese_score:.2f}, LED={led_score:.2f}")
                    
                except Exception as e:
                    print(f"  Size {test_size}px: Error - {str(e)}")
            
            # 最適サイズ選定
            if size_scores:
                best_size = max(size_scores, key=lambda x: x['led_score'])
                test_results['led_suitability_score'] = best_size['led_score']
                test_results['recommended_size'] = best_size['size']
                test_results['size_scores'] = size_scores
                
                print(f"  Best size: {best_size['size']}px (LED score: {best_size['led_score']:.2f})")
            
        except Exception as e:
            test_results['error'] = str(e)
            print(f"  Error loading font: {str(e)}")
        
        return test_results
    
    def test_character_set(self, face, charset_name, test_chars):
        """文字セットのレンダリングテスト"""
        successful_renders = 0
        total_clarity = 0
        
        for char in test_chars:
            try:
                face.load_char(char)
                bitmap = face.glyph.bitmap
                
                if bitmap.buffer and bitmap.width > 0 and bitmap.rows > 0:
                    # ビットマップデータの解析
                    bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape(bitmap.rows, bitmap.width)
                    
                    # 鮮明度計算（ビットマップフォントらしさ）
                    unique_values = np.unique(bitmap_array)
                    clarity = self.calculate_clarity_score(bitmap_array, unique_values)
                    
                    successful_renders += 1
                    total_clarity += clarity
                    
            except Exception:
                continue
        
        if successful_renders > 0:
            return (successful_renders / len(test_chars)) * (total_clarity / successful_renders)
        return 0
    
    def calculate_clarity_score(self, bitmap_array, unique_values):
        """鮮明度スコア計算（ビットマップフォントの特徴評価）"""
        # ビットマップフォントは値の種類が少ない（0と255が多い）
        if len(unique_values) <= 3:
            # 明確な値の割合
            clear_pixels = np.sum((bitmap_array == 0) | (bitmap_array == 255))
            total_pixels = bitmap_array.size
            clarity_ratio = clear_pixels / total_pixels if total_pixels > 0 else 0
            return clarity_ratio
        else:
            # アンチエイリアスフォントは低スコア
            return 0.3
    
    def calculate_led_suitability(self, face, size, ascii_score, japanese_score):
        """LED表示適性スコア計算"""
        score = 0
        
        # サイズ適性（12x10 LEDに適したサイズ）
        if size in [10, 12]:
            score += 3.0
        elif size in [8, 14, 16]:
            score += 2.0
        else:
            score += 1.0
        
        # 文字レンダリング品質
        score += ascii_score * 2.0
        score += japanese_score * 1.5
        
        # ビットマップ特性ボーナス
        if ascii_score > 0.8:  # 高鮮明度
            score += 1.0
        
        return min(score, 10.0)  # 最大10点
    
    def analyze_all_fonts(self):
        """全ビットマップフォントを解析"""
        if not self.load_detection_results():
            return
        
        print("="*80)
        print("BITMAP FONT DETAILED ANALYSIS FOR LED DISPLAY")
        print("="*80)
        
        # 重複除去（同じファイル名のフォントを除外）
        unique_fonts = {}
        for font in self.bitmap_fonts:
            filename = font['filename']
            if filename not in unique_fonts:
                unique_fonts[filename] = font
        
        print(f"Analyzing {len(unique_fonts)} unique bitmap fonts...")
        
        for font_data in unique_fonts.values():
            font_path = font_data['path']
            font_name = font_data['filename']
            
            # 各フォントをテスト
            result = self.test_font_rendering(font_path, font_name)
            result['original_data'] = font_data
            self.analysis_results.append(result)
        
        # 結果をスコア順にソート
        self.analysis_results.sort(key=lambda x: x.get('led_suitability_score', 0), reverse=True)
    
    def generate_recommendations(self):
        """LED表示用フォント推奨リスト生成"""
        print("\n" + "="*80)
        print("LED DISPLAY FONT RECOMMENDATIONS")
        print("="*80)
        
        # トップ10を表示
        top_fonts = self.analysis_results[:10]
        
        print("TOP 10 FONTS FOR LED DISPLAY:")
        print("-"*80)
        
        for i, font in enumerate(top_fonts, 1):
            print(f"{i:2d}. {font['font_name']}")
            print(f"    Family: {font.get('family_name', 'Unknown')}")
            print(f"    LED Score: {font.get('led_suitability_score', 0):.2f}/10.0")
            print(f"    Recommended Size: {font.get('recommended_size', 'Unknown')}px")
            print(f"    Japanese Support: {'Yes' if font.get('japanese_support', False) else 'No'}")
            print(f"    File Size: {font['original_data']['size']:,} bytes")
            print()
        
        # 日本語対応フォント
        japanese_fonts = [f for f in self.analysis_results if f.get('japanese_support', False)]
        
        if japanese_fonts:
            print(f"\nJAPANESE-COMPATIBLE FONTS ({len(japanese_fonts)}):")
            print("-"*60)
            for font in japanese_fonts[:5]:
                score = font.get('led_suitability_score', 0)
                size = font.get('recommended_size', '?')
                print(f"  {font['font_name']} (Score: {score:.2f}, Size: {size}px)")
        
        # Font2LED Tool統合推奨
        print(f"\nRECOMMENDATION FOR Font2LED TOOL INTEGRATION:")
        print("-"*60)
        
        if top_fonts:
            best_font = top_fonts[0]
            print(f"BEST OVERALL: {best_font['font_name']}")
            print(f"  LED Score: {best_font.get('led_suitability_score', 0):.2f}/10.0")
            print(f"  Path: {best_font['font_path']}")
            print(f"  Recommended for: General LED display use")
        
        if japanese_fonts:
            best_japanese = japanese_fonts[0]
            print(f"\nBEST JAPANESE: {best_japanese['font_name']}")
            print(f"  LED Score: {best_japanese.get('led_suitability_score', 0):.2f}/10.0")
            print(f"  Path: {best_japanese['font_path']}")
            print(f"  Recommended for: Japanese text LED display")
    
    def save_analysis_results(self, output_file):
        """解析結果を保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            print(f"\nAnalysis results saved to: {output_file}")
        except Exception as e:
            print(f"Save error: {e}")

def main():
    """メイン実行関数"""
    print("Bitmap Font Analyzer for LED Display")
    print("="*50)
    
    results_file = "H:\\Yuki Tsuruoka Dropbox\\鶴岡悠生\\Claude\\0722-windous\\Font2LED_Tool\\bitmap_font_scan_results.json"
    
    analyzer = BitmapFontAnalyzer(results_file)
    analyzer.analyze_all_fonts()
    analyzer.generate_recommendations()
    
    # 結果保存
    output_file = "H:\\Yuki Tsuruoka Dropbox\\鶴岡悠生\\Claude\\0722-windous\\Font2LED_Tool\\bitmap_font_analysis.json"
    analyzer.save_analysis_results(output_file)
    
    print("\nAnalysis completed!")

if __name__ == "__main__":
    main()