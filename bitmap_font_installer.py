#!/usr/bin/env python3
"""
Font2LED Tool ビットマップフォント一括インストールスクリプト
116個の真のビットマップフォントをFont2LED Toolに統合
"""

import os
import shutil
import json
from pathlib import Path

class BitmapFontInstaller:
    def __init__(self):
        self.font2led_dir = Path(__file__).parent
        self.bitmap_fonts_dir = self.font2led_dir / "bitmap_fonts"
        self.results_file = self.font2led_dir / "bitmap_font_scan_results.json"
        self.font_configs = {}
        self.installed_fonts = []
        self.failed_fonts = []
        
    def create_bitmap_fonts_directory(self):
        """ビットマップフォント専用ディレクトリを作成"""
        if not self.bitmap_fonts_dir.exists():
            self.bitmap_fonts_dir.mkdir()
            print(f"Created bitmap fonts directory: {self.bitmap_fonts_dir}")
        else:
            print(f"Bitmap fonts directory already exists: {self.bitmap_fonts_dir}")
    
    def load_bitmap_font_list(self):
        """検出されたビットマップフォントリストを読み込み"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bitmap_fonts = data.get('bitmap_fonts', [])
            
            print(f"Loaded {len(bitmap_fonts)} bitmap fonts from scan results")
            return bitmap_fonts
        except Exception as e:
            print(f"Error loading bitmap font list: {e}")
            return []
    
    def copy_font_files(self, bitmap_fonts):
        """フォントファイルをコピー"""
        print(f"\nStarting font file copy process...")
        
        for i, font_data in enumerate(bitmap_fonts, 1):
            source_path = Path(font_data['path'])
            filename = font_data['filename']
            target_path = self.bitmap_fonts_dir / filename
            
            if i % 10 == 0:
                print(f"Progress: {i}/{len(bitmap_fonts)} fonts processed")
            
            try:
                if source_path.exists():
                    # ファイルが既に存在する場合はスキップ
                    if target_path.exists():
                        print(f"SKIP Skipped (already exists): {filename}")
                        self.installed_fonts.append({
                            'filename': filename,
                            'status': 'already_exists',
                            'size': font_data['size']
                        })
                    else:
                        shutil.copy2(source_path, target_path)
                        print(f"OK Copied: {filename} ({font_data['size']:,} bytes)")
                        self.installed_fonts.append({
                            'filename': filename,
                            'status': 'copied',
                            'size': font_data['size']
                        })
                else:
                    print(f"ERROR Source not found: {source_path}")
                    self.failed_fonts.append({
                        'filename': filename,
                        'error': 'source_not_found',
                        'source_path': str(source_path)
                    })
            except Exception as e:
                print(f"ERROR Copy failed for {filename}: {e}")
                self.failed_fonts.append({
                    'filename': filename,
                    'error': str(e),
                    'source_path': str(source_path)
                })
    
    def generate_font_configs(self):
        """font2led_gui.py用のフォント設定を生成"""
        print(f"\nGEN Generating font configurations...")
        
        # 基本設定
        base_configs = {
            # 最優先フォント（LED表示に最適化されたもの）
            "gn12bitmap (Bitmap★)": {
                "path": "bitmap_fonts/gn12bitmap.ttf",
                "size": (12, 12),
                "description": "True bitmap font optimized for LED display"
            },
            
            # Microsoft標準フォント
            "MS明朝 (Bitmap)": {
                "path": "bitmap_fonts/MSMINCHO.TTF", 
                "size": (12, 12),
                "description": "Microsoft Mincho bitmap font"
            },
            "MSPゴシック (Bitmap)": {
                "path": "bitmap_fonts/MSPRGOT.TTF",
                "size": (12, 12), 
                "description": "Microsoft Gothic bitmap font"
            },
            
            # システムフォント
            "ヒラギノ角ゴ Pro (Bitmap)": {
                "path": "bitmap_fonts/HiraKakuPro-W3.otf",
                "size": (12, 12),
                "description": "Hiragino Kaku Gothic Pro bitmap"
            },
            "ヒラギノ明朝 Pro (Bitmap)": {
                "path": "bitmap_fonts/HiraMinPro-W3.otf", 
                "size": (12, 12),
                "description": "Hiragino Mincho Pro bitmap"
            },
            
            # 特別フォント
            "みかちゃん (Bitmap)": {
                "path": "bitmap_fonts/mikachanALL.ttc",
                "size": (12, 12),
                "description": "Mikachan All bitmap font"
            },
            "aqua_pfont (Bitmap)": {
                "path": "bitmap_fonts/aqua_pfont.ttf",
                "size": (12, 12), 
                "description": "Aqua P Font bitmap"
            },
        }
        
        # 追加のビットマップフォント（アルファベット順）
        additional_fonts = []
        
        for font_info in self.installed_fonts:
            filename = font_info['filename']
            
            # 既に基本設定に含まれている場合はスキップ
            if any(filename in config.get('path', '') for config in base_configs.values()):
                continue
            
            # フォント名を生成（拡張子を除去してBitmapを追加）
            font_name = filename.rsplit('.', 1)[0]
            if len(font_name) > 30:  # 長すぎる名前は短縮
                font_name = font_name[:27] + "..."
            
            display_name = f"{font_name} (Bitmap)"
            
            # サイズ推定（ファイル名から）
            if '12' in filename.lower():
                size = (12, 12)
            elif '10' in filename.lower():
                size = (10, 10)
            elif '16' in filename.lower():
                size = (16, 16)
            elif '8' in filename.lower():
                size = (8, 8)
            else:
                size = (12, 12)  # デフォルト
            
            additional_fonts.append({
                'name': display_name,
                'config': {
                    "path": f"bitmap_fonts/{filename}",
                    "size": size,
                    "description": f"True bitmap font - {filename}"
                }
            })
        
        # アルファベット順でソート
        additional_fonts.sort(key=lambda x: x['name'])
        
        # 追加フォントを基本設定に結合
        for font in additional_fonts:
            base_configs[font['name']] = font['config']
        
        self.font_configs = base_configs
        print(f"OK Generated {len(base_configs)} font configurations")
        
        return base_configs
    
    def update_font2led_gui(self):
        """font2led_gui.pyを更新してビットマップフォントを統合"""
        gui_file = self.font2led_dir / "font2led_gui.py"
        
        if not gui_file.exists():
            print(f"ERROR font2led_gui.py not found: {gui_file}")
            return False
        
        print(f"\nUPDATE Updating font2led_gui.py...")
        
        try:
            # 現在のファイルを読み込み
            with open(gui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # font_configsセクションを探して置き換え
            start_marker = "        self.font_configs = {"
            end_marker = "        }"
            
            start_idx = content.find(start_marker)
            if start_idx == -1:
                print("ERROR font_configs section not found in font2led_gui.py")
                return False
            
            # 終了位置を探す（対応する}を見つける）
            brace_count = 0
            end_idx = start_idx + len(start_marker)
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content[end_idx:], end_idx):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == -1:
                            end_idx = i + 1
                            break
            
            # 新しいfont_configs文字列を生成
            new_configs = "        self.font_configs = {\n"
            for font_name, config in self.font_configs.items():
                new_configs += f'            "{font_name}": {{\n'
                new_configs += f'                "path": os.path.join(base_dir, "{config["path"]}"),\n'
                new_configs += f'                "size": {config["size"]},\n'
                new_configs += f'                "description": "{config["description"]}"\n'
                new_configs += f'            }},\n'
            new_configs += "        }"
            
            # 置き換え
            new_content = content[:start_idx] + new_configs + content[end_idx:]
            
            # バックアップを作成
            backup_file = gui_file.with_suffix('.py.backup')
            shutil.copy2(gui_file, backup_file)
            print(f"DIR Backup created: {backup_file}")
            
            # 新しい内容を書き込み
            with open(gui_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"OK Updated font2led_gui.py with {len(self.font_configs)} bitmap fonts")
            return True
            
        except Exception as e:
            print(f"ERROR Error updating font2led_gui.py: {e}")
            return False
    
    def generate_installation_report(self):
        """インストール結果レポートを生成"""
        report = {
            'installation_summary': {
                'total_fonts_attempted': len(self.installed_fonts) + len(self.failed_fonts),
                'successfully_installed': len([f for f in self.installed_fonts if f['status'] == 'copied']),
                'already_existed': len([f for f in self.installed_fonts if f['status'] == 'already_exists']),
                'failed': len(self.failed_fonts),
                'total_configurations': len(self.font_configs)
            },
            'installed_fonts': self.installed_fonts,
            'failed_fonts': self.failed_fonts,
            'font_configurations': self.font_configs
        }
        
        report_file = self.font2led_dir / "bitmap_font_installation_report.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"REPORT Installation report saved: {report_file}")
        except Exception as e:
            print(f"ERROR Error saving report: {e}")
        
        return report
    
    def print_summary(self, report):
        """インストール結果のサマリーを表示"""
        summary = report['installation_summary']
        
        print(f"\n" + "="*80)
        print(f"DONE BITMAP FONT INSTALLATION COMPLETED!")
        print(f"="*80)
        print(f"REPORT INSTALLATION SUMMARY:")
        print(f"   Total fonts attempted: {summary['total_fonts_attempted']}")
        print(f"   OK Successfully installed: {summary['successfully_installed']}")
        print(f"   SKIP Already existed: {summary['already_existed']}")
        print(f"   ERROR Failed: {summary['failed']}")
        print(f"   UPDATE Font configurations: {summary['total_configurations']}")
        
        if summary['failed'] > 0:
            print(f"\nERROR FAILED FONTS:")
            for font in self.failed_fonts[:5]:  # 最初の5個のみ表示
                print(f"   - {font['filename']}: {font['error']}")
            if len(self.failed_fonts) > 5:
                print(f"   ... and {len(self.failed_fonts) - 5} more")
        
        print(f"\nOK Font2LED Tool is now ready with {summary['total_configurations']} bitmap fonts!")
        print(f"READY You can now select from {summary['successfully_installed'] + summary['already_existed']} bitmap fonts in the GUI.")

def main():
    """メイン実行関数"""
    print("Font2LED Tool Bitmap Font Installer")
    print("="*80)
    
    installer = BitmapFontInstaller()
    
    # 1. ビットマップフォント用ディレクトリ作成
    installer.create_bitmap_fonts_directory()
    
    # 2. ビットマップフォントリスト読み込み
    bitmap_fonts = installer.load_bitmap_font_list()
    if not bitmap_fonts:
        print("ERROR No bitmap fonts found. Please run bitmap font detection first.")
        return
    
    # 3. フォントファイルコピー
    installer.copy_font_files(bitmap_fonts)
    
    # 4. フォント設定生成
    installer.generate_font_configs()
    
    # 5. font2led_gui.py更新
    installer.update_font2led_gui()
    
    # 6. インストールレポート生成
    report = installer.generate_installation_report()
    
    # 7. サマリー表示
    installer.print_summary(report)

if __name__ == "__main__":
    main()