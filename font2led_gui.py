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
from pixelmap_parser import PixelMapParser

class Font2LEDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Font2LED Tool - JF-Dot-k12x10")
        self.root.geometry("900x700")
        
        # システムフォント設定（FreeType 100%互換）
        self.font_configs = {
            "Consolas (推奨★)": {
                "path": "C:/Windows/Fonts/consola.ttf",
                "size": (12, 12),
                "description": "Japanese support - Optimal monospace for LED"
            },
            "Meiryo (日本語)": {
                "path": "C:/Windows/Fonts/meiryo.ttc",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "Arial": {
                "path": "C:/Windows/Fonts/arial.ttf",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "Calibri": {
                "path": "C:/Windows/Fonts/calibri.ttf",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "Courier New": {
                "path": "C:/Windows/Fonts/courier.ttf",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "Times New Roman": {
                "path": "C:/Windows/Fonts/times.ttf",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "Verdana": {
                "path": "C:/Windows/Fonts/verdana.ttf",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "MS Gothic (日本語)": {
                "path": "C:/Windows/Fonts/msgothic.ttc",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "MS Mincho (日本語)": {
                "path": "C:/Windows/Fonts/msmincho.ttc",
                "size": (12, 12),
                "description": "Japanese support"
            },
            "Yu Gothic Medium (日本語)": {
                "path": "C:/Windows/Fonts/YuGothM.ttc",
                "size": (12, 12),
                "description": "Japanese support"
            }
        }
        self.current_font = "Consolas (推奨★)"
        self.font_path = self.font_configs[self.current_font]["path"]
        self.face = None
        self.current_led_data = None
        self.preview_scale = 10
        self.frames = []
        self.zoom_scale = 1.0  # ズームスケール変数を追加
        self.temp_font_dir = None  # 一時フォントディレクトリ
        self.temp_font_paths = {}  # 一時フォントパスの辞書
        
        # アニメーション状態変数
        self.animation_running = False
        self.animation_paused = False
        self.animation_start_time = 0
        self.animation_pause_time = 0
        
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
        
        # 行数・列数方向制御のためのoffset管理
        self.y_offset_adjustment = 0  # 上下方向の位置調整値
        self.x_offset_adjustment = 0  # 左右方向の位置調整値
        
        # ボタン操作のロック機構（同時押し防止）
        self.button_operation_lock = False
        
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
        self.text_var = tk.StringVar(value="小津ちゃん")
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
        
        # アニメーション設定セクション
        anim_frame = ttk.LabelFrame(left_frame, text="アニメーション設定", padding="5")
        anim_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # アニメーション有効チェック
        self.animation_enabled = tk.BooleanVar(value=False)
        anim_check = ttk.Checkbutton(anim_frame, text="アニメーション有効", 
                                   variable=self.animation_enabled,
                                   command=self.toggle_animation)
        anim_check.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        # アニメーション方向
        ttk.Label(anim_frame, text="方向:").grid(row=1, column=0, sticky=tk.W)
        self.animation_direction = tk.StringVar(value="右→左")
        direction_combo = ttk.Combobox(anim_frame, textvariable=self.animation_direction,
                                     values=["右→左", "左→右", "上→下", "下→上"],
                                     state="readonly", width=10)
        direction_combo.grid(row=1, column=1, padx=5)
        
        # アニメーション速度（フレーム数）
        ttk.Label(anim_frame, text="フレーム数:").grid(row=2, column=0, sticky=tk.W)
        self.animation_frames = tk.IntVar(value=72)  # 24fps × 3秒 = 72フレーム
        frames_spinbox = ttk.Spinbox(anim_frame, from_=24, to=720, increment=24,
                                     textvariable=self.animation_frames, width=8)
        frames_spinbox.grid(row=2, column=1, padx=5)
        
        # 秒数表示（参考）
        ttk.Label(anim_frame, text="(24fps)").grid(row=2, column=2, sticky=tk.W)
        self.duration_label = ttk.Label(anim_frame, text="= 3.0秒")
        self.duration_label.grid(row=2, column=3, sticky=tk.W, padx=5)
        
        # フレーム数変更時に秒数表示を更新
        self.animation_frames.trace_add('write', self.update_duration_label)
        
        # プレビュー制御
        preview_control_frame = ttk.Frame(anim_frame)
        preview_control_frame.grid(row=3, column=0, columnspan=3, pady=5)
        
        self.play_button = ttk.Button(preview_control_frame, text="▶", command=self.play_animation, width=3)
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.pause_button = ttk.Button(preview_control_frame, text="⏸", command=self.pause_animation, width=3, state='disabled')
        self.pause_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(preview_control_frame, text="⏹", command=self.stop_animation, width=3, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # 進行度スライダー
        progress_frame = ttk.Frame(anim_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(progress_frame, text="進行:").pack(side=tk.LEFT)
        
        self.animation_progress = tk.DoubleVar(value=0.0)
        self.progress_scale = ttk.Scale(progress_frame, from_=0.0, to=1.0, 
                                       variable=self.animation_progress,
                                       orient=tk.HORIZONTAL, length=200,
                                       command=self.on_progress_change)
        self.progress_scale.pack(side=tk.LEFT, padx=5)
        
        # アニメーション時間表示
        self.progress_label = ttk.Label(progress_frame, text="0.0s / 3.0s")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        self.animation_time = 0.0
        self.animation_timer = None
        
        # プレビュー生成ボタンとインポートボタン
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="プレビュー生成", command=self.generate_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="ピクセルマップインポート", command=self.import_pixelmap).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="手動編集をリセット", command=self.reset_manual_positions).pack(side=tk.LEFT, padx=2)
        
        # フレームリスト
        ttk.Label(left_frame, text="フレームリスト:").grid(row=5, column=0, sticky=tk.W, pady=(10, 0))
        
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
        screen_frame = ttk.LabelFrame(left_frame, text="LEDスクリーン設定（拡張版）", padding="5")
        screen_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # === 現在の設定表示エリア（常時表示） ===
        info_frame = ttk.LabelFrame(screen_frame, text="現在の設定", padding="5")
        info_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 行数・列数・総ピクセル数表示
        self.screen_display_label = ttk.Label(info_frame, text="", font=("Arial", 11, "bold"))
        self.screen_display_label.grid(row=0, column=0, columnspan=2, pady=2)
        
        self.total_pixels_label = ttk.Label(info_frame, text="", font=("Arial", 10))
        self.total_pixels_label.grid(row=1, column=0, columnspan=2, pady=2)
        
        # プリセット選択（従来の機能）
        preset_frame = ttk.LabelFrame(screen_frame, text="プリセット", padding="5")
        preset_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.screen_size_var = tk.StringVar(value=self.current_screen_config)
        preset_row = 0
        preset_col = 0
        for i, config_name in enumerate(self.screen_configs.keys()):
            rb = ttk.Radiobutton(preset_frame, text=config_name, 
                               variable=self.screen_size_var, 
                               value=config_name,
                               command=self.update_screen_size)
            rb.grid(row=preset_row, column=preset_col, sticky=tk.W, padx=5, pady=2)
            preset_col += 1
            if preset_col > 2:  # 3列で改行
                preset_col = 0
                preset_row += 1
        
        # === 行数調整エリア ===
        rows_frame = ttk.LabelFrame(screen_frame, text="行数調整", padding="5")
        rows_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        
        # 現在の行数表示
        ttk.Label(rows_frame, text="行数:").grid(row=0, column=0, sticky=tk.W)
        self.custom_rows_var = tk.IntVar(value=10)
        self.rows_display = ttk.Label(rows_frame, textvariable=self.custom_rows_var, font=("Arial", 12, "bold"))
        self.rows_display.grid(row=0, column=1, padx=5)
        
        # 行数追加ボタン（上・下）
        ttk.Button(rows_frame, text="▲上に追加", 
                  command=self.add_row_top, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(rows_frame, text="▼下に追加", 
                  command=self.add_row_bottom, width=10).grid(row=0, column=3, padx=2)
        
        # 行数削除ボタン
        ttk.Button(rows_frame, text="上から削除", 
                  command=self.remove_row_top, width=10).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(rows_frame, text="下から削除", 
                  command=self.remove_row_bottom, width=10).grid(row=1, column=3, padx=2, pady=2)
        
        # 位置リセットボタン
        ttk.Button(rows_frame, text="位置リセット", 
                  command=self.reset_position_adjustment, width=10).grid(row=2, column=2, columnspan=2, padx=2, pady=2)
        
        # === 列数調整エリア ===
        cols_frame = ttk.LabelFrame(screen_frame, text="列数調整", padding="5")
        cols_frame.grid(row=2, column=2, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        # 現在の列数表示
        ttk.Label(cols_frame, text="列数:").grid(row=0, column=0, sticky=tk.W)
        self.custom_cols_var = tk.IntVar(value=65)
        self.cols_display = ttk.Label(cols_frame, textvariable=self.custom_cols_var, font=("Arial", 12, "bold"))
        self.cols_display.grid(row=0, column=1, padx=5)
        
        # 列数追加ボタン（左・右）
        ttk.Button(cols_frame, text="◀左に追加", 
                  command=self.add_col_left, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(cols_frame, text="▶右に追加", 
                  command=self.add_col_right, width=10).grid(row=0, column=3, padx=2)
        
        # 列数削除ボタン
        ttk.Button(cols_frame, text="左から削除", 
                  command=self.remove_col_left, width=10).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(cols_frame, text="右から削除", 
                  command=self.remove_col_right, width=10).grid(row=1, column=3, padx=2, pady=2)
        
        # === 直接入力・その他設定エリア ===
        custom_frame = ttk.LabelFrame(screen_frame, text="詳細設定", padding="5")
        custom_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # 直接入力
        ttk.Label(custom_frame, text="直接入力 - 行数:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(custom_frame, from_=1, to=100, textvariable=self.custom_rows_var, 
                   width=8, command=self.update_screen_display).grid(row=0, column=1, padx=2)
        
        ttk.Label(custom_frame, text="列数:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Spinbox(custom_frame, from_=1, to=200, textvariable=self.custom_cols_var, 
                   width=8, command=self.update_screen_display).grid(row=0, column=3, padx=2)
        
        # ドローン間隔
        ttk.Label(custom_frame, text="ドローン間隔:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.custom_drone_spacing_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(custom_frame, from_=0.5, to=10.0, increment=0.1, textvariable=self.custom_drone_spacing_var, 
                   width=8, command=self.update_screen_display).grid(row=1, column=1, padx=2, pady=(5, 0))
        ttk.Label(custom_frame, text="メートル").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(custom_frame, text="設定適用", command=self.apply_custom_settings).grid(row=1, column=3, padx=5, pady=(5, 0))
        
        # 変数変更時の自動更新設定
        self.custom_rows_var.trace_add('write', lambda *args: self.update_screen_display())
        self.custom_cols_var.trace_add('write', lambda *args: self.update_screen_display())
        self.custom_drone_spacing_var.trace_add('write', lambda *args: self.update_screen_display())
        
        # 初期表示更新
        self.update_screen_display()
        
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
        ttk.Button(button_frame, text="アニメーションエクスポート", command=self.export_animation).pack(side=tk.LEFT, padx=5)
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
        
        # ドラッグ&ドロップ用の変数
        self.dragging_pixel = None  # ドラッグ中のピクセル情報
        self.drag_start_pos = None  # ドラッグ開始位置
        self.manual_pixel_positions = {}  # 手動で移動したピクセルの位置
        
        # マウスイベントのバインド
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
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
            
    def update_color_display(self):
        """色表示を更新"""
        hex_color = f"#{int(self.current_color[0]*255):02x}{int(self.current_color[1]*255):02x}{int(self.current_color[2]*255):02x}"
        self.color_frame.config(bg=hex_color)
    
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
        
        # 手動で移動したピクセル位置をクリア
        self.manual_pixel_positions.clear()
            
        self.current_led_data = self.text_to_led_matrix(text)
        self.update_preview_canvas(self.current_led_data)
        self.status_var.set(f"プレビュー生成完了: {self.current_led_data['width']}×{self.current_led_data['height']}ピクセル")
        
                
    def update_canvas_size(self):
        """キャンバスサイズを更新"""
        if self.current_led_data:
            self.update_preview_canvas(self.current_led_data)
        
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
        if self.current_led_data:
            self.update_preview_canvas(self.current_led_data)
        
    def reset_zoom(self):
        """ズームを100%にリセット"""
        self.zoom_scale = 1.0
        self.zoom_percent_var.set(100)
        if self.current_led_data:
            self.update_preview_canvas(self.current_led_data)
        
    def apply_zoom_percent(self):
        """入力されたパーセンテージでズームを適用"""
        percent = self.zoom_percent_var.get()
        self.zoom_scale = percent / 100.0
        if self.current_led_data:
            self.update_preview_canvas(self.current_led_data)
        
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
            
            # 手動移動を考慮した最終位置を取得
            final_pixels = self.get_final_pixel_positions(led_data)
            
            for pixel in final_pixels:
                pixel_data = {
                    "x": pixel[0],
                    "y": pixel[1],
                    "r": frame["color"][0],
                    "g": frame["color"][1],
                    "b": frame["color"][2]
                }
                
                # カラーマップがある場合は色を上書き
                if led_data.get('color_map') and len(pixel) > 2:
                    color_id = str(pixel[2])
                    if color_id in led_data['color_map']:
                        color_rgb = led_data['color_map'][color_id]
                        if isinstance(color_rgb, (list, tuple)) and len(color_rgb) >= 3:
                            pixel_data["r"] = color_rgb[0]
                            pixel_data["g"] = color_rgb[1]
                            pixel_data["b"] = color_rgb[2]
                
                frame_data["pixels"].append(pixel_data)
                    
            export_data["frames"].append(frame_data)
        
        # JSON保存
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        self.status_var.set(f"JSONエクスポート完了: {filename}")
        
    def export_skybrush_script(self):
        """Skybrush Formation用のBlenderスクリプトをエクスポート
        
        このスクリプトは、BlenderのSkybrush Formationsフォルダに
        LEDスクリーンレイアウトのエンプティを作成します。
        """
        print("export_skybrush_script called")  # デバッグ
        
        # 現在の設定を取得
        if self.screen_size_var.get() == "custom":
            rows = self.custom_rows_var.get()
            cols = self.custom_cols_var.get()
            drone_spacing_m = self.custom_drone_spacing_var.get()
        else:
            config = self.screen_configs[self.screen_size_var.get()]
            rows = config["rows"]
            cols = config["cols"]
            drone_spacing_m = config["drone_spacing_m"]
            
        print(f"Settings: {rows}x{cols}, spacing: {drone_spacing_m}m")  # デバッグ
            
        # デフォルトファイル名
        default_filename = f"skybrush_formation_{rows}x{cols}"
            
        filename = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if not filename:
            print("No filename selected, cancelling export")  # デバッグ
            self.status_var.set("エクスポートがキャンセルされました")
            return
            
        # 座標計算（Blenderでは1単位 = 1メートル）
        total_width = (cols - 1) * drone_spacing_m
        total_height = (rows - 1) * drone_spacing_m
        
        # スクリプトテンプレート
        script_template = '''"""
Skybrush Formation Creation Script - Generated by Font2LED Tool
Grid: {rows} rows x {cols} columns  
Drone Spacing: {drone_spacing_m} meters
Total Size: {total_width:.1f}m x {total_height:.1f}m
"""

import bpy
from mathutils import Vector
from functools import partial

# 必要なコレクションを作成または取得
def ensure_collection_exists(parent, name):
    """指定された親コレクション内にコレクションが存在することを確認"""
    if name in parent.children:
        return parent.children[name]
    else:
        collection = bpy.data.collections.new(name)
        parent.children.link(collection)
        return collection

# Scene CollectionでFormationsフォルダを確保
scene_collection = bpy.context.scene.collection
formations_collection = ensure_collection_exists(scene_collection, "Formations")

# LEDスクリーンフォーメーション名
formation_name = "LED_Screen_{rows}x{cols}"

# 既存のフォーメーションを削除
if formation_name in formations_collection.children:
    old_formation = formations_collection.children[formation_name]
    # 子オブジェクトを削除
    for obj in list(old_formation.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    # コレクション自体を削除
    bpy.data.collections.remove(old_formation)

# 新しいフォーメーションコレクションを作成
formation = bpy.data.collections.new(formation_name)
formations_collection.children.link(formation)

# グリッド設定
rows = {rows}
cols = {cols}
drone_spacing = {drone_spacing_m}

# 中心を原点にするためのオフセット
x_offset = -((cols - 1) * drone_spacing) / 2
y_offset = 0  # 前後方向は0
z_offset = ((rows - 1) * drone_spacing) / 2  # 上が正

# エンプティを作成
empty_count = 0
for row in range(rows):
    for col in range(cols):
        # Skybrush座標系：X=左右、Y=前後、Z=上下
        x = col * drone_spacing + x_offset
        y = y_offset
        z = z_offset - row * drone_spacing  # 上から下へ
        
        # エンプティ名（LED_XX_YY形式）
        empty_name = f"LED_{{{{col+1:02d}}}}_{{{{row+1:02d}}}}"
        
        # エンプティを作成
        empty = bpy.data.objects.new(empty_name, None)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.empty_display_size = 0.5
        empty.location = (x, y, z)
        
        # フォーメーションに追加
        formation.objects.link(empty)
        empty_count += 1

print(f"Created formation '{{formation_name}}' with {{empty_count}} empty objects")
print(f"Grid: {{rows}} rows x {{cols}} columns")
print(f"Spacing: {{drone_spacing}}m")
total_width = (cols - 1) * drone_spacing
total_height = (rows - 1) * drone_spacing
print(f"Total size: {{total_width:.1f}}m x {{total_height:.1f}}m")

# ビューポートで見やすくするため、3Dビューを調整
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                # ビューをリセット
                space.region_3d.view_rotation = (1, 0, 0, 0)
                space.region_3d.view_location = (0, 0, 0)
                # 全体が見えるように距離を調整
                view_distance = max(total_width, total_height) * 1.5
                space.region_3d.view_distance = view_distance
                break
'''
        
        # スクリプト生成
        script_content = script_template.format(
            rows=rows,
            cols=cols,
            drone_spacing_m=drone_spacing_m,
            total_width=total_width,
            total_height=total_height
        )
        
        # ファイル保存
        print(f"Saving to: {filename}")  # デバッグ
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(script_content)
            print(f"File saved successfully")  # デバッグ
            self.status_var.set(f"Skybrushスクリプトエクスポート完了: {filename}")
        except Exception as e:
            print(f"Error saving file: {e}")  # デバッグ
            self.status_var.set(f"エラー: ファイル保存に失敗しました - {str(e)}")
            messagebox.showerror("エラー", f"ファイル保存に失敗しました:\n{str(e)}")
        
    # === 新しい方向指定付き追加・削除メソッド ===
    
    def reset_position_adjustment(self):
        """位置調整をリセット"""
        self.y_offset_adjustment = 0
        self.x_offset_adjustment = 0
        print(f"位置調整をリセット: x_offset = {self.x_offset_adjustment}, y_offset = {self.y_offset_adjustment}")
        self.status_var.set("位置調整をリセットしました")
        self.update_preview_if_exists()
    
    def update_screen_display(self):
        """画面表示情報の更新"""
        rows = self.custom_rows_var.get()
        cols = self.custom_cols_var.get() 
        spacing = self.custom_drone_spacing_var.get()
        total_pixels = rows * cols
        
        # メイン表示更新
        self.screen_display_label.config(text=f"LEDスクリーン: {rows}行 × {cols}列")
        self.total_pixels_label.config(text=f"総ピクセル数: {total_pixels:,}個 | ドローン間隔: {spacing}m")
        
        # 実サイズ計算
        width_m = (cols - 1) * spacing
        height_m = (rows - 1) * spacing
        area_m2 = width_m * height_m
        
        # 右パネルのタイトル更新
        if hasattr(self, 'right_frame'):
            self.right_frame.config(text=f"LEDスクリーン ({rows}行×{cols}列) - {total_pixels:,}ピクセル")
    
    def add_row_top(self):
        """上に1行追加 - テキストを下にシフトして上に空白行を追加"""
        current = self.custom_rows_var.get()
        self.custom_rows_var.set(current + 1)
        # 上に行を追加 = テキストを下にシフトさせる
        self.y_offset_adjustment += 1
        print(f"上に1行追加: {current} → {current + 1} (y_offset: {self.y_offset_adjustment})")
        self.status_var.set(f"上に1行追加: {current + 1}行")
        self.update_preview_if_exists()
    
    def add_row_bottom(self):
        """下に1行追加 - 下に空白行を追加（テキスト位置は変わらない）"""
        current = self.custom_rows_var.get()
        self.custom_rows_var.set(current + 1)
        # y_offset_adjustmentは変更しない（テキスト位置維持）
        print(f"下に1行追加: {current} → {current + 1} (y_offset: {self.y_offset_adjustment})")
        self.status_var.set(f"下に1行追加: {current + 1}行 (テキスト位置維持)")
        self.update_preview_if_exists()
    
    def remove_row_top(self):
        """上から1行削除 - 上の行を削除（テキストは相対的に上にシフト）"""
        current = self.custom_rows_var.get()
        if current > 1:
            self.custom_rows_var.set(current - 1)
            # 上の行を削除 = テキストを上にシフトさせる
            self.y_offset_adjustment = max(0, self.y_offset_adjustment - 1)
            print(f"上から1行削除: {current} → {current - 1} (y_offset: {self.y_offset_adjustment})")
            self.status_var.set(f"上から1行削除: {current - 1}行")
            self.update_preview_if_exists()
    
    def remove_row_bottom(self):
        """下から1行削除 - 下の空白行を削除（テキスト位置は変わらない）"""
        current = self.custom_rows_var.get()
        if current > 1:
            self.custom_rows_var.set(current - 1)
            # y_offset_adjustmentは変更しない（テキスト位置維持）
            print(f"下から1行削除: {current} → {current - 1} (y_offset: {self.y_offset_adjustment})")
            self.status_var.set(f"下から1行削除: {current - 1}行 (テキスト位置維持)")
            self.update_preview_if_exists()
    
    def update_preview_if_exists(self):
        """現在のLEDデータが存在する場合、プレビューを更新"""
        if hasattr(self, 'current_led_data') and self.current_led_data:
            self.update_preview_canvas(self.current_led_data)
    
    def add_col_left(self):
        """左に1列追加 - 左側に空白列を追加（テキストを右にシフト）"""
        if hasattr(self, 'button_operation_lock') and self.button_operation_lock:
            print("左に1列追加: 操作ロック中、無視")
            return
        
        current = self.custom_cols_var.get()
        
        # 中央配置の変化を計算
        if hasattr(self, 'current_led_data') and self.current_led_data:
            text_width = self.current_led_data['width']
            old_center = (current - text_width) // 2
            new_center = (current + 1 - text_width) // 2
            center_shift = new_center - old_center
        else:
            center_shift = 0
        
        self.custom_cols_var.set(current + 1)
        # 左に列を追加 = テキストを右にシフトさせる
        # ただし、中央配置の自動シフトを相殺する
        self.x_offset_adjustment = self.x_offset_adjustment + 1 - center_shift
        
        print(f"左に1列追加: {current} → {current + 1} (x_offset: {self.x_offset_adjustment})")
        self.status_var.set(f"左に1列追加: {current + 1}列 (左側に空白追加)")
        self.update_preview_if_exists()
    
    def add_col_right(self):
        """右に1列追加 - 右側に空白列を追加（テキスト位置は維持）"""
        if hasattr(self, 'button_operation_lock') and self.button_operation_lock:
            print("右に1列追加: 操作ロック中、無視")
            return
        
        current = self.custom_cols_var.get()
        
        # 中央配置の変化を計算
        if hasattr(self, 'current_led_data') and self.current_led_data:
            text_width = self.current_led_data['width']
            old_center = (current - text_width) // 2
            new_center = (current + 1 - text_width) // 2
            center_shift = new_center - old_center
        else:
            center_shift = 0
        
        self.custom_cols_var.set(current + 1)
        # 右に列を追加する場合、位置を維持するため中央配置の変化を相殺
        self.x_offset_adjustment = self.x_offset_adjustment - center_shift
        
        print(f"右に1列追加: {current} → {current + 1} (x_offset: {self.x_offset_adjustment})")
        self.status_var.set(f"右に1列追加: {current + 1}列 (右側に空白追加)")
        self.update_preview_if_exists()
    
    def remove_col_left(self):
        """左から1列削除 - 左側の列を削除（テキストを左にシフト）"""
        current = self.custom_cols_var.get()
        if current > 1:
            # 中央配置の変化を計算
            if hasattr(self, 'current_led_data') and self.current_led_data:
                text_width = self.current_led_data['width']
                old_center = (current - text_width) // 2
                new_center = (current - 1 - text_width) // 2
                center_shift = new_center - old_center
            else:
                center_shift = 0
                
            self.custom_cols_var.set(current - 1)
            # 左の列を削除 = テキストを左にシフトさせる
            # ただし、中央配置の自動シフトを相殺する
            self.x_offset_adjustment = self.x_offset_adjustment - 1 - center_shift
            
            print(f"左から1列削除: {current} → {current - 1} (x_offset: {self.x_offset_adjustment})")
            self.status_var.set(f"左から1列削除: {current - 1}列")
            self.update_preview_if_exists()
    
    def remove_col_right(self):
        """右から1列削除 - 右側の列を削除（テキスト位置は維持）"""
        current = self.custom_cols_var.get()
        if current > 1:
            # 中央配置の変化を計算
            if hasattr(self, 'current_led_data') and self.current_led_data:
                text_width = self.current_led_data['width']
                old_center = (current - text_width) // 2
                new_center = (current - 1 - text_width) // 2
                center_shift = new_center - old_center
            else:
                center_shift = 0
                
            self.custom_cols_var.set(current - 1)
            # 右の列を削除する場合、位置を維持するため中央配置の変化を相殺
            self.x_offset_adjustment = self.x_offset_adjustment - center_shift
            
            print(f"右から1列削除: {current} → {current - 1} (x_offset: {self.x_offset_adjustment})")
            self.status_var.set(f"右から1列削除: {current - 1}列 (右側から削除)")
            self.update_preview_if_exists()
        
    def apply_custom_settings(self):
        """カスタム設定を適用"""
        rows = self.custom_rows_var.get()
        cols = self.custom_cols_var.get()
        spacing = self.custom_drone_spacing_var.get()
        
        # カスタム設定を更新
        self.screen_configs["カスタム"] = {
            "rows": rows,
            "cols": cols,
            "spacing": 30,  # GUI表示用のピクセル間隔は固定
            "drone_spacing_m": spacing  # メートル単位
        }
        
        # カスタムを選択
        self.screen_size_var.set("カスタム")
        self.update_screen_size()
        
        # 表示情報更新
        self.update_screen_display()
        
        total_pixels = rows * cols
        self.status_var.set(f"カスタム設定適用: {rows}×{cols}列 ({total_pixels:,}ピクセル), 間隔{spacing}m")
        
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
            x_offset = (config["cols"] - led_data["width"]) // 2 + self.x_offset_adjustment  # 水平方向のセンタリング + x_offset調整
            # 行数が足りない場合は下が切れるように、上から配置 + y_offset調整を適用
            y_offset = 0 + self.y_offset_adjustment
            
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
            
        # 現在の設定を取得（カスタム設定に対応）
        if self.screen_size_var.get() == "custom":
            rows = self.custom_rows_var.get()
            cols = self.custom_cols_var.get()
        else:
            config = self.screen_configs[self.screen_size_var.get()]
            rows = config["rows"]
            cols = config["cols"]
            
        # ピクセルデータを収集（中央配置を適用）
        pixels_data = []
        for frame in self.frames:
            led_data = frame["led_data"]
            x_offset = (cols - led_data["width"]) // 2 + self.x_offset_adjustment  # 水平方向のセンタリング + x_offset調整
            # 行数が足りない場合は下が切れるように、上から配置 + y_offset調整を適用
            y_offset = 0 + self.y_offset_adjustment
            
            for x, y in led_data["pixels"]:
                adjusted_x = x + x_offset
                adjusted_y = y + y_offset
                if 0 <= adjusted_x < cols and 0 <= adjusted_y < rows:
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

    def update_duration_label(self, *args):
        """フレーム数から秒数を計算して表示"""
        frames = self.animation_frames.get()
        seconds = frames / 24.0  # 24fps
        self.duration_label.config(text=f"= {seconds:.1f}秒")
    
    def toggle_animation(self):
        """アニメーション有効/無効の切り替え"""
        if self.animation_enabled.get():
            self.status_var.set("アニメーション有効化")
        else:
            self.stop_animation()
            self.status_var.set("アニメーション無効化")
    
    def play_animation(self):
        """アニメーション再生開始"""
        if not self.current_led_data:
            messagebox.showwarning("警告", "プレビューを生成してからアニメーションを再生してください")
            return
            
        if not self.animation_enabled.get():
            messagebox.showwarning("警告", "アニメーション有効にチェックを入れてください")
            return
        
        self.animation_running = True
        self.animation_paused = False
        self.animation_current_frame = 0  # フレームベースで管理
        self.play_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        
        self.animate_frame()
        self.status_var.set("アニメーション再生中...")
    
    def pause_animation(self):
        """アニメーション一時停止"""
        if self.animation_running and not self.animation_paused:
            self.animation_paused = True
            import time
            self.animation_pause_time = time.time() * 1000
            self.play_button.config(state='normal', text="▶")
            self.pause_button.config(state='disabled')
            self.status_var.set("アニメーション一時停止")
        elif self.animation_paused:
            # 再開
            import time
            pause_duration = time.time() * 1000 - self.animation_pause_time
            self.animation_start_time += pause_duration
            self.animation_paused = False
            self.play_button.config(state='disabled')
            self.pause_button.config(state='normal')
            self.animate_frame()
            self.status_var.set("アニメーション再開")
    
    def stop_animation(self):
        """アニメーション停止"""
        self.animation_running = False
        self.animation_paused = False
        self.animation_progress.set(0.0)
        self.play_button.config(state='normal', text="▶")
        self.pause_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        
        # 初期フレームに戻す
        if self.current_led_data:
            self.update_preview_canvas(self.current_led_data, 0.0)
        
        total_frames = self.animation_frames.get()
        self.progress_label.config(text=f"0 / {total_frames} frames")
        self.status_var.set("アニメーション停止")
    
    def animate_frame(self):
        """アニメーションフレームの更新"""
        if not self.animation_running or self.animation_paused:
            return
        
        total_frames = self.animation_frames.get()
        
        if self.animation_current_frame >= total_frames:
            # アニメーション完了
            self.stop_animation()
            return
        
        # 進行度計算（0.0-1.0）
        time_fraction = self.animation_current_frame / float(total_frames)
        self.animation_progress.set(time_fraction)
        self.progress_label.config(text=f"{self.animation_current_frame} / {total_frames} frames")
        
        # アニメーションフレームをプレビューに反映
        self.update_preview_canvas(self.current_led_data, time_fraction)
        
        # 次のフレームに進む
        self.animation_current_frame += 1
        
        # 次のフレームをスケジュール（24fps）
        self.root.after(42, self.animate_frame)  # 1000ms / 24fps = 41.67ms ≈ 42ms
    
    def on_progress_change(self, event=None):
        """進行度スライダーの変更"""
        if self.animation_running and not self.animation_paused:
            return  # 再生中は手動変更を無視
        
        if self.current_led_data:
            time_fraction = self.animation_progress.get()
            total_frames = self.animation_frames.get()
            current_frame = int(time_fraction * total_frames)
            self.progress_label.config(text=f"{current_frame} / {total_frames} frames")
            self.update_preview_canvas(self.current_led_data, time_fraction)
    
    def update_preview_canvas(self, led_data, time_fraction=0.0):
        """プレビューキャンバスを更新（アニメーション対応）"""
        # 実際のカスタム設定値を使用
        config = {
            "rows": self.custom_rows_var.get(),
            "cols": self.custom_cols_var.get(),
            "spacing": 30,  # プレビュー表示用の固定値
            "drone_spacing_m": self.custom_drone_spacing_var.get()
        }
        
        # ズーム対応のスペーシング計算
        spacing = int(config["spacing"] * self.zoom_scale)
        canvas_width = config["cols"] * spacing
        canvas_height = config["rows"] * spacing
        
        # キャンバスのスクロール領域を設定
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # キャンバスをクリア
        self.canvas.delete("all")
        
        
        # すべてのLED位置を描画（消灯状態）
        led_size = max(4, int(spacing // 4))
        for row in range(config["rows"]):
            for col in range(config["cols"]):
                center_x = col * spacing + spacing // 2
                center_y = row * spacing + spacing // 2
                
                # LED球体（消灯時は暗いグレー）
                x1 = center_x - led_size // 2
                y1 = center_y - led_size // 2
                x2 = center_x + led_size // 2
                y2 = center_y + led_size // 2
                
                self.canvas.create_oval(x1, y1, x2, y2, fill="#202020", outline="#404040", width=1)
        
        # LEDドット描画（アニメーション適用）
        if self.animation_enabled.get() and time_fraction > 0:
            animated_pixels = self.calculate_animated_pixels(led_data, time_fraction)
        else:
            animated_pixels = led_data["pixels"]
        
        # 中央配置のオフセット計算 + x_offset/y_offset調整を適用
        x_offset = (config["cols"] - led_data["width"]) // 2 + self.x_offset_adjustment
        # 行数が足りない場合は下が切れるように、上から配置 + y_offset調整を適用
        y_offset = 0 + self.y_offset_adjustment
        
        # カラーマップの取得
        color_map = led_data.get('color_map', {})
        
        # ピクセルごとに描画
        for i, pixel_data in enumerate(animated_pixels):
            # 座標を取得
            if isinstance(pixel_data, (list, tuple)):
                x, y = pixel_data[0], pixel_data[1]
            else:
                continue
            
            # 手動で移動したピクセルの位置を確認
            if i in self.manual_pixel_positions:
                led_x, led_y = self.manual_pixel_positions[i]
            else:
                led_x = x + x_offset
                led_y = y + y_offset
            
            if 0 <= led_x < config["cols"] and 0 <= led_y < config["rows"]:
                center_x = led_x * spacing + spacing // 2
                
                # 色を決定
                if color_map and i < len(led_data['pixels']) and len(led_data['pixels'][i]) > 2:
                    # カラーマップから色を取得
                    color_id = str(led_data['pixels'][i][2])
                    if color_id in color_map:
                        color_rgb = color_map[color_id]
                        if isinstance(color_rgb, (list, tuple)) and len(color_rgb) >= 3:
                            color = (color_rgb[0], color_rgb[1], color_rgb[2])
                        else:
                            color = self.current_color
                    else:
                        color = self.current_color
                else:
                    # デフォルトカラー
                    color = self.current_color
                
                # RGB(0.0-1.0)から16進数カラーコードに変換
                hex_color = f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
                
                # 明るい色（エミッション効果）
                bright_hex = f"#{min(255, int(color[0]*255*1.3)):02x}{min(255, int(color[1]*255*1.3)):02x}{min(255, int(color[2]*255*1.3)):02x}"
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
                
                # ドラッグ中のピクセルはハイライト表示
                if self.dragging_pixel and self.dragging_pixel['index'] == i:
                    self.canvas.create_oval(gx1-2, gy1-2, gx2+2, gy2+2, fill="", outline="yellow", width=3)
                    self.canvas.create_oval(gx1, gy1, gx2, gy2, fill="", outline=hex_color, width=2)
                else:
                    self.canvas.create_oval(gx1, gy1, gx2, gy2, fill="", outline=hex_color, width=2)
                self.canvas.create_oval(x1, y1, x2, y2, fill=bright_hex, outline=hex_color, width=2)
    
    def calculate_animated_pixels(self, led_data, time_fraction):
        """アニメーション適用後のピクセル座標を計算"""
        direction = self.animation_direction.get()
        original_pixels = led_data["pixels"]
        config = self.screen_configs[self.screen_size_var.get()]
        
        animated_pixels = []
        
        if direction == "右→左":
            # 右から左へのスクロール
            scroll_distance = config["cols"] + led_data["width"] + 10  # 余裕を持たせる
            # time_fraction = 0: 右端外側、time_fraction = 1: 左端外側
            offset_x = int(scroll_distance * (1 - time_fraction)) - led_data["width"] - 5
            
            for x, y in original_pixels:
                new_x = x + offset_x
                if -20 <= new_x < config["cols"] + 20:  # 広い範囲で表示
                    animated_pixels.append((new_x, y))
                    
        elif direction == "左→右":
            # 左から右へのスクロール
            scroll_distance = config["cols"] + led_data["width"] + 10
            # time_fraction = 0: 左端外側、time_fraction = 1: 右端外側
            offset_x = int(scroll_distance * time_fraction) - led_data["width"] - 5
            
            for x, y in original_pixels:
                new_x = x + offset_x
                if -20 <= new_x < config["cols"] + 20:
                    animated_pixels.append((new_x, y))
                    
        elif direction == "上→下":
            # 上から下へのスクロール
            scroll_distance = config["rows"] + led_data["height"] + 5
            offset_y = int(scroll_distance * time_fraction) - led_data["height"] - 3
            
            for x, y in original_pixels:
                new_y = y + offset_y
                if -10 <= new_y < config["rows"] + 10:
                    animated_pixels.append((x, new_y))
                    
        elif direction == "下→上":
            # 下から上へのスクロール
            scroll_distance = config["rows"] + led_data["height"] + 5
            offset_y = int(scroll_distance * (1 - time_fraction)) - led_data["height"] - 3
            
            for x, y in original_pixels:
                new_y = y + offset_y
                if -10 <= new_y < config["rows"] + 10:
                    animated_pixels.append((x, new_y))
        return animated_pixels
    
    def export_animation(self):
        """アニメーション付きCustom Expressionをエクスポート"""
        if not self.current_led_data:
            messagebox.showwarning("警告", "プレビューを生成してからエクスポートしてください")
            return
        
        if not self.animation_enabled.get():
            messagebox.showwarning("警告", "アニメーション有効にしてからエクスポートしてください")
            return
        
        # ファイル名の生成
        text = self.text_var.get() or "animation"
        direction_map = {"右→左": "scroll_right_to_left", "左→右": "scroll_left_to_right", 
                        "上→下": "scroll_top_to_bottom", "下→上": "scroll_bottom_to_top"}
        direction_name = direction_map.get(self.animation_direction.get(), "scroll")
        default_filename = f"animated_{text}_{direction_name}"
        
        filename = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        # アニメーション用テンプレートを生成
        config = self.screen_configs[self.screen_size_var.get()]
        direction = self.animation_direction.get()
        total_frames = self.animation_frames.get()
        duration_seconds = total_frames / 24.0  # 24fps
        
        # ピクセルデータをタプル形式に変換
        pixels_str = "{\n"
        for i, (x, y) in enumerate(self.current_led_data["pixels"]):
            if i > 0 and i % 8 == 0:
                pixels_str += "\n"
            pixels_str += f"({x},{y}), "
        pixels_str = pixels_str.rstrip(", ") + "\n}"
        
        script_content = f'''# Skybrush Custom Expression Function - アニメーション版
# Generated by Font2LED Tool - Animation Export
# Text: {self.text_var.get()} ({direction}、{total_frames}フレーム = {duration_seconds:.1f}秒 @ 24fps)
#
# 【重要】Blenderでの設定方法:
# 1. Light Effectsパネルで新しいエフェクトを追加
# 2. Type: COLOR_RAMP, Output: FUNCTION (Script)
# 3. Frame範囲を設定:
#    - 開始フレーム: 任意（例: 1）
#    - 終了フレーム: 開始フレーム + {total_frames}
#    - 例: Frame 1-{total_frames + 1} で{total_frames}フレームのアニメーション
# 4. このスクリプトをFunction欄に貼り付け

# グリッドサイズ設定
GRID_WIDTH = {config["cols"]}
GRID_HEIGHT = {config["rows"]}

# 座標範囲（ドローン配置設定に基づく動的計算）
# グリッド: {config["cols"]}列×{config["rows"]}行、間隔: {config["drone_spacing_m"]}m
DRONE_SPACING = {config["drone_spacing_m"]}  # ドローン間隔(m)
X_MIN = -(GRID_WIDTH - 1) * DRONE_SPACING / 2
X_MAX = (GRID_WIDTH - 1) * DRONE_SPACING / 2
Z_MIN = -(GRID_HEIGHT - 1) * DRONE_SPACING / 2
Z_MAX = (GRID_HEIGHT - 1) * DRONE_SPACING / 2

# アニメーション設定
ANIMATION_FRAMES = {total_frames}  # 総フレーム数
ANIMATION_DURATION = {duration_seconds:.1f}  # 秒数（{total_frames}フレーム ÷ 24fps）
ANIMATION_DIRECTION = "{direction}"

# ピクセルデータ（Grid座標）- Font2LED Tool出力
PIXELS = {pixels_str}

def animated_{text.replace(' ', '_')}_{direction_name}(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """
    {direction}アニメーション - "{self.text_var.get()}"
    
    Args:
        frame: フレーム番号
        time_fraction: 時間進行度（0.0-1.0）
                      ※Skybrushが自動計算: (現在frame - 開始frame) / (終了frame - 開始frame)
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
        # X軸: グリッド列 (0-{config["cols"]-1})
        grid_x = int(round((x_pos - X_MIN) / (X_MAX - X_MIN) * (GRID_WIDTH - 1)))
        
        # Z軸: グリッド行 (0-{config["rows"]-1})、上下反転
        grid_z = int(round((z_pos - Z_MIN) / (Z_MAX - Z_MIN) * (GRID_HEIGHT - 1)))
        grid_z = {config["rows"]-1} - grid_z  # 上下反転
        
        # アニメーション計算: {direction}
        {self._generate_animation_logic(direction, config)}
        
        # 範囲チェック
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_z < GRID_HEIGHT:
            # アニメーション適用：元のピクセル座標をオフセット分調整
            for pixel_x, pixel_z in PIXELS:
                # ピクセルのアニメーション後の座標
                animated_pixel_x = pixel_x + animated_x_offset
                animated_pixel_z = pixel_z + animated_z_offset
                
                # 現在のドローン位置と一致するかチェック
                if (abs(animated_pixel_x - grid_x) < 0.5 and 
                    abs(animated_pixel_z - grid_z) < 0.5):
                    return 1.0  # 文字部分（Color Rampで色に変換）
        
        return 0.0  # 背景（黒）
    else:
        return 0.0  # エラー時（黒）
'''
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.status_var.set(f"アニメーションエクスポート完了: {os.path.basename(filename)}")
            messagebox.showinfo("エクスポート完了", 
                              f"アニメーション付きCustom Expressionをエクスポートしました:\\n{filename}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル保存エラー: {e}")
    
    def _generate_animation_logic(self, direction, config):
        """アニメーションロジックのコード生成"""
        if direction == "右→左":
            return f'''        # 右から左へのスクロール
        scroll_distance = GRID_WIDTH + {self.current_led_data["width"]}
        animated_x_offset = int(scroll_distance * (1 - time_fraction)) - {self.current_led_data["width"]}
        animated_z_offset = 0'''
        elif direction == "左→右":
            return f'''        # 左から右へのスクロール
        scroll_distance = GRID_WIDTH + {self.current_led_data["width"]}
        animated_x_offset = int(scroll_distance * time_fraction) - {self.current_led_data["width"]}
        animated_z_offset = 0'''
        elif direction == "上→下":
            return f'''        # 上から下へのスクロール
        scroll_distance = GRID_HEIGHT + {self.current_led_data["height"]}
        animated_z_offset = int(scroll_distance * time_fraction) - {self.current_led_data["height"]}
        animated_x_offset = 0'''
        elif direction == "下→上":
            return f'''        # 下から上へのスクロール
        scroll_distance = GRID_HEIGHT + {self.current_led_data["height"]}
        animated_z_offset = int(scroll_distance * (1 - time_fraction)) - {self.current_led_data["height"]}
        animated_x_offset = 0'''

    def import_pixelmap(self):
        """ピクセルマップファイルをインポート"""
        filename = filedialog.askopenfilename(
            title="ピクセルマップファイルを選択",
            filetypes=[
                ("対応ファイル", "*.html;*.htm;*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.txt;*.json"),
                ("HTMLファイル", "*.html;*.htm"),
                ("画像ファイル", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("テキストファイル", "*.txt"),
                ("JSONファイル", "*.json"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            # パーサーを使用してファイルを解析
            parser = PixelMapParser()
            pixelmap_data = parser.parse_file(filename)
            
            # インポートしたデータをLED形式に変換
            led_data = self._pixelmap_to_led_data(pixelmap_data)
            
            # 現在のLEDデータとして設定
            self.current_led_data = led_data
            
            # テキスト入力欄を更新
            self.text_var.set(f"Import: {os.path.basename(filename)}")
            
            # 色が1つだけの場合は現在の色として設定
            if len(pixelmap_data.get('colors', {})) == 1:
                color_values = list(pixelmap_data['colors'].values())
                if color_values:
                    self.current_color = color_values[0]
                    self.update_color_display()
            
            # プレビューを更新
            self.update_preview_canvas(led_data)
            
            # ステータス更新
            self.status_var.set(f"ピクセルマップインポート完了: {os.path.basename(filename)} ({led_data['width']}x{led_data['height']})")
            
            # 複数色の場合は情報を表示
            if len(pixelmap_data.get('colors', {})) > 1:
                color_info = f"インポートされた色数: {len(pixelmap_data['colors'])}色\n"
                for color_id, rgb in pixelmap_data['colors'].items():
                    color_info += f"  色{color_id}: RGB({rgb[0]:.2f}, {rgb[1]:.2f}, {rgb[2]:.2f})\n"
                messagebox.showinfo("色情報", color_info)
                
        except Exception as e:
            messagebox.showerror("インポートエラー", f"ファイルのインポートに失敗しました:\n{str(e)}")
    
    def _pixelmap_to_led_data(self, pixelmap_data):
        """ピクセルマップデータをLED形式に変換"""
        width = pixelmap_data['width']
        height = pixelmap_data['height']
        
        # Font2LED形式のLEDデータを作成
        led_data = {
            'width': width,
            'height': height,
            'pixels': []
        }
        
        # ピクセルデータを変換
        if isinstance(pixelmap_data['pixels'], list) and len(pixelmap_data['pixels']) > 0:
            if isinstance(pixelmap_data['pixels'][0], dict):
                # 辞書形式の場合（カラー情報付き）
                led_data['color_map'] = pixelmap_data.get('colors', {})
                for pixel in pixelmap_data['pixels']:
                    led_data['pixels'].append((pixel['x'], pixel['y'], pixel.get('color_id', 1)))
            else:
                # タプル形式の場合（座標のみ）
                for pixel in pixelmap_data['pixels']:
                    if isinstance(pixel, (list, tuple)) and len(pixel) >= 2:
                        led_data['pixels'].append((pixel[0], pixel[1]))
        
        return led_data
    
    
    def on_closing(self):
        """アプリケーション終了時のクリーンアップ"""
        # アニメーション停止
        self.stop_animation()
        
        try:
            # 一時フォントディレクトリのクリーンアップ
            if self.temp_font_dir and os.path.exists(self.temp_font_dir):
                shutil.rmtree(self.temp_font_dir)
                print(f"一時ディレクトリをクリーンアップ: {self.temp_font_dir}")
        except Exception as e:
            print(f"クリーンアップエラー: {e}")
        finally:
            self.root.destroy()
    
    def on_canvas_click(self, event):
        """キャンバスクリックイベント"""
        if not self.current_led_data:
            return
        
        # スクロール位置を考慮した実際の座標
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # グリッド設定
        config = {
            "rows": self.custom_rows_var.get(),
            "cols": self.custom_cols_var.get(),
            "spacing": 30,
            "drone_spacing_m": self.custom_drone_spacing_var.get()
        }
        spacing = int(config["spacing"] * self.zoom_scale)
        
        # クリック位置のグリッド座標を計算
        grid_x = int(canvas_x // spacing)
        grid_y = int(canvas_y // spacing)
        
        # 点灯しているピクセルか確認
        x_offset = (config["cols"] - self.current_led_data["width"]) // 2 + self.x_offset_adjustment
        y_offset = 0 + self.y_offset_adjustment
        
        # アニメーション中の位置も考慮
        time_fraction = self.animation_progress.get() if self.animation_enabled.get() else 0.0
        if self.animation_enabled.get() and time_fraction > 0:
            animated_pixels = self.calculate_animated_pixels(self.current_led_data, time_fraction)
        else:
            animated_pixels = self.current_led_data["pixels"]
        
        # クリック位置に点灯ピクセルがあるか確認
        for i, pixel_data in enumerate(animated_pixels):
            if isinstance(pixel_data, (list, tuple)):
                x, y = pixel_data[0], pixel_data[1]
                
                # 手動で移動したピクセルの位置を確認
                if i in self.manual_pixel_positions:
                    led_x, led_y = self.manual_pixel_positions[i]
                else:
                    led_x = x + x_offset
                    led_y = y + y_offset
                
                if led_x == grid_x and led_y == grid_y:
                    # このピクセルをドラッグ開始
                    self.dragging_pixel = {
                        'index': i,
                        'original_x': x,
                        'original_y': y,
                        'current_grid_x': led_x,
                        'current_grid_y': led_y
                    }
                    self.drag_start_pos = (canvas_x, canvas_y)
                    break
    
    def on_canvas_drag(self, event):
        """キャンバスドラッグイベント"""
        if not self.dragging_pixel:
            return
        
        # スクロール位置を考慮した実際の座標
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # グリッド設定
        config = {
            "rows": self.custom_rows_var.get(),
            "cols": self.custom_cols_var.get(),
            "spacing": 30,
            "drone_spacing_m": self.custom_drone_spacing_var.get()
        }
        spacing = int(config["spacing"] * self.zoom_scale)
        
        # 新しいグリッド座標を計算
        new_grid_x = int(canvas_x // spacing)
        new_grid_y = int(canvas_y // spacing)
        
        # グリッド範囲内に制限
        new_grid_x = max(0, min(config["cols"] - 1, new_grid_x))
        new_grid_y = max(0, min(config["rows"] - 1, new_grid_y))
        
        # ピクセル位置を更新
        if (new_grid_x != self.dragging_pixel['current_grid_x'] or 
            new_grid_y != self.dragging_pixel['current_grid_y']):
            self.dragging_pixel['current_grid_x'] = new_grid_x
            self.dragging_pixel['current_grid_y'] = new_grid_y
            
            # 手動位置を記録
            self.manual_pixel_positions[self.dragging_pixel['index']] = (new_grid_x, new_grid_y)
            
            # キャンバスを再描画
            time_fraction = self.animation_progress.get() if self.animation_enabled.get() else 0.0
            self.update_preview_canvas(self.current_led_data, time_fraction)
    
    def on_canvas_release(self, event):
        """キャンバスマウスリリースイベント"""
        if self.dragging_pixel:
            self.status_var.set(f"ピクセルを移動しました: ({self.dragging_pixel['current_grid_x']}, {self.dragging_pixel['current_grid_y']})")
        self.dragging_pixel = None
        self.drag_start_pos = None
    
    def get_final_pixel_positions(self, led_data):
        """手動移動を考慮した最終的なピクセル位置を取得"""
        config = {
            "cols": self.custom_cols_var.get(),
            "rows": self.custom_rows_var.get()
        }
        
        # オフセット計算
        x_offset = (config["cols"] - led_data["width"]) // 2 + self.x_offset_adjustment
        y_offset = 0 + self.y_offset_adjustment
        
        final_pixels = []
        for i, pixel_data in enumerate(led_data["pixels"]):
            if isinstance(pixel_data, (list, tuple)):
                x, y = pixel_data[0], pixel_data[1]
                
                # 手動で移動した位置があればそれを使用
                if i in self.manual_pixel_positions:
                    led_x, led_y = self.manual_pixel_positions[i]
                else:
                    led_x = x + x_offset
                    led_y = y + y_offset
                
                # グリッド範囲内のピクセルのみ追加
                if 0 <= led_x < config["cols"] and 0 <= led_y < config["rows"]:
                    # カラー情報も含める
                    if len(pixel_data) > 2:
                        final_pixels.append((led_x, led_y, pixel_data[2]))
                    else:
                        final_pixels.append((led_x, led_y))
        
        return final_pixels
    
    def reset_manual_positions(self):
        """手動編集位置をリセット"""
        self.manual_pixel_positions.clear()
        if self.current_led_data:
            time_fraction = self.animation_progress.get() if self.animation_enabled.get() else 0.0
            self.update_preview_canvas(self.current_led_data, time_fraction)
            self.status_var.set("手動編集位置をリセットしました")

def main():
    root = tk.Tk()
    app = Font2LEDApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()