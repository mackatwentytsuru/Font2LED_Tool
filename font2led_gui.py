#!/usr/bin/env python3
"""
Font2LED GUI - JF-Dot-k12x10 フォントをLEDマトリックスデータに変換するGUIツール
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import freetype
import numpy as np
from PIL import Image, ImageDraw, ImageTk
import json
import os
import sys
import shutil
import tempfile
from datetime import datetime
from typing import List, Dict, Tuple

class Font2LEDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Font2LED Tool - JF-Dot-k12x10")
        self.root.geometry("900x700")
        
        # ピクセルフォント設定
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.font_configs = {
            "JF-Dot-k12x10 (推奨)": {
                "path": r"C:\Users\macka\Downloads\JF-Dot-k12x10\JF-Dot-k12x10.ttf",
                "size": (12, 10),
                "description": "日本語対応12x10ピクセルフォント"
            },
            "k8x12 (8×12ピクセル)": {
                "path": os.path.join(base_dir, "k8x12_ttf_2021-05-05", "k8x12.ttf"),
                "size": (16, 16),
                "description": "8×12ピクセル日本語フォント（96ドット、650ドローン対応）"
            },
            "k8x12L (8×12細字)": {
                "path": os.path.join(base_dir, "k8x12_ttf_2021-05-05", "k8x12L.ttf"),
                "size": (16, 16),
                "description": "8×12ピクセル細字（96ドット、650ドローン対応）"
            },
            "k8x12S (8×12太字)": {
                "path": os.path.join(base_dir, "k8x12_ttf_2021-05-05", "k8x12S.ttf"),
                "size": (16, 16),
                "description": "8×12ピクセル太字（96ドット、650ドローン対応）"
            },
            "マルミーニャ (12×12ピクセル)": {
                "path": os.path.join(base_dir, "x12y12pxMaruMinya_2023-07-14", "x12y12pxMaruMinya.ttf"),
                "size": (12, 12),
                "description": "12×12ピクセル丸ゴシック（144ドット、かわいいデザイン）"
            },
            # 他のピクセルフォントをここに追加可能
        }
        self.current_font = "JF-Dot-k12x10 (推奨)"
        self.font_path = self.font_configs[self.current_font]["path"]
        self.face = None
        self.current_led_data = None
        self.preview_scale = 10
        self.frames = []
        self.zoom_scale = 1.0  # ズームスケール変数を追加
        self.temp_font_dir = None  # 一時フォントディレクトリ
        self.temp_font_paths = {}  # 一時フォントパスの辞書
        
        # LEDスクリーンサイズの設定
        self.screen_configs = {
            "10×65 (標準)": {"rows": 10, "cols": 65, "spacing": 30, "drone_spacing_m": 2.0},
            "13×50 (Blender実測)": {"rows": 13, "cols": 50, "spacing": 30, "drone_spacing_m": 2.0},
            "13×50 (650ドローン最適)": {"rows": 13, "cols": 50, "spacing": 26, "drone_spacing_m": 2.0},
            "10×65 (650ドローン最適)": {"rows": 10, "cols": 65, "spacing": 20, "drone_spacing_m": 2.0},
            "カスタム": {"rows": 10, "cols": 65, "spacing": 30, "drone_spacing_m": 2.0}
        }
        self.current_screen_config = "10×65 (標準)"
        
        # ドローンLEDのサイズ設定（センチメートル）
        self.drone_led_size_cm = 20.0  # デフォルト20cm
        
        # フォントサイズのカスタマイズ設定
        self.font_size_custom = {"width": 12, "height": 10}
        
        # UI構築
        self.setup_ui()
        
        # フォント読み込み
        self.load_font()
        
        # アプリケーション終了時のクリーンアップ
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """UIの構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左側パネル（入力）
        left_frame = ttk.LabelFrame(main_frame, text="テキスト入力", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # テキスト入力
        ttk.Label(left_frame, text="テキスト:").grid(row=0, column=0, sticky=tk.W)
        self.text_var = tk.StringVar(value="小津")
        text_entry = ttk.Entry(left_frame, textvariable=self.text_var, width=30, font=("Arial", 12))
        text_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # 色選択
        ttk.Label(left_frame, text="色:").grid(row=1, column=0, sticky=tk.W)
        self.color_frame = tk.Frame(left_frame, width=30, height=20, bg="#FF0000")
        self.color_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.current_color = (1.0, 0.0, 0.0)  # RGB (0.0-1.0)
        
        ttk.Button(left_frame, text="色を選択", command=self.choose_color).grid(row=1, column=2, padx=5)
        
        # フォント選択
        ttk.Label(left_frame, text="フォント:").grid(row=2, column=0, sticky=tk.W)
        self.font_var = tk.StringVar(value=self.current_font)
        font_combo = ttk.Combobox(left_frame, textvariable=self.font_var, 
                                 values=list(self.font_configs.keys()),
                                 state="readonly", width=28)
        font_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
        font_combo.bind("<<ComboboxSelected>>", self.on_font_change)
        
        # プレビュー生成ボタン
        ttk.Button(left_frame, text="プレビュー生成", command=self.generate_preview).grid(row=3, column=0, columnspan=3, pady=10)
        
        # フレームリスト
        ttk.Label(left_frame, text="フレームリスト:").grid(row=4, column=0, sticky=tk.W, pady=(10, 0))
        
        # リストボックスとスクロールバー
        list_frame = ttk.Frame(left_frame)
        list_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.frame_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.frame_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.frame_listbox.yview)
        
        # フレーム追加ボタン
        ttk.Button(left_frame, text="現在のテキストを追加", command=self.add_frame).grid(row=6, column=0, columnspan=2, pady=5)
        ttk.Button(left_frame, text="選択を削除", command=self.delete_frame).grid(row=6, column=2, pady=5)
        
        # スクリーンサイズ選択
        screen_frame = ttk.LabelFrame(left_frame, text="LEDスクリーン設定", padding="5")
        screen_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.screen_size_var = tk.StringVar(value=self.current_screen_config)
        for i, config_name in enumerate(self.screen_configs.keys()):
            rb = ttk.Radiobutton(screen_frame, text=config_name, 
                               variable=self.screen_size_var, 
                               value=config_name,
                               command=self.update_screen_size)
            rb.grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        
        # カスタム設定フレーム
        custom_frame = ttk.Frame(screen_frame)
        custom_frame.grid(row=len(self.screen_configs), column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 行数と列数
        ttk.Label(custom_frame, text="行数:").grid(row=0, column=0, sticky=tk.W)
        self.custom_rows_var = tk.IntVar(value=10)
        ttk.Spinbox(custom_frame, from_=1, to=100, textvariable=self.custom_rows_var, width=8).grid(row=0, column=1, padx=2)
        
        ttk.Label(custom_frame, text="列数:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.custom_cols_var = tk.IntVar(value=65)
        ttk.Spinbox(custom_frame, from_=1, to=200, textvariable=self.custom_cols_var, width=8).grid(row=0, column=3, padx=2)
        
        # ドローン間隔
        ttk.Label(custom_frame, text="ドローン間隔:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.custom_drone_spacing_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(custom_frame, from_=0.5, to=10.0, increment=0.1, textvariable=self.custom_drone_spacing_var, width=8).grid(row=1, column=1, padx=2, pady=(5, 0))
        ttk.Label(custom_frame, text="メートル").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(custom_frame, text="カスタム適用", command=self.apply_custom_settings).grid(row=1, column=3, padx=5, pady=(5, 0))
        
        # フォントサイズ設定
        font_size_frame = ttk.LabelFrame(left_frame, text="フォントサイズ設定", padding="5")
        font_size_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(font_size_frame, text="幅(ピクセル):").grid(row=0, column=0, sticky=tk.W)
        self.font_width_var = tk.IntVar(value=12)
        ttk.Spinbox(font_size_frame, from_=8, to=32, textvariable=self.font_width_var, width=8).grid(row=0, column=1, padx=2)
        
        ttk.Label(font_size_frame, text="高さ(ピクセル):").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.font_height_var = tk.IntVar(value=10)
        ttk.Spinbox(font_size_frame, from_=8, to=32, textvariable=self.font_height_var, width=8).grid(row=0, column=3, padx=2)
        
        ttk.Button(font_size_frame, text="フォントサイズ更新", command=self.update_font_size).grid(row=0, column=4, padx=10)
        
        # 右側パネル（プレビュー）
        config = self.screen_configs[self.current_screen_config]
        self.right_frame = ttk.LabelFrame(main_frame, text=f"LEDスクリーン ({config['rows']}行×{config['cols']}列)", padding="10")
        right_frame = self.right_frame
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # プレビューキャンバス（選択されたスクリーンサイズに基づく）
        # デフォルト：10×65（標準）
        # GUI表示比率：10倍（3.0単位 = 30ピクセル）
        
        # スクロール可能なキャンバス用のフレーム
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # キャンバスとスクロールバー
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        
        # 初期サイズは小さめに設定（ウィンドウに収まるように）
        self.canvas = tk.Canvas(canvas_frame, width=600, height=300, bg="#000000",
                               xscrollcommand=h_scrollbar.set,
                               yscrollcommand=v_scrollbar.set)
        
        # グリッド配置
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # スクロールバーの設定
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # フレームのグリッド設定
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 右フレームのグリッド設定
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # スケール調整
        scale_frame = ttk.Frame(right_frame)
        scale_frame.grid(row=1, column=0, pady=5)
        
        # LED球体サイズ
        ttk.Label(scale_frame, text="LEDサイズ:").pack(side=tk.LEFT)
        self.led_size_cm_var = tk.DoubleVar(value=20.0)  # デフォルト20cm
        size_spinbox = ttk.Spinbox(scale_frame, from_=5.0, to=100.0, increment=1.0, textvariable=self.led_size_cm_var, width=6)
        size_spinbox.pack(side=tk.LEFT, padx=2)
        ttk.Label(scale_frame, text="cm").pack(side=tk.LEFT)
        
        # 表示間隔（表示用のみ）
        ttk.Label(scale_frame, text="表示間隔:").pack(side=tk.LEFT, padx=(10, 0))
        self.spacing_var = tk.IntVar(value=30)  # ピクセル単位
        spacing_spinbox = ttk.Spinbox(scale_frame, from_=20, to=50, textvariable=self.spacing_var, width=5)
        spacing_spinbox.pack(side=tk.LEFT, padx=2)
        ttk.Label(scale_frame, text="px").pack(side=tk.LEFT)
        
        ttk.Button(scale_frame, text="適用", command=self.update_canvas_size).pack(side=tk.LEFT, padx=10)
        
        # ズーム調整
        ttk.Label(scale_frame, text="表示:").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Button(scale_frame, text="全体表示", command=self.fit_to_window).pack(side=tk.LEFT, padx=5)
        
        # 拡大率入力
        self.zoom_percent_var = tk.IntVar(value=100)
        zoom_spinbox = ttk.Spinbox(scale_frame, from_=10, to=500, increment=10, textvariable=self.zoom_percent_var, width=6)
        zoom_spinbox.pack(side=tk.LEFT, padx=2)
        ttk.Label(scale_frame, text="%").pack(side=tk.LEFT)
        ttk.Button(scale_frame, text="適用", command=self.apply_zoom_percent).pack(side=tk.LEFT, padx=5)
        
        # 下部パネル（エクスポート）
        bottom_frame = ttk.LabelFrame(main_frame, text="エクスポート", padding="10")
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # エクスポートボタン
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="JSONエクスポート", command=self.export_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skybrushスクリプトエクスポート", command=self.export_skybrush_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Custom Expressionエクスポート", command=self.export_custom_expression).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="画像プレビュー保存", command=self.save_preview_images).pack(side=tk.LEFT, padx=5)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # ウィンドウサイズ設定
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
    def load_font(self):
        """フォントを読み込み（Unicode パス問題を解決）"""
        try:
            font_config = self.font_configs[self.current_font]
            original_path = font_config["path"]
            
            if not os.path.exists(original_path):
                messagebox.showerror("エラー", f"フォントファイルが見つかりません:\n{original_path}")
                return
            
            # Unicode パス問題の対策：一時ディレクトリにコピー
            if not original_path.isascii():
                # 一時ディレクトリの作成（初回のみ）
                if self.temp_font_dir is None:
                    self.temp_font_dir = tempfile.mkdtemp(prefix="font2led_")
                
                # フォント名から安全なファイル名を作成（ASCII文字のみ）
                import re
                safe_font_name = re.sub(r'[^\w\-_\.]', '_', self.current_font)  # 英数字、アンダースコア、ハイフンのみ
                safe_font_name = safe_font_name.encode('ascii', 'ignore').decode('ascii')  # 非ASCII文字を除去
                if not safe_font_name:  # 空文字列の場合はデフォルト名
                    safe_font_name = f"font_{hash(self.current_font) % 10000}"
                temp_font_path = os.path.join(self.temp_font_dir, f"{safe_font_name}.ttf")
                
                # まだコピーしていない場合のみコピー
                if self.current_font not in self.temp_font_paths:
                    shutil.copy2(original_path, temp_font_path)
                    self.temp_font_paths[self.current_font] = temp_font_path
                    print(f"フォントを一時ディレクトリにコピー: {temp_font_path}")
                
                self.font_path = self.temp_font_paths[self.current_font]
            else:
                self.font_path = original_path
            
            # freetypeでフォントロード
            self.face = freetype.Face(self.font_path)
            self.face.set_pixel_sizes(font_config["size"][0], font_config["size"][1])
            self.status_var.set(f"フォント読み込み完了: {self.current_font}")
            
        except Exception as e:
            error_msg = f"フォント読み込みエラー:\n{str(e)}\n\nフォント: {self.current_font}\nパス: {original_path}"
            messagebox.showerror("エラー", error_msg)
            print(f"Font loading error: {e}")  # デバッグ用
            
    def on_font_change(self, event=None):
        """フォント選択変更時の処理"""
        self.current_font = self.font_var.get()
        self.load_font()
        # プレビューを更新
        if self.current_led_data:
            self.generate_preview()
            
    def choose_color(self):
        """色選択ダイアログ"""
        # 現在の色をRGB(0-255)に変換
        init_color = tuple(int(c * 255) for c in self.current_color)
        color = colorchooser.askcolor(initialcolor=init_color)
        
        if color[0]:  # 色が選択された場合
            # RGB(0-255)から(0.0-1.0)に変換
            self.current_color = tuple(c / 255.0 for c in color[0])
            # 色プレビューを更新
            hex_color = color[1]
            self.color_frame.config(bg=hex_color)
            
    def get_char_bitmap(self, char: str) -> np.ndarray:
        """文字のビットマップを取得"""
        try:
            # 文字をロード（モノクロモード）
            self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_MONOCHROME)
            bitmap = self.face.glyph.bitmap
            
            if bitmap.width > 0 and bitmap.rows > 0:
                # モノクロビットマップを2D配列に変換
                data = []
                for y in range(bitmap.rows):
                    row = []
                    for x in range(bitmap.width):
                        # ビット位置を計算
                        byte_index = y * bitmap.pitch + x // 8
                        bit_index = 7 - (x % 8)
                        
                        if byte_index < len(bitmap.buffer):
                            pixel = (bitmap.buffer[byte_index] >> bit_index) & 1
                            row.append(pixel)
                        else:
                            row.append(0)
                    data.append(row)
                
                result = np.array(data, dtype=np.uint8)
                
                # カスタマイズ可能なフォントサイズに正規化
                font_height = self.font_height_var.get() if hasattr(self, 'font_height_var') else 10
                font_width = self.font_width_var.get() if hasattr(self, 'font_width_var') else 12
                
                normalized = np.zeros((font_height, font_width), dtype=np.uint8)
                h, w = result.shape
                # 下揃えで配置（高さが異なる場合も対応）
                if w <= font_width:
                    if h < font_height:
                        # 高さが指定未満の場合は下揃え
                        normalized[font_height-h:font_height, :w] = result
                    elif h == font_height:
                        # 高さがちょうど指定の場合
                        normalized[:, :w] = result
                    else:
                        # 高さが指定を超える場合は下から指定行を取る
                        normalized[:, :w] = result[h-font_height:h, :w]
                else:
                    # 幅が指定を超える場合はクロップ
                    if h < font_height:
                        normalized[font_height-h:font_height, :font_width] = result[:, :font_width]
                    elif h == font_height:
                        normalized[:, :font_width] = result[:, :font_width]
                    else:
                        normalized[:, :font_width] = result[h-font_height:h, :font_width]
                
                return normalized
            else:
                # 空白文字の場合
                font_height = self.font_height_var.get() if hasattr(self, 'font_height_var') else 10
                font_width = self.font_width_var.get() if hasattr(self, 'font_width_var') else 12
                return np.zeros((font_height, font_width), dtype=np.uint8)
                
        except Exception as e:
            print(f"Warning: Failed to load character '{char}': {e}")
            return np.zeros((10, 12), dtype=np.uint8)
            
    def text_to_led_matrix(self, text: str, spacing: int = 1) -> Dict:
        """テキストをLEDマトリックスデータに変換"""
        font_height = self.font_height_var.get() if hasattr(self, 'font_height_var') else 10
        font_width = self.font_width_var.get() if hasattr(self, 'font_width_var') else 12
        
        if not text:
            return {"width": 0, "height": font_height, "pixels": [], "matrix": np.zeros((font_height, 0))}
        
        # 各文字のビットマップを取得
        bitmaps = []
        total_width = 0
        
        for i, char in enumerate(text):
            bitmap = self.get_char_bitmap(char)
            # 実際の文字幅を計算（空白列を除く）
            char_width = 0
            for x in range(bitmap.shape[1]):
                if np.any(bitmap[:, x] > 0):
                    char_width = x + 1
            
            if char_width > 0:
                bitmaps.append(bitmap[:, :char_width])
                total_width += char_width
            else:
                # スペースの場合は固定幅
                bitmaps.append(np.zeros((font_height, 4), dtype=np.uint8))
                total_width += 4
            
            if i < len(text) - 1:
                total_width += spacing
        
        # 全体のマトリックスを作成
        matrix = np.zeros((font_height, total_width), dtype=np.uint8)
        x_offset = 0
        
        for i, bitmap in enumerate(bitmaps):
            h, w = bitmap.shape
            matrix[:h, x_offset:x_offset+w] = bitmap
            x_offset += w
            if i < len(bitmaps) - 1:
                x_offset += spacing
        
        # 点灯ピクセルの座標を抽出
        pixels = []
        for y in range(font_height):
            for x in range(total_width):
                if matrix[y, x] > 0:
                    pixels.append((x, y))
        
        return {
            "width": total_width,
            "height": font_height,
            "pixels": pixels,
            "matrix": matrix
        }
        
    def generate_preview(self):
        """プレビュー生成"""
        text = self.text_var.get()
        if not text:
            messagebox.showwarning("警告", "テキストを入力してください")
            return
            
        self.current_led_data = self.text_to_led_matrix(text)
        self.update_preview()
        self.status_var.set(f"プレビュー生成完了: {self.current_led_data['width']}×10ピクセル")
        
    def update_preview(self):
        """プレビュー表示を更新（選択されたスクリーンサイズに基づく）"""
        if not self.current_led_data:
            return
            
        spacing = int(self.spacing_var.get() * self.zoom_scale)
        # LEDサイズをcmからピクセルに変換（表示用）
        # 20cm → 20ピクセルの比率で計算
        led_size = int((self.led_size_cm_var.get() / 20.0) * 20 * self.zoom_scale)
        
        # 選択されたスクリーンサイズを使用
        config = self.screen_configs[self.screen_size_var.get()]
        rows = config["rows"]
        cols = config["cols"]
        canvas_width = cols * spacing
        canvas_height = rows * spacing
        
        # キャンバスのスクロール領域を設定
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # キャンバスをクリア
        self.canvas.delete("all")
        
        # すべてのLED位置を描画（消灯状態）
        for row in range(rows):
            for col in range(cols):
                center_x = col * spacing + spacing // 2
                center_y = row * spacing + spacing // 2
                
                # LED球体（消灯時は暗いグレー）
                x1 = center_x - led_size // 2
                y1 = center_y - led_size // 2
                x2 = center_x + led_size // 2
                y2 = center_y + led_size // 2
                
                self.canvas.create_oval(x1, y1, x2, y2, fill="#101010", outline="#303030", width=1)
        
        # 点灯するLEDを描画
        led_data = self.current_led_data
        x_offset = (cols - led_data["width"]) // 2  # 水平方向のセンタリング
        y_offset = (rows - led_data["height"]) // 2  # 垂直方向のセンタリング
        
        # RGB(0.0-1.0)から16進数カラーコードに変換
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(self.current_color[0] * 255),
            int(self.current_color[1] * 255),
            int(self.current_color[2] * 255)
        )
        
        # 明るい色（エミッション効果）
        bright_hex = "#{:02x}{:02x}{:02x}".format(
            min(255, int(self.current_color[0] * 255 * 1.3)),
            min(255, int(self.current_color[1] * 255 * 1.3)),
            min(255, int(self.current_color[2] * 255 * 1.3))
        )
        
        for x, y in led_data["pixels"]:
            led_x = x + x_offset
            led_y = y + y_offset
            if 0 <= led_x < cols and 0 <= led_y < rows:
                center_x = led_x * spacing + spacing // 2
                center_y = led_y * spacing + spacing // 2
                
                # LED球体（点灯時）
                x1 = center_x - led_size // 2
                y1 = center_y - led_size // 2
                x2 = center_x + led_size // 2
                y2 = center_y + led_size // 2
                
                # グロー効果（外側の輪）
                glow_size = led_size + 4
                gx1 = center_x - glow_size // 2
                gy1 = center_y - glow_size // 2
                gx2 = center_x + glow_size // 2
                gy2 = center_y + glow_size // 2
                
                self.canvas.create_oval(gx1, gy1, gx2, gy2, fill="", outline=hex_color, width=2)
                self.canvas.create_oval(x1, y1, x2, y2, fill=bright_hex, outline=hex_color, width=2)
                
    def update_canvas_size(self):
        """キャンバスサイズを更新"""
        self.update_preview()
        
    def fit_to_window(self):
        """ウィンドウサイズに合わせて全体表示"""
        # キャンバスの表示可能サイズを取得
        canvas_view_width = self.canvas.winfo_width()
        canvas_view_height = self.canvas.winfo_height()
        
        if canvas_view_width <= 1 or canvas_view_height <= 1:
            # ウィンドウがまだ描画されていない場合は少し待つ
            self.root.after(100, self.fit_to_window)
            return
        
        # 選択されたスクリーンサイズを取得
        config = self.screen_configs[self.screen_size_var.get()]
        rows = config["rows"]
        cols = config["cols"]
        base_spacing = self.spacing_var.get()
        
        # 必要なスケールを計算（パディングを考慮）
        padding = 20
        scale_x = (canvas_view_width - padding) / (cols * base_spacing)
        scale_y = (canvas_view_height - padding) / (rows * base_spacing)
        
        # 小さい方のスケールを採用（全体が収まるように）
        self.zoom_scale = min(scale_x, scale_y, 1.0)  # 最大でも100%
        
        # プレビューを更新
        self.update_preview()
        
    def reset_zoom(self):
        """ズームを100%にリセット"""
        self.zoom_scale = 1.0
        self.zoom_percent_var.set(100)
        self.update_preview()
        
    def apply_zoom_percent(self):
        """入力されたパーセンテージでズームを適用"""
        percent = self.zoom_percent_var.get()
        self.zoom_scale = percent / 100.0
        self.update_preview()
        
    def update_screen_size(self):
        """スクリーンサイズの変更を反映"""
        config_name = self.screen_size_var.get()
        config = self.screen_configs[config_name]
        
        # ラベルを更新
        self.right_frame.config(text=f"LEDスクリーン ({config['rows']}行×{config['cols']}列)")
        
        # キャンバスサイズを更新
        self.update_canvas_size()
        
    def add_frame(self):
        """現在のテキストをフレームリストに追加"""
        text = self.text_var.get()
        if not text:
            messagebox.showwarning("警告", "テキストを入力してください")
            return
            
        # フレームデータを作成
        led_data = self.text_to_led_matrix(text)
        frame_data = {
            "text": text,
            "color": self.current_color,
            "led_data": led_data
        }
        
        self.frames.append(frame_data)
        
        # リストボックスに追加
        color_str = f"RGB({self.current_color[0]:.1f}, {self.current_color[1]:.1f}, {self.current_color[2]:.1f})"
        self.frame_listbox.insert(tk.END, f"{text} - {color_str}")
        
        self.status_var.set(f"フレーム追加: {text}")
        
    def delete_frame(self):
        """選択されたフレームを削除"""
        selection = self.frame_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        self.frame_listbox.delete(index)
        del self.frames[index]
        
        self.status_var.set("フレーム削除完了")
        
    def export_json(self):
        """JSONファイルとしてエクスポート"""
        if not self.frames:
            messagebox.showwarning("警告", "エクスポートするフレームがありません")
            return
            
        # デフォルトファイル名を最初のフレームのテキストから生成
        default_filename = "led_animation"
        if self.frames:
            default_filename = self.frames[0]["text"]
            
        filename = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        # エクスポート用データを構築
        config = self.screen_configs[self.screen_size_var.get()]
        export_data = {
            "metadata": {
                "grid_width": config["cols"],
                "grid_height": config["rows"],
                "frame_count": len(self.frames),
                "font": "JF-Dot-k12x10",
                "created": datetime.now().isoformat()
            },
            "frames": []
        }
        
        for i, frame in enumerate(self.frames):
            frame_data = {
                "frame": i * 20,  # 20フレーム間隔
                "text": frame["text"],
                "pixels": []
            }
            
            led_data = frame["led_data"]
            x_offset = (config["cols"] - led_data["width"]) // 2  # 水平方向のセンタリング
            y_offset = (config["rows"] - led_data["height"]) // 2  # 垂直方向のセンタリング
            
            for x, y in led_data["pixels"]:
                led_x = x + x_offset
                led_y = y + y_offset
                if 0 <= led_x < config["cols"] and 0 <= led_y < config["rows"]:
                    frame_data["pixels"].append({
                        "x": led_x,
                        "y": led_y,
                        "r": frame["color"][0],
                        "g": frame["color"][1],
                        "b": frame["color"][2]
                    })
                    
            export_data["frames"].append(frame_data)
        
        # JSON保存
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        self.status_var.set(f"JSONエクスポート完了: {filename}")
        
    def export_skybrush_script(self):
        """Skybrush用スクリプトをエクスポート"""
        if not self.frames:
            messagebox.showwarning("警告", "エクスポートするフレームがありません")
            return
            
        # デフォルトファイル名を最初のフレームのテキストから生成
        default_filename = "skybrush_led_script"
        if self.frames:
            default_filename = f"skybrush_{self.frames[0]['text']}"
            
        filename = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        # スクリプト生成のための座標計算
        config = self.screen_configs[self.screen_size_var.get()]
        rows = config["rows"]
        cols = config["cols"]
        drone_spacing_m = config["drone_spacing_m"]  # メートル単位
        
        # Blender内での座標計算（メートルをBlender単位として扱う）
        drone_spacing = drone_spacing_m  # Blenderでは1単位 = 1メートル
        
        # 座標範囲を計算（実際のSkybrush配置に基づく）
        if cols == 65 and rows == 10:
            # 10x65 LEDスクリーンの実測値を使用
            x_min, x_max = -47.1, 47.1  # 実測値
            z_min, z_max = 45.7, 58.9   # 実測値
        else:
            # その他のサイズは理論値を使用
            total_width = (cols - 1) * drone_spacing
            total_height = (rows - 1) * drone_spacing
            x_min = -total_width / 2
            x_max = total_width / 2
            z_min = 0
            z_max = total_height
        
        # スクリプトテンプレート
        script_template = '''"""
Skybrush LED Effects Script - Generated by Font2LED Tool
Generated: {timestamp}
Grid: {rows} rows x {cols} columns
Drone Spacing: {drone_spacing_m} meters
"""

# エンベッドされたLEDデータ
LED_DATA = {led_data}

def main(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """Skybrush LED Effects メイン関数"""
    
    # 座標からグリッド位置を計算
    x = position[0]
    z = position[2]
    
    # 座標範囲
    x_min, x_max = {x_min:.1f}, {x_max:.1f}
    z_min, z_max = {z_min:.1f}, {z_max:.1f}
    
    # グリッド位置
    grid_x = int(round((x - x_min) / {drone_spacing}))
    grid_z = {rows_minus_1} - int(round((z - z_min) / {drone_spacing}))
    
    # 範囲チェック
    if not (0 <= grid_x < {cols} and 0 <= grid_z < {rows}):
        return (0.0, 0.0, 0.0, 1.0)
    
    # フレーム選択
    frames = LED_DATA["frames"]
    if not frames:
        return (0.0, 0.0, 0.0, 1.0)
        
    frame_index = min(int(time_fraction * len(frames)), len(frames) - 1)
    current_frame = frames[frame_index]
    
    # ピクセルチェック
    for pixel in current_frame["pixels"]:
        if grid_x == pixel["x"] and grid_z == pixel["y"]:
            return (pixel["r"], pixel["g"], pixel["b"], 1.0)
    
    return (0.0, 0.0, 0.0, 1.0)
'''
        
        # エクスポート用データを構築
        config = self.screen_configs[self.screen_size_var.get()]
        export_data = {
            "frames": []
        }
        
        for i, frame in enumerate(self.frames):
            frame_data = {
                "text": frame["text"],
                "pixels": []
            }
            
            led_data = frame["led_data"]
            x_offset = (config["cols"] - led_data["width"]) // 2  # 選択された列数にセンタリング
            
            for x, y in led_data["pixels"]:
                led_x = x + x_offset
                if 0 <= led_x < config["cols"]:
                    frame_data["pixels"].append({
                        "x": led_x,
                        "y": y,
                        "r": frame["color"][0],
                        "g": frame["color"][1],
                        "b": frame["color"][2]
                    })
                    
            export_data["frames"].append(frame_data)
        
        # スクリプト生成
        script_content = script_template.format(
            timestamp=datetime.now().isoformat(),
            rows=rows,
            cols=cols,
            drone_spacing_m=drone_spacing_m,
            led_data=json.dumps(export_data, ensure_ascii=False, indent=4),
            x_min=x_min,
            x_max=x_max,
            z_min=z_min,
            z_max=z_max,
            rows_minus_1=rows-1
        )
        
        # ファイル保存
        with open(filename, "w", encoding="utf-8") as f:
            f.write(script_content)
            
        self.status_var.set(f"Skybrushスクリプトエクスポート完了: {filename}")
        
    def apply_custom_settings(self):
        """カスタム設定を適用"""
        # カスタム設定を更新
        self.screen_configs["カスタム"] = {
            "rows": self.custom_rows_var.get(),
            "cols": self.custom_cols_var.get(),
            "spacing": 30,  # GUI表示用のピクセル間隔は固定
            "drone_spacing_m": self.custom_drone_spacing_var.get()  # メートル単位
        }
        
        # カスタムを選択
        self.screen_size_var.set("カスタム")
        self.update_screen_size()
        
        self.status_var.set(f"カスタム設定適用: {self.custom_rows_var.get()}×{self.custom_cols_var.get()}, 間隔{self.custom_drone_spacing_var.get()}m")
        
    def update_font_size(self):
        """フォントサイズを更新"""
        # フォントを再読み込み
        if self.face:
            self.face.set_pixel_sizes(self.font_width_var.get(), self.font_height_var.get())
            self.status_var.set(f"フォントサイズ更新: {self.font_width_var.get()}×{self.font_height_var.get()}")
            
            # プレビューを更新
            if self.current_led_data:
                self.generate_preview()
        
    def save_preview_images(self):
        """プレビュー画像を保存"""
        if not self.frames:
            messagebox.showwarning("警告", "保存するフレームがありません")
            return
            
        # デフォルトのフォルダ名を提案（初回は手動で選択）
        folder = filedialog.askdirectory(
            title="画像保存先フォルダを選択"
        )
        if not folder:
            return
            
        for i, frame in enumerate(self.frames):
            # 画像生成（選択されたスクリーンサイズ準拠）
            config = self.screen_configs[self.screen_size_var.get()]
            scale = 20
            img_width = config["cols"] * scale
            img_height = config["rows"] * scale
            
            image = Image.new('RGB', (img_width, img_height), 'black')
            draw = ImageDraw.Draw(image)
            
            # グリッド線
            for x in range(0, img_width + 1, scale):
                draw.line([(x, 0), (x, img_height)], fill=(40, 40, 40))
            for y in range(0, img_height + 1, scale):
                draw.line([(0, y), (img_width, y)], fill=(40, 40, 40))
            
            # LEDピクセル（選択されたグリッド）
            led_data = frame["led_data"]
            x_offset = (config["cols"] - led_data["width"]) // 2  # 水平方向のセンタリング
            y_offset = (config["rows"] - led_data["height"]) // 2  # 垂直方向のセンタリング
            
            color_rgb = tuple(int(c * 255) for c in frame["color"])
            
            for x, y in led_data["pixels"]:
                led_x = x + x_offset
                led_y = y + y_offset
                if 0 <= led_x < config["cols"] and 0 <= led_y < config["rows"]:
                    x1 = led_x * scale + 2
                    y1 = led_y * scale + 2
                    x2 = x1 + scale - 4
                    y2 = y1 + scale - 4
                    draw.ellipse([x1, y1, x2, y2], fill=color_rgb)
            
            # テキスト情報
            info_image = Image.new('RGB', (img_width, img_height + 30), 'black')
            info_image.paste(image, (0, 0))
            info_draw = ImageDraw.Draw(info_image)
            info_draw.text((10, img_height + 5), f"Text: {frame['text']}", fill=(200, 200, 200))
            
            # 保存
            filename = os.path.join(folder, f"frame_{i+1:02d}_{frame['text']}.png")
            info_image.save(filename)
            
        self.status_var.set(f"画像保存完了: {folder}")
        
    def export_custom_expression(self):
        """Skybrush Custom Expression用スクリプトをエクスポート"""
        if not self.frames:
            messagebox.showwarning("警告", "エクスポートするフレームがありません")
            return
            
        # デフォルトファイル名を最初のフレームのテキストから生成
        default_filename = "custom_expression_led"
        if self.frames:
            default_filename = f"custom_expression_{self.frames[0]['text']}"
            
        filename = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        # ピクセルデータを収集（中央配置を適用）
        config = self.screen_configs[self.screen_size_var.get()]
        pixels_data = []
        for frame in self.frames:
            led_data = frame["led_data"]
            x_offset = (config["cols"] - led_data["width"]) // 2  # 水平方向のセンタリング
            y_offset = (config["rows"] - led_data["height"]) // 2  # 垂直方向のセンタリング
            
            for x, y in led_data["pixels"]:
                adjusted_x = x + x_offset
                adjusted_y = y + y_offset
                if 0 <= adjusted_x < config["cols"] and 0 <= adjusted_y < config["rows"]:
                    pixels_data.append((adjusted_x, adjusted_y))
        
        # 重複を除去してソート
        unique_pixels = sorted(list(set(pixels_data)))
        
        # Pythonタプル形式の文字列を作成
        pixels_str = "{\n"
        for i, (x, y) in enumerate(unique_pixels):
            if i > 0 and i % 8 == 0:  # 8個ごとに改行
                pixels_str += ",\n"
            elif i > 0:
                pixels_str += ", "
            pixels_str += f"({x},{y})"
        pixels_str += "\n}"
        
        # Custom Expression テンプレート（正しいSkybrush関数形式）
        custom_expression_template = '''# Skybrush Custom Expression Function
# Generated by Font2LED Tool - {timestamp}
# Text: {text_content}

# グリッドサイズ設定
GRID_WIDTH = {grid_cols}
GRID_HEIGHT = {grid_rows}

# 座標範囲（ドローン配置設定に基づく動的計算）
# グリッド: {grid_cols}列×{grid_rows}行、間隔: {drone_spacing}m
DRONE_SPACING = {drone_spacing}  # ドローン間隔(m)
X_MIN = -(GRID_WIDTH - 1) * DRONE_SPACING / 2
X_MAX = (GRID_WIDTH - 1) * DRONE_SPACING / 2
Z_MIN = -(GRID_HEIGHT - 1) * DRONE_SPACING / 2
Z_MAX = (GRID_HEIGHT - 1) * DRONE_SPACING / 2

# ピクセルデータ（Grid座標）
PIXELS = {pixels_data}

def {function_name}(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """
    Skybrush Custom Expression関数
    
    Args:
        frame: フレーム番号
        time_fraction: 時間進行度（0.0-1.0）
        drone_index: ドローンインデックス
        formation_index: フォーメーションインデックス
        position: ドローンの3D座標 (x, y, z)
        drone_count: ドローン総数
    
    Returns:
        float: Color Ramp用のインデックス値（0.0-1.0）
    """
    
    # ドローンの現在位置を取得
    x_pos = position[0]  # X座標
    z_pos = position[2]  # Z座標（高さ）
    
    # 座標をグリッドインデックスに変換
    if X_MAX > X_MIN and Z_MAX > Z_MIN:
        # X軸: グリッド列 (0-{grid_cols_minus_1})
        grid_x = int(round((x_pos - X_MIN) / (X_MAX - X_MIN) * (GRID_WIDTH - 1)))
        
        # Z軸: グリッド行 (0-{grid_rows_minus_1})、上下反転
        grid_z = int(round((z_pos - Z_MIN) / (Z_MAX - Z_MIN) * (GRID_HEIGHT - 1)))
        grid_z = {grid_rows_minus_1} - grid_z  # 上下反転
        
        # 範囲チェック
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_z < GRID_HEIGHT:
            # ピクセルデータをチェック
            if (grid_x, grid_z) in PIXELS:
                return 1.0  # 文字部分（Color Rampで色に変換）
        
        return 0.0  # 背景（黒）
    else:
        return 0.0  # エラー時（黒）'''
        
        # スクリプト生成のための設定
        config = self.screen_configs[self.screen_size_var.get()]
        text_content = " + ".join([frame["text"] for frame in self.frames])
        
        # 関数名を生成（テキストから安全な関数名を作成）
        safe_text = text_content.replace(" ", "_").replace("+", "_").replace("　", "_")
        safe_text = "".join(c for c in safe_text if c.isalnum() or c == "_")
        function_name = f"{safe_text}_display" if safe_text else "text_display"
        
        script_content = custom_expression_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            text_content=text_content,
            function_name=function_name,
            pixels_data=pixels_str,
            grid_cols=config["cols"],
            grid_rows=config["rows"],
            grid_cols_minus_1=config["cols"] - 1,
            grid_rows_minus_1=config["rows"] - 1,
            drone_spacing=config["drone_spacing_m"]
        )
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(script_content)
                
            self.status_var.set(f"Custom Expression エクスポート完了: {os.path.basename(filename)}")
            
            # 使用方法を表示
            usage_msg = f"""Custom Expressionエクスポート完了！

使用方法:
1. Blenderのテキストエディタで新規ファイルを作成
2. エクスポートしたファイル内容をコピー&ペースト
3. ファイル名を設定（例: {os.path.basename(filename).replace('.py', '')}）
4. Skybrush Light Effectsで:
   - Type: COLOR_RAMP
   - Output: CUSTOM
   - File: テキストブロック名を選択
   - Color Rampで0.0→黒、1.0→希望の色に設定

⚠️ 重要: 座標範囲は動的計算されます
設定: {config['cols']}列×{config['rows']}行、間隔{config['drone_spacing_m']}m
計算座標範囲: X({-(config['cols']-1)*config['drone_spacing_m']/2:.1f}～{(config['cols']-1)*config['drone_spacing_m']/2:.1f}), Z({-(config['rows']-1)*config['drone_spacing_m']/2:.1f}～{(config['rows']-1)*config['drone_spacing_m']/2:.1f})
Font2LED Toolの設定とBlenderの実際のドローン配置が一致している必要があります。"""
            
            messagebox.showinfo("エクスポート完了", usage_msg)
            
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル保存エラー: {e}")

    def on_closing(self):
        """アプリケーション終了時のクリーンアップ"""
        try:
            # 一時フォントディレクトリのクリーンアップ
            if self.temp_font_dir and os.path.exists(self.temp_font_dir):
                shutil.rmtree(self.temp_font_dir)
                print(f"一時ディレクトリをクリーンアップ: {self.temp_font_dir}")
        except Exception as e:
            print(f"クリーンアップエラー: {e}")
        finally:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = Font2LEDApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()