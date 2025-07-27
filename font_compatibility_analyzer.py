#!/usr/bin/env python3
"""
フォント互換性分析スクリプト
実際にインストールされているフォントファイルを調査し、
使用可能性を詳細に分析
"""

import os
import struct
from pathlib import Path

class FontCompatibilityAnalyzer:
    def __init__(self):
        self.font2led_dir = Path(__file__).parent
        self.bitmap_fonts_dir = self.font2led_dir / "bitmap_fonts"
        self.results = {
            'existing_files': [],
            'missing_files': [],
            'freetype_compatible': [],
            'freetype_incompatible': [],
            'analysis_details': []
        }
    
    def analyze_font_file(self, font_path):
        """フォントファイルの詳細分析"""
        result = {
            'filename': font_path.name,
            'path': str(font_path),
            'exists': font_path.exists(),
            'size': font_path.stat().st_size if font_path.exists() else 0,
            'format': 'Unknown',
            'is_bitmap': False,
            'has_ebdt_eblc': False,
            'freetype_compatible': False,
            'error_reason': None
        }
        
        if not font_path.exists():
            result['error_reason'] = "File does not exist"
            return result
        
        try:
            # ファイルヘッダー分析
            with open(font_path, 'rb') as f:
                header = f.read(12)
                
                if len(header) < 4:
                    result['error_reason'] = "File too small"
                    return result
                
                # フォーマット判定
                if header[:4] == b'\x00\x01\x00\x00':
                    result['format'] = 'TrueType'
                elif header[:4] == b'OTTO':
                    result['format'] = 'OpenType'
                elif header[:4] == b'true':
                    result['format'] = 'Apple TrueType'
                elif header[:4] == b'ttcf':
                    result['format'] = 'TrueType Collection'
                else:
                    result['format'] = f'Unknown ({header[:4].hex()})'
                
                # TrueType/OpenTypeの場合、テーブル一覧を取得
                if result['format'] in ['TrueType', 'OpenType', 'Apple TrueType']:
                    f.seek(4)
                    num_tables = struct.unpack('>H', f.read(2))[0]
                    f.seek(12)  # テーブルディレクトリへ
                    
                    tables = []
                    for i in range(num_tables):
                        table_tag = f.read(4).decode('ascii', errors='ignore')
                        f.read(12)  # checksum, offset, length をスキップ
                        tables.append(table_tag)
                    
                    result['tables'] = tables
                    
                    # ビットマップテーブルチェック
                    if 'EBDT' in tables and 'EBLC' in tables:
                        result['has_ebdt_eblc'] = True
                        result['is_bitmap'] = True
                elif result['format'] == 'TrueType Collection':
                    # TTCの場合は複雑なので簡易チェック
                    result['is_bitmap'] = 'probably'
            
            # FreeTypeテスト
            try:
                import freetype
                face = freetype.Face(str(font_path))
                result['freetype_compatible'] = True
                result['family_name'] = face.family_name.decode('utf-8') if face.family_name else 'Unknown'
                result['style_name'] = face.style_name.decode('utf-8') if face.style_name else 'Unknown'
            except Exception as ft_error:
                result['freetype_compatible'] = False
                result['error_reason'] = f"FreeType error: {str(ft_error)}"
        
        except Exception as e:
            result['error_reason'] = f"Analysis error: {str(e)}"
        
        return result
    
    def scan_bitmap_fonts_directory(self):
        """bitmap_fontsディレクトリをスキャン"""
        print("Scanning bitmap_fonts directory...")
        print(f"Directory: {self.bitmap_fonts_dir}")
        print(f"Directory exists: {self.bitmap_fonts_dir.exists()}")
        
        if not self.bitmap_fonts_dir.exists():
            print("ERROR: bitmap_fonts directory does not exist!")
            return
        
        # 実際にあるファイルを確認
        actual_files = list(self.bitmap_fonts_dir.iterdir())
        print(f"Found {len(actual_files)} files in bitmap_fonts directory")
        
        for font_file in actual_files:
            if font_file.is_file():
                print(f"Analyzing: {font_file.name}")
                result = self.analyze_font_file(font_file)
                self.results['analysis_details'].append(result)
                
                if result['exists']:
                    self.results['existing_files'].append(result)
                    
                    if result['freetype_compatible']:
                        self.results['freetype_compatible'].append(result)
                    else:
                        self.results['freetype_incompatible'].append(result)
                else:
                    self.results['missing_files'].append(result)
    
    def check_configured_fonts(self):
        """font2led_gui.pyで設定されているフォントをチェック"""
        print("\nChecking configured fonts...")
        
        # 簡易的にbitmap_fonts/で始まるパスを持つフォントを確認
        configured_bitmap_fonts = [
            'gn12bitmap.ttf',
            'MSMINCHO.TTF', 
            'MSPRGOT.TTF',
            'HiraKakuPro-W3.otf',
            'HiraMinPro-W3.otf',
            'mikachanALL.ttc',
            'aqua_pfont.ttf'
        ]
        
        for font_name in configured_bitmap_fonts:
            font_path = self.bitmap_fonts_dir / font_name
            result = self.analyze_font_file(font_path)
            
            if not result['exists']:
                self.results['missing_files'].append(result)
                print(f"MISSING: {font_name}")
            else:
                print(f"FOUND: {font_name} - {result['format']}")
    
    def generate_detailed_report(self):
        """詳細レポート生成"""
        print("\n" + "="*80)
        print("FONT COMPATIBILITY ANALYSIS REPORT")
        print("="*80)
        
        print(f"Total files analyzed: {len(self.results['analysis_details'])}")
        print(f"Existing files: {len(self.results['existing_files'])}")
        print(f"Missing files: {len(self.results['missing_files'])}")
        print(f"FreeType compatible: {len(self.results['freetype_compatible'])}")
        print(f"FreeType incompatible: {len(self.results['freetype_incompatible'])}")
        
        # 動作可能なフォント
        if self.results['freetype_compatible']:
            print(f"\nWORKING FONTS ({len(self.results['freetype_compatible'])}):")
            print("-" * 60)
            for font in self.results['freetype_compatible']:
                bitmap_status = "BITMAP" if font['is_bitmap'] else "VECTOR"
                print(f"OK {font['filename']}")
                print(f"   Format: {font['format']} ({bitmap_status})")
                print(f"   Family: {font.get('family_name', 'Unknown')}")
                print(f"   Size: {font['size']:,} bytes")
                if font['has_ebdt_eblc']:
                    print(f"   Tables: EBDT+EBLC (True Bitmap)")
                print()
        
        # 問題のあるフォント
        if self.results['freetype_incompatible']:
            print(f"\nPROBLEMATIC FONTS ({len(self.results['freetype_incompatible'])}):")
            print("-" * 60)
            for font in self.results['freetype_incompatible']:
                print(f"ERROR {font['filename']}")
                print(f"   Reason: {font.get('error_reason', 'Unknown error')}")
                print(f"   Format: {font['format']}")
                print(f"   Size: {font['size']:,} bytes")
                print()
        
        # 不足ファイル
        if self.results['missing_files']:
            print(f"\nMISSING FILES ({len(self.results['missing_files'])}):")
            print("-" * 60)
            for font in self.results['missing_files']:
                print(f"MISSING {font['filename']}")
                print(f"   Expected path: {font['path']}")
                print()
        
        # 推奨事項
        print("RECOMMENDATIONS:")
        print("-" * 60)
        
        working_count = len(self.results['freetype_compatible'])
        total_count = len(self.results['existing_files'])
        
        if working_count == 0:
            print("ERROR: No working fonts found!")
            print("  - Check if bitmap_fonts directory exists")
            print("  - Verify font files are properly copied")
            print("  - Consider using different font sources")
        elif working_count < total_count // 2:
            print("WARNING: Many fonts are incompatible")
            print("  - Focus on working fonts for production use")
            print("  - Consider removing problematic fonts")
        else:
            print("GOOD: Most fonts are working properly")
            print(f"  - {working_count} working fonts available")
            print("  - Ready for production use")

def main():
    """メイン実行関数"""
    print("Font Compatibility Analyzer")
    print("="*80)
    
    analyzer = FontCompatibilityAnalyzer()
    
    # bitmap_fontsディレクトリスキャン
    analyzer.scan_bitmap_fonts_directory()
    
    # 設定されたフォントチェック
    analyzer.check_configured_fonts()
    
    # 詳細レポート生成
    analyzer.generate_detailed_report()
    
    print("\nAnalysis completed!")

if __name__ == "__main__":
    main()