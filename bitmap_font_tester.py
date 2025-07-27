#!/usr/bin/env python3
"""
Font2LED Tool ビットマップフォント包括テストスクリプト
統合された全フォントが実際に使用可能かを徹底検証
"""

import os
import sys
import json
import freetype
import traceback
from pathlib import Path

class BitmapFontTester:
    def __init__(self):
        self.font2led_dir = Path(__file__).parent
        self.bitmap_fonts_dir = self.font2led_dir / "bitmap_fonts"
        self.test_results = {
            'working_fonts': [],
            'broken_fonts': [],
            'freetype_compatible': [],
            'freetype_incompatible': [],
            'japanese_support': [],
            'no_japanese_support': [],
            'test_summary': {}
        }
        
        # テスト用文字セット
        self.test_chars = {
            'ascii': ['A', 'B', 'C', '1', '2', '3'],
            'hiragana': ['あ', 'い', 'う', 'か', 'き', 'く'],
            'katakana': ['ア', 'イ', 'ウ', 'カ', 'キ', 'ク'],
            'kanji': ['日', '本', '語', '文', '字', '漢']
        }
        
    def load_font_configs(self):
        """font2led_gui.pyからフォント設定を取得"""
        gui_file = self.font2led_dir / "font2led_gui.py"
        
        # フォント設定を含む辞書を作成
        font_configs = {}
        
        try:
            with open(gui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # font_configsセクションを抽出
            start_marker = "self.font_configs = {"
            end_marker = "        }"
            
            start_idx = content.find(start_marker)
            if start_idx == -1:
                print("ERROR: font_configs section not found")
                return {}
            
            # font_configsの内容を解析
            lines = content[start_idx:].split('\n')
            current_font = None
            
            for line in lines:
                if '": {' in line and '"path":' not in line:
                    # フォント名を抽出
                    font_name = line.split('"')[1]
                    current_font = font_name
                    font_configs[font_name] = {}
                elif '"path":' in line and current_font:
                    # パスを抽出
                    path_part = line.split('"')[3]
                    if 'bitmap_fonts/' in path_part:
                        filename = path_part.split('bitmap_fonts/')[1]
                        full_path = self.bitmap_fonts_dir / filename
                        font_configs[current_font]['path'] = str(full_path)
                    else:
                        font_configs[current_font]['path'] = path_part
                elif '"size":' in line and current_font:
                    # サイズを抽出
                    size_str = line.split('(')[1].split(')')[0]
                    size_values = [int(x.strip()) for x in size_str.split(',')]
                    font_configs[current_font]['size'] = tuple(size_values)
                elif current_font and '        }' in line:
                    current_font = None
            
            print(f"Loaded {len(font_configs)} font configurations")
            return font_configs
            
        except Exception as e:
            print(f"ERROR loading font configs: {e}")
            return {}
    
    def test_freetype_compatibility(self, font_path, font_name):
        """FreeTypeでフォントが読み込めるかテスト"""
        test_result = {
            'font_name': font_name,
            'font_path': font_path,
            'freetype_compatible': False,
            'renderable_chars': {},
            'japanese_support': False,
            'error_message': None
        }
        
        try:
            # FreeTypeでフォントを開く
            face = freetype.Face(font_path)
            test_result['freetype_compatible'] = True
            
            # フォント情報取得
            family_name = face.family_name.decode('utf-8') if face.family_name else 'Unknown'
            style_name = face.style_name.decode('utf-8') if face.style_name else 'Unknown'
            
            test_result['family_name'] = family_name
            test_result['style_name'] = style_name
            
            print(f"Testing: {font_name}")
            print(f"  Family: {family_name}, Style: {style_name}")
            
            # 文字セットテスト
            face.set_pixel_sizes(12, 12)  # 標準サイズ
            
            for char_type, chars in self.test_chars.items():
                successful_chars = []
                
                for char in chars:
                    try:
                        face.load_char(char)
                        bitmap = face.glyph.bitmap
                        
                        if bitmap.buffer and bitmap.width > 0 and bitmap.rows > 0:
                            successful_chars.append(char)
                            
                            # 日本語文字が1つでもレンダリングできれば日本語対応と判定
                            if char_type in ['hiragana', 'katakana', 'kanji']:
                                test_result['japanese_support'] = True
                                
                    except Exception as char_error:
                        continue
                
                test_result['renderable_chars'][char_type] = successful_chars
                print(f"    {char_type}: {len(successful_chars)}/{len(chars)} chars")
            
            # 判定
            ascii_success = len(test_result['renderable_chars'].get('ascii', [])) >= 3
            if ascii_success:
                self.test_results['working_fonts'].append(test_result)
                self.test_results['freetype_compatible'].append(font_name)
                
                if test_result['japanese_support']:
                    self.test_results['japanese_support'].append(font_name)
                else:
                    self.test_results['no_japanese_support'].append(font_name)
            else:
                test_result['error_message'] = "Insufficient ASCII character support"
                self.test_results['broken_fonts'].append(test_result)
                
        except Exception as e:
            test_result['error_message'] = str(e)
            test_result['freetype_compatible'] = False
            self.test_results['broken_fonts'].append(test_result)
            self.test_results['freetype_incompatible'].append(font_name)
            print(f"  ERROR: {str(e)}")
        
        return test_result
    
    def test_font2led_integration(self, font_configs):
        """Font2LED Tool統合テスト"""
        print("\n" + "="*80)
        print("FONT2LED TOOL INTEGRATION TEST")
        print("="*80)
        
        working_count = 0
        broken_count = 0
        
        for font_name, config in font_configs.items():
            font_path = config.get('path')
            
            if not font_path or not Path(font_path).exists():
                print(f"SKIP: {font_name} - File not found: {font_path}")
                continue
            
            # FreeType互換性テスト
            result = self.test_freetype_compatibility(font_path, font_name)
            
            if result['freetype_compatible']:
                working_count += 1
            else:
                broken_count += 1
            
            print()  # 空行
        
        self.test_results['test_summary'] = {
            'total_fonts': len(font_configs),
            'working_fonts': working_count,
            'broken_fonts': broken_count,
            'success_rate': (working_count / len(font_configs)) * 100 if font_configs else 0,
            'japanese_compatible': len(self.test_results['japanese_support']),
            'freetype_compatible': len(self.test_results['freetype_compatible'])
        }
    
    def generate_detailed_report(self):
        """詳細テストレポート生成"""
        summary = self.test_results['test_summary']
        
        print("\n" + "="*80)
        print("BITMAP FONT TEST RESULTS SUMMARY")
        print("="*80)
        
        print(f"Total fonts tested: {summary['total_fonts']}")
        print(f"Working fonts: {summary['working_fonts']} ({summary['success_rate']:.1f}%)")
        print(f"Broken fonts: {summary['broken_fonts']}")
        print(f"Japanese compatible: {summary['japanese_compatible']}")
        print(f"FreeType compatible: {summary['freetype_compatible']}")
        
        # 動作するフォント一覧
        if self.test_results['working_fonts']:
            print(f"\nWORKING FONTS ({len(self.test_results['working_fonts'])}):")
            print("-" * 60)
            
            for i, font in enumerate(self.test_results['working_fonts'][:10], 1):
                japanese_mark = "日本語✓" if font['japanese_support'] else "ASCII"
                print(f"{i:2d}. {font['font_name']}")
                print(f"    Support: {japanese_mark}")
                print(f"    Family: {font.get('family_name', 'Unknown')}")
        
        # 日本語対応フォント
        if self.test_results['japanese_support']:
            print(f"\nJAPANESE-COMPATIBLE FONTS ({len(self.test_results['japanese_support'])}):")
            print("-" * 60)
            for font_name in self.test_results['japanese_support'][:5]:
                print(f"  ✓ {font_name}")
            if len(self.test_results['japanese_support']) > 5:
                print(f"  ... and {len(self.test_results['japanese_support']) - 5} more")
        
        # 問題のあるフォント
        if self.test_results['broken_fonts']:
            print(f"\nBROKEN/PROBLEMATIC FONTS ({len(self.test_results['broken_fonts'])}):")
            print("-" * 60)
            for font in self.test_results['broken_fonts'][:5]:
                print(f"  ✗ {font['font_name']}")
                print(f"    Error: {font.get('error_message', 'Unknown error')}")
            if len(self.test_results['broken_fonts']) > 5:
                print(f"  ... and {len(self.test_results['broken_fonts']) - 5} more")
        
        # 推奨事項
        print(f"\nRECOMMENDATIONS:")
        print("-" * 60)
        
        if summary['success_rate'] >= 90:
            print("✓ Excellent: Most fonts are working properly")
        elif summary['success_rate'] >= 70:
            print("⚠ Good: Most fonts work, some issues detected")
        else:
            print("✗ Warning: Many fonts have compatibility issues")
        
        if summary['japanese_compatible'] >= 5:
            print("✓ Good: Multiple Japanese-compatible fonts available")
        else:
            print("⚠ Limited: Few Japanese-compatible fonts found")
        
        # 最適なフォント推奨
        best_fonts = []
        for font in self.test_results['working_fonts']:
            if font['japanese_support']:
                score = 0
                # ASCII文字数
                score += len(font['renderable_chars'].get('ascii', [])) * 2
                # 日本語文字数
                score += len(font['renderable_chars'].get('hiragana', [])) * 3
                score += len(font['renderable_chars'].get('katakana', [])) * 3
                score += len(font['renderable_chars'].get('kanji', [])) * 4
                
                font['score'] = score
                best_fonts.append(font)
        
        best_fonts.sort(key=lambda x: x['score'], reverse=True)
        
        if best_fonts:
            print(f"\nTOP RECOMMENDED FONTS FOR LED DISPLAY:")
            print("-" * 60)
            for i, font in enumerate(best_fonts[:3], 1):
                print(f"{i}. {font['font_name']} (Score: {font['score']})")
    
    def save_test_results(self):
        """テスト結果を保存"""
        report_file = self.font2led_dir / "bitmap_font_test_results.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\nTest results saved to: {report_file}")
        except Exception as e:
            print(f"ERROR saving test results: {e}")

def main():
    """メイン実行関数"""
    print("Font2LED Tool Bitmap Font Compatibility Tester")
    print("="*80)
    
    tester = BitmapFontTester()
    
    # フォント設定読み込み
    font_configs = tester.load_font_configs()
    
    if not font_configs:
        print("ERROR: No font configurations found")
        return
    
    # 統合テスト実行
    tester.test_font2led_integration(font_configs)
    
    # 詳細レポート生成
    tester.generate_detailed_report()
    
    # 結果保存
    tester.save_test_results()
    
    print("\nTesting completed!")

if __name__ == "__main__":
    main()