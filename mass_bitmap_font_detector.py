#!/usr/bin/env python3
"""
大量フォント一括ビットマップ検出ツール
フォルダ内の全フォントファイルをスキャンしてビットマップフォントを特定する
"""

import os
import struct
import time
from pathlib import Path
import json

class MassBitmapFontDetector:
    def __init__(self, font_directory):
        self.font_directory = Path(font_directory)
        self.results = {
            'bitmap_fonts': [],
            'scalable_fonts': [],
            'error_fonts': [],
            'unsupported_fonts': [],
            'statistics': {}
        }
        
        # サポートするフォント拡張子
        self.supported_extensions = ['.ttf', '.TTF', '.otf', '.OTF', '.ttc', '.TTC']
        
        # ビットマップ関連テーブル
        self.bitmap_tables = ['EBDT', 'EBLC', 'bloc', 'bdat', 'CBDT', 'CBLC']
    
    def analyze_ttf_font(self, font_path):
        """TTF/OTFフォントのビットマップテーブル解析"""
        try:
            with open(font_path, 'rb') as f:
                # ファイルヘッダー読み取り
                header = f.read(12)
                if len(header) < 12:
                    return {'error': 'File too small'}
                
                # スケーラータイプ確認
                scaler_type = header[:4]
                format_type = 'Unknown'
                
                if scaler_type == b'\x00\x01\x00\x00':
                    format_type = 'TrueType'
                elif scaler_type == b'OTTO':
                    format_type = 'OpenType CFF'
                elif scaler_type == b'true':
                    format_type = 'Apple TrueType'
                
                # テーブル数取得
                num_tables = struct.unpack('>H', header[4:6])[0]
                
                # テーブル一覧読み取り
                tables = []
                for i in range(num_tables):
                    table_record = f.read(16)
                    if len(table_record) < 16:
                        break
                    tag = table_record[:4].decode('ascii', errors='ignore')
                    tables.append(tag)
                
                # ビットマップテーブル検出
                found_bitmap_tables = [t for t in self.bitmap_tables if t in tables]
                
                return {
                    'format': format_type,
                    'tables': len(tables),
                    'all_tables': tables,
                    'bitmap_tables': found_bitmap_tables,
                    'is_bitmap': len(found_bitmap_tables) > 0
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_ttc_font(self, font_path):
        """TTCコレクションの解析"""
        try:
            with open(font_path, 'rb') as f:
                # TTCヘッダー
                header = f.read(12)
                if len(header) < 12:
                    return {'error': 'File too small'}
                
                ttc_tag = header[:4]
                if ttc_tag != b'ttcf':
                    return {'error': 'Not a TTC file'}
                
                version = struct.unpack('>I', header[4:8])[0]
                num_fonts = struct.unpack('>I', header[8:12])[0]
                
                # 各フォントのオフセット読み取り
                offsets = []
                for i in range(num_fonts):
                    offset_data = f.read(4)
                    if len(offset_data) == 4:
                        offset = struct.unpack('>I', offset_data)[0]
                        offsets.append(offset)
                
                # 最初のフォントを解析（代表として）
                bitmap_found = False
                all_bitmap_tables = []
                
                for font_index, offset in enumerate(offsets):
                    try:
                        f.seek(offset)
                        font_header = f.read(12)
                        if len(font_header) >= 12:
                            num_tables = struct.unpack('>H', font_header[4:6])[0]
                            
                            tables = []
                            for i in range(num_tables):
                                table_record = f.read(16)
                                if len(table_record) < 16:
                                    break
                                tag = table_record[:4].decode('ascii', errors='ignore')
                                tables.append(tag)
                            
                            found_bitmap = [t for t in self.bitmap_tables if t in tables]
                            if found_bitmap:
                                bitmap_found = True
                                all_bitmap_tables.extend(found_bitmap)
                    except:
                        continue
                
                return {
                    'format': f'TTC Collection ({num_fonts} fonts)',
                    'num_fonts': num_fonts,
                    'bitmap_tables': list(set(all_bitmap_tables)),
                    'is_bitmap': bitmap_found
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def scan_all_fonts(self):
        """フォントディレクトリ全体をスキャン"""
        print(f"Scanning font directory: {self.font_directory}")
        print("="*70)
        
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
        
        # プログレス表示用
        start_time = time.time()
        bitmap_count = 0
        
        for i, font_file in enumerate(all_font_files, 1):
            # プログレス表示（100個ごと）
            if i % 100 == 0 or i == total_files:
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
            
            try:
                # 拡張子に応じて解析方法を選択
                if file_info['extension'] in ['.ttc', '.TTC']:
                    analysis = self.analyze_ttc_font(font_file)
                else:
                    analysis = self.analyze_ttf_font(font_file)
                
                file_info.update(analysis)
                
                # 結果を分類
                if 'error' in analysis:
                    self.results['error_fonts'].append(file_info)
                elif analysis.get('is_bitmap', False):
                    self.results['bitmap_fonts'].append(file_info)
                    bitmap_count += 1
                    # ビットマップフォント発見を即座に表示
                    print(f"BITMAP FONT FOUND! [{bitmap_count}] {font_file.name}")
                    if analysis.get('bitmap_tables'):
                        print(f"   Tables: {analysis['bitmap_tables']}")
                else:
                    self.results['scalable_fonts'].append(file_info)
                    
            except Exception as e:
                file_info['error'] = str(e)
                self.results['error_fonts'].append(file_info)
        
        # 統計情報
        self.results['statistics'] = {
            'total_files': total_files,
            'bitmap_fonts': len(self.results['bitmap_fonts']),
            'scalable_fonts': len(self.results['scalable_fonts']),
            'error_fonts': len(self.results['error_fonts']),
            'processing_time': time.time() - start_time
        }
        
        print(f"\nProcessing completed: {self.results['statistics']['processing_time']:.2f}sec")
    
    def generate_report(self):
        """結果レポートを生成"""
        stats = self.results['statistics']
        
        print("\n" + "="*70)
        print("BITMAP FONT DETECTION RESULTS")
        print("="*70)
        
        print(f"Total files: {stats['total_files']:,}")
        print(f"Bitmap fonts: {stats['bitmap_fonts']} ({stats['bitmap_fonts']/stats['total_files']*100:.2f}%)")
        print(f"Scalable fonts: {stats['scalable_fonts']} ({stats['scalable_fonts']/stats['total_files']*100:.2f}%)")
        print(f"Error files: {stats['error_fonts']} ({stats['error_fonts']/stats['total_files']*100:.2f}%)")
        
        # ビットマップフォント詳細
        if self.results['bitmap_fonts']:
            print(f"\nDISCOVERED BITMAP FONTS ({len(self.results['bitmap_fonts'])}):")
            print("-"*70)
            
            for i, font in enumerate(self.results['bitmap_fonts'], 1):
                print(f"{i:2d}. {font['filename']}")
                print(f"    Format: {font.get('format', 'Unknown')}")
                print(f"    Size: {font['size']:,} bytes")
                if font.get('bitmap_tables'):
                    print(f"    Bitmap tables: {font['bitmap_tables']}")
                if font.get('num_fonts'):
                    print(f"    Collection: {font['num_fonts']} fonts")
                print()
        else:
            print("\nNo bitmap fonts found")
        
        # エラーファイル（一部のみ表示）
        if self.results['error_fonts']:
            print(f"\nERROR FILES (first 10):")
            print("-"*50)
            for font in self.results['error_fonts'][:10]:
                print(f"   {font['filename']}: {font.get('error', 'Unknown error')}")
            
            if len(self.results['error_fonts']) > 10:
                print(f"   ... and {len(self.results['error_fonts']) - 10} more")
    
    def save_results(self, output_file):
        """結果をJSONファイルに保存"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_file}")
        except Exception as e:
            print(f"Save error: {e}")

def main():
    """メイン実行関数"""
    print("Mass Bitmap Font Detection Tool")
    print("="*70)
    
    # フォントディレクトリ設定
    font_directory = r"C:\Users\macka\Downloads\新しいフォルダー\Japanese_Font_Collection\Fonts"
    
    if not os.path.exists(font_directory):
        print(f"ERROR: Font directory not found: {font_directory}")
        return
    
    # 検出器を初期化して実行
    detector = MassBitmapFontDetector(font_directory)
    
    # 全フォントをスキャン
    detector.scan_all_fonts()
    
    # レポート生成
    detector.generate_report()
    
    # 結果をJSONファイルに保存
    output_file = "H:\\Yuki Tsuruoka Dropbox\\鶴岡悠生\\Claude\\0722-windous\\Font2LED_Tool\\bitmap_font_scan_results.json"
    detector.save_results(output_file)
    
    print("\nDetection completed!")

if __name__ == "__main__":
    main()