#!/usr/bin/env python3
"""
高度ビットマップフォント検出ツール（FontTools使用）
ウェブ調査の結果を踏まえた正確な検出方法
"""

import os
import json
import time
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import DefaultTable

class AdvancedBitmapFontDetector:
    def __init__(self, font_directory):
        self.font_directory = Path(font_directory)
        self.results = {
            'true_bitmap_fonts': [],
            'scalable_fonts': [],
            'error_fonts': [],
            'ambiguous_fonts': [],
            'statistics': {}
        }
        
        # サポートするフォント拡張子
        self.supported_extensions = ['.ttf', '.TTF', '.otf', '.OTF', '.ttc', '.TTC']
        
        # ビットマップ関連テーブル（調査結果に基づく）
        self.essential_bitmap_tables = ['EBDT', 'EBLC']  # 必須ペア
        self.additional_bitmap_tables = ['EBSC', 'bloc', 'bdat', 'CBDT', 'CBLC']  # 追加テーブル
    
    def analyze_font_with_fonttools(self, font_path):
        """FontToolsライブラリによる詳細解析"""
        try:
            # TTFontオブジェクトで開く
            font = TTFont(font_path)
            
            # 基本情報取得
            sfnt_version = font.sfntVersion
            
            # フォーマット判定
            if sfnt_version == b'\x00\x01\x00\x00':
                font_format = 'TrueType'
            elif sfnt_version == b'OTTO':
                font_format = 'OpenType CFF'
            elif sfnt_version == b'true':
                font_format = 'Apple TrueType'
            elif sfnt_version == b'ttcf':
                font_format = 'TrueType Collection'
            else:
                font_format = f'Unknown ({sfnt_version.hex()})'
            
            # 全テーブル一覧取得
            all_tables = list(font.keys())
            
            # ビットマップテーブル検出
            essential_bitmap = [t for t in self.essential_bitmap_tables if t in all_tables]
            additional_bitmap = [t for t in self.additional_bitmap_tables if t in all_tables]
            
            # ビットマップ判定ロジック（調査結果に基づく厳格な判定）
            is_true_bitmap = len(essential_bitmap) == 2  # EBDT+EBLC必須
            is_partial_bitmap = len(essential_bitmap) == 1 or len(additional_bitmap) > 0
            
            # ビットマップサイズ情報（可能な場合）
            bitmap_strikes = []
            if 'EBLC' in font:
                try:
                    eblc_table = font['EBLC']
                    # EBLCテーブルからストライク（サイズ）情報を取得
                    if hasattr(eblc_table, 'strikes'):
                        for strike in eblc_table.strikes:
                            strike_info = {
                                'ppemX': getattr(strike, 'ppemX', 'Unknown'),
                                'ppemY': getattr(strike, 'ppemY', 'Unknown'),
                                'startGlyphIndex': getattr(strike, 'startGlyphIndex', 'Unknown'),
                                'endGlyphIndex': getattr(strike, 'endGlyphIndex', 'Unknown')
                            }
                            bitmap_strikes.append(strike_info)
                except Exception as e:
                    bitmap_strikes = [{'error': str(e)}]
            
            # フォント名情報取得
            font_name = 'Unknown'
            if 'name' in font:
                try:
                    name_table = font['name']
                    # フォントファミリー名を取得（ID=1）
                    for record in name_table.names:
                        if record.nameID == 1:  # Font Family Name
                            font_name = str(record)
                            break
                except:
                    pass
            
            font.close()
            
            return {
                'success': True,
                'format': font_format,
                'sfnt_version': sfnt_version.hex(),
                'font_name': font_name,
                'all_tables': all_tables,
                'essential_bitmap_tables': essential_bitmap,
                'additional_bitmap_tables': additional_bitmap,
                'bitmap_strikes': bitmap_strikes,
                'is_true_bitmap': is_true_bitmap,
                'is_partial_bitmap': is_partial_bitmap,
                'table_count': len(all_tables)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def scan_all_fonts_advanced(self):
        """高度な一括スキャン"""
        print("Advanced Bitmap Font Detection Tool (FontTools-based)")
        print("="*80)
        print(f"Scanning directory: {self.font_directory}")
        
        # 全フォントファイルを収集
        all_font_files = []
        for ext in self.supported_extensions:
            pattern = f"*{ext}"
            found_files = list(self.font_directory.glob(pattern))
            all_font_files.extend(found_files)
        
        total_files = len(all_font_files)
        print(f"Found font files: {total_files}")
        
        if total_files == 0:
            print("No font files found")
            return
        
        # 処理開始
        start_time = time.time()
        true_bitmap_count = 0
        partial_bitmap_count = 0
        
        for i, font_file in enumerate(all_font_files, 1):
            # プログレス表示（50個ごと）
            if i % 50 == 0 or i == total_files:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total_files - i) / rate if rate > 0 else 0
                print(f"Progress: {i}/{total_files} ({i/total_files*100:.1f}%) "
                      f"Rate: {rate:.1f}files/sec ETA: {eta:.0f}sec")
            
            file_info = {
                'filename': font_file.name,
                'path': str(font_file),
                'size': font_file.stat().st_size,
                'extension': font_file.suffix.lower()
            }
            
            # FontToolsで解析
            analysis = self.analyze_font_with_fonttools(font_file)
            file_info.update(analysis)
            
            # 結果分類（調査結果に基づく厳格な分類）
            if not analysis['success']:
                self.results['error_fonts'].append(file_info)
            elif analysis['is_true_bitmap']:
                self.results['true_bitmap_fonts'].append(file_info)
                true_bitmap_count += 1
                print(f"TRUE BITMAP FONT FOUND! [{true_bitmap_count}] {font_file.name}")
                print(f"   Format: {analysis.get('format', 'Unknown')}")
                print(f"   Tables: {analysis.get('essential_bitmap_tables', [])}")
                if analysis.get('bitmap_strikes'):
                    print(f"   Strikes: {len(analysis['bitmap_strikes'])}")
                    for j, strike in enumerate(analysis['bitmap_strikes'][:3]):  # 最初の3つのみ表示
                        if 'error' not in strike:
                            print(f"     Strike {j+1}: {strike.get('ppemX', '?')}x{strike.get('ppemY', '?')} ppem")
            elif analysis['is_partial_bitmap']:
                self.results['ambiguous_fonts'].append(file_info)
                partial_bitmap_count += 1
                if partial_bitmap_count <= 10:  # 最初の10個のみ表示
                    print(f"PARTIAL BITMAP: {font_file.name} - {analysis.get('essential_bitmap_tables', [])} + {analysis.get('additional_bitmap_tables', [])}")
            else:
                self.results['scalable_fonts'].append(file_info)
        
        # 統計情報
        self.results['statistics'] = {
            'total_files': total_files,
            'true_bitmap_fonts': len(self.results['true_bitmap_fonts']),
            'partial_bitmap_fonts': len(self.results['ambiguous_fonts']),
            'scalable_fonts': len(self.results['scalable_fonts']),
            'error_fonts': len(self.results['error_fonts']),
            'processing_time': time.time() - start_time
        }
        
        print(f"\nProcessing completed: {self.results['statistics']['processing_time']:.2f}sec")
    
    def generate_detailed_report(self):
        """詳細レポート生成"""
        stats = self.results['statistics']
        
        print("\n" + "="*80)
        print("ADVANCED BITMAP FONT DETECTION RESULTS")
        print("="*80)
        
        print(f"Total files analyzed: {stats['total_files']:,}")
        print(f"TRUE bitmap fonts (EBDT+EBLC): {stats['true_bitmap_fonts']} ({stats['true_bitmap_fonts']/stats['total_files']*100:.2f}%)")
        print(f"PARTIAL bitmap fonts: {stats['partial_bitmap_fonts']} ({stats['partial_bitmap_fonts']/stats['total_files']*100:.2f}%)")
        print(f"Scalable fonts: {stats['scalable_fonts']} ({stats['scalable_fonts']/stats['total_files']*100:.2f}%)")
        print(f"Error files: {stats['error_fonts']} ({stats['error_fonts']/stats['total_files']*100:.2f}%)")
        
        # 真のビットマップフォント詳細
        if self.results['true_bitmap_fonts']:
            print(f"\nTRUE BITMAP FONTS ({len(self.results['true_bitmap_fonts'])}):")
            print("-"*80)
            
            for i, font in enumerate(self.results['true_bitmap_fonts'], 1):
                print(f"{i:3d}. {font['filename']}")
                print(f"     Format: {font.get('format', 'Unknown')}")
                print(f"     Size: {font['size']:,} bytes")
                print(f"     Font name: {font.get('font_name', 'Unknown')}")
                print(f"     Tables: {font.get('essential_bitmap_tables', [])} (+ {len(font.get('additional_bitmap_tables', []))} additional)")
                
                if font.get('bitmap_strikes'):
                    strikes = font['bitmap_strikes']
                    if strikes and 'error' not in strikes[0]:
                        print(f"     Bitmap strikes: {len(strikes)}")
                        for j, strike in enumerate(strikes[:2]):  # 最初の2つ
                            ppem_x = strike.get('ppemX', '?')
                            ppem_y = strike.get('ppemY', '?')
                            if ppem_x != '?' and ppem_y != '?':
                                print(f"       Strike {j+1}: {ppem_x}x{ppem_y} pixels")
                print()
        else:
            print("\nNo TRUE bitmap fonts found")
        
        # 部分的ビットマップフォントのサマリー
        if self.results['ambiguous_fonts']:
            print(f"\nPARTIAL BITMAP FONTS (first 5 of {len(self.results['ambiguous_fonts'])}):")
            print("-"*60)
            for font in self.results['ambiguous_fonts'][:5]:
                tables = font.get('essential_bitmap_tables', []) + font.get('additional_bitmap_tables', [])
                print(f"  {font['filename']}: {tables}")
        
        # エラーファイル（最初の5個のみ）
        if self.results['error_fonts']:
            print(f"\nERROR FILES (first 5 of {len(self.results['error_fonts'])}):")
            print("-"*60)
            for font in self.results['error_fonts'][:5]:
                print(f"  {font['filename']}: {font.get('error', 'Unknown error')}")
    
    def save_detailed_results(self, output_file):
        """詳細結果保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\nDetailed results saved to: {output_file}")
        except Exception as e:
            print(f"Save error: {e}")

def main():
    """メイン実行関数"""
    print("Advanced Bitmap Font Detection Tool v2.0")
    print("Based on web research findings for accurate detection")
    print("="*80)
    
    # フォントディレクトリ設定
    font_directory = r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts"
    
    if not os.path.exists(font_directory):
        print(f"ERROR: Font directory not found: {font_directory}")
        return
    
    # 検出器を初期化
    detector = AdvancedBitmapFontDetector(font_directory)
    
    # 高度スキャン実行
    detector.scan_all_fonts_advanced()
    
    # 詳細レポート生成
    detector.generate_detailed_report()
    
    # 結果保存
    output_file = "H:\\Yuki Tsuruoka Dropbox\\鶴岡悠生\\Claude\\0722-windous\\Font2LED_Tool\\advanced_bitmap_results.json"
    detector.save_detailed_results(output_file)
    
    print("\nAdvanced detection completed!")

if __name__ == "__main__":
    main()