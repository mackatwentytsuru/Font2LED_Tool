#!/usr/bin/env python3
"""
Font2LED Tool統合計画ツール
検出されたビットマップフォントからLED表示に最適なフォントを選定
"""

import json
import os
from pathlib import Path

class FontIntegrationPlanner:
    def __init__(self, results_file):
        self.results_file = results_file
        self.bitmap_fonts = []
        self.recommendations = []
        
    def load_detection_results(self):
        """検出結果を読み込み"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.bitmap_fonts = data.get('bitmap_fonts', [])
            print(f"Loaded {len(self.bitmap_fonts)} bitmap fonts")
            return True
        except Exception as e:
            print(f"Error loading results: {e}")
            return False
    
    def analyze_font_characteristics(self):
        """フォント特性を分析してLED表示適性を評価"""
        print("\n=== ANALYZING FONT CHARACTERISTICS ===")
        
        # 重複除去
        unique_fonts = {}
        for font in self.bitmap_fonts:
            filename = font['filename']
            if filename not in unique_fonts:
                unique_fonts[filename] = font
        
        print(f"Unique fonts: {len(unique_fonts)}")
        
        # 各フォントの特性を評価
        font_scores = []
        
        for font_data in unique_fonts.values():
            score = self.calculate_led_suitability_score(font_data)
            font_scores.append({
                'font_data': font_data,
                'led_score': score,
                'category': self.categorize_font(font_data)
            })
        
        # スコア順にソート
        font_scores.sort(key=lambda x: x['led_score'], reverse=True)
        
        return font_scores
    
    def calculate_led_suitability_score(self, font_data):
        """LED表示適性スコアを計算"""
        score = 0
        filename = font_data['filename'].lower()
        file_size = font_data['size']
        
        # ファイル名による推定
        if 'bitmap' in filename:
            score += 5.0  # 明確にビットマップと表示
        
        if '12' in filename:
            score += 3.0  # 12ピクセル系（LED表示に適している）
        elif '10' in filename or '16' in filename:
            score += 2.0  # 10/16ピクセル系
        elif '8' in filename:
            score += 1.5  # 8ピクセル系
        
        # 日本語対応の推定
        if any(jp in filename for jp in ['jp', 'japan', 'ms', 'hira', 'min', 'goth']):
            score += 2.0
        
        # ファイルサイズによる評価（適度なサイズが良い）
        if 1_000_000 <= file_size <= 10_000_000:  # 1-10MB
            score += 1.0
        elif file_size < 1_000_000:  # 1MB未満は小さすぎる可能性
            score += 0.5
        
        # フォーマットによる評価
        if font_data.get('format') == 'TrueType':
            score += 1.0
        
        # ビットマップテーブルの数
        bitmap_tables = font_data.get('bitmap_tables', [])
        if len(bitmap_tables) >= 2:
            score += 1.0
        
        return score
    
    def categorize_font(self, font_data):
        """フォントをカテゴリ分類"""
        filename = font_data['filename'].lower()
        
        if 'gn12bitmap' in filename:
            return 'specialized_bitmap'
        elif any(ms in filename for ms in ['msmincho', 'msprgot', 'msgothic']):
            return 'microsoft_standard'
        elif 'hira' in filename:
            return 'hiragino'
        elif any(ds in filename for ds in ['ds', 'fg']):
            return 'design_font'
        elif 'try' in filename:
            return 'truetype_classic'
        else:
            return 'other'
    
    def generate_integration_plan(self, font_scores):
        """Font2LED Tool統合計画を生成"""
        print("\n" + "="*80)
        print("FONT2LED TOOL INTEGRATION PLAN")
        print("="*80)
        
        # カテゴリ別の最適フォント
        categories = {}
        for font_score in font_scores:
            category = font_score['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(font_score)
        
        print("\nCATEGORY-BASED ANALYSIS:")
        print("-"*50)
        
        for category, fonts in categories.items():
            best_font = max(fonts, key=lambda x: x['led_score'])
            print(f"\n{category.upper().replace('_', ' ')}: {len(fonts)} fonts")
            print(f"  Best: {best_font['font_data']['filename']}")
            print(f"  Score: {best_font['led_score']:.2f}")
            print(f"  Size: {best_font['font_data']['size']:,} bytes")
        
        # TOP 5推奨フォント
        print(f"\n" + "="*60)
        print("TOP 5 RECOMMENDED FONTS FOR FONT2LED TOOL")
        print("="*60)
        
        top_5 = font_scores[:5]
        
        for i, font_score in enumerate(top_5, 1):
            font_data = font_score['font_data']
            print(f"\n{i}. {font_data['filename']}")
            print(f"   LED Score: {font_score['led_score']:.2f}/10.0")
            print(f"   Category: {font_score['category'].replace('_', ' ').title()}")
            print(f"   Format: {font_data.get('format', 'Unknown')}")
            print(f"   Size: {font_data['size']:,} bytes")
            print(f"   Tables: {font_data.get('bitmap_tables', [])}")
            print(f"   Path: {font_data['path']}")
            
            # 統合推奨度
            if font_score['led_score'] >= 8.0:
                recommendation = "HIGHLY RECOMMENDED"
            elif font_score['led_score'] >= 6.0:
                recommendation = "RECOMMENDED"
            elif font_score['led_score'] >= 4.0:
                recommendation = "SUITABLE"
            else:
                recommendation = "CONSIDER WITH CAUTION"
            
            print(f"   Recommendation: {recommendation}")
        
        # 具体的な統合手順
        print(f"\n" + "="*60)
        print("INTEGRATION IMPLEMENTATION PLAN")
        print("="*60)
        
        if top_5:
            best_font = top_5[0]['font_data']
            print(f"\nPRIMARY INTEGRATION TARGET:")
            print(f"Font: {best_font['filename']}")
            print(f"Path: {best_font['path']}")
            
            print(f"\nIMPLEMENTATION STEPS:")
            print("1. Copy font file to Font2LED_Tool directory")
            print("2. Add font configuration to font2led_gui.py")
            print("3. Test font rendering with LED matrix")
            print("4. Validate Japanese character support")
            print("5. Update GUI font selection dropdown")
            
            print(f"\nCODE INTEGRATION EXAMPLE:")
            print('```python')
            print('# Add to font_configs in font2led_gui.py')
            print(f'"{best_font["filename"][:-4]} (Bitmap)": {{')
            print(f'    "path": os.path.join(base_dir, "{best_font["filename"]}"),')
            print(f'    "size": (12, 12),  # Adjust based on testing')
            print(f'    "description": "True bitmap font for LED display"')
            print('},')
            print('```')
        
        return top_5
    
    def create_integration_script(self, top_fonts):
        """統合用スクリプト生成"""
        import datetime
        script_content = f'''#!/usr/bin/env python3
"""
Font2LED Tool ビットマップフォント統合スクリプト
自動生成日: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import os
import shutil
from pathlib import Path

# 統合対象フォント（上位5フォント）
INTEGRATION_FONTS = [
'''
        
        for i, font_score in enumerate(top_fonts, 1):
            font_data = font_score['font_data']
            script_content += f'''    {{
        "rank": {i},
        "filename": "{font_data['filename']}",
        "source_path": r"{font_data['path']}",
        "score": {font_score['led_score']:.2f},
        "category": "{font_score['category']}"
    }},
'''
        
        script_content += ''']

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
    
    print("\\nFont integration completed!")
    print("Next steps:")
    print("1. Update font2led_gui.py font_configs")
    print("2. Test font rendering")
    print("3. Validate LED display output")

if __name__ == "__main__":
    integrate_fonts()
'''
        
        script_path = "H:\\Yuki Tsuruoka Dropbox\\鶴岡悠生\\Claude\\0722-windous\\Font2LED_Tool\\integrate_bitmap_fonts.py"
        
        try:
            import datetime
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            print(f"\nIntegration script created: {script_path}")
        except Exception as e:
            print(f"Error creating script: {e}")

def main():
    """メイン実行関数"""
    print("Font2LED Tool Integration Planner")
    print("="*50)
    
    results_file = "H:\\Yuki Tsuruoka Dropbox\\鶴岡悠生\\Claude\\0722-windous\\Font2LED_Tool\\bitmap_font_scan_results.json"
    
    planner = FontIntegrationPlanner(results_file)
    
    if not planner.load_detection_results():
        return
    
    # フォント特性分析
    font_scores = planner.analyze_font_characteristics()
    
    # 統合計画生成
    top_fonts = planner.generate_integration_plan(font_scores)
    
    # 統合スクリプト作成
    planner.create_integration_script(top_fonts)
    
    print("\nIntegration planning completed!")

if __name__ == "__main__":
    main()