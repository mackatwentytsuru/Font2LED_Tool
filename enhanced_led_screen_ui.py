#!/usr/bin/env python3
"""
LED画面設定UI拡張版
- 方向指定付き行数・列数追加ボタン
- リアルタイム行数・列数表示
- より直感的なユーザーインターフェース
"""

import tkinter as tk
from tkinter import ttk

class EnhancedLEDScreenSettings:
    def __init__(self, parent_frame, app_instance):
        self.parent_frame = parent_frame
        self.app = app_instance
        
        # スクリーン設定の変数
        self.current_rows = tk.IntVar(value=10)
        self.current_cols = tk.IntVar(value=65)
        self.current_spacing = tk.DoubleVar(value=2.0)
        
        # UI構築
        self.setup_enhanced_screen_ui()
        
        # 初期表示更新
        self.update_display_info()
    
    def setup_enhanced_screen_ui(self):
        """拡張されたLEDスクリーン設定UIの構築"""
        
        # メインフレーム
        screen_frame = ttk.LabelFrame(self.parent_frame, text="LEDスクリーン設定（拡張版）", padding="10")
        screen_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # === 現在の設定表示エリア（常時表示） ===
        info_frame = ttk.LabelFrame(screen_frame, text="現在の設定", padding="5")
        info_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 行数・列数表示
        self.display_label = ttk.Label(info_frame, text="", font=("Arial", 11, "bold"))
        self.display_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # 総LED数表示
        self.total_leds_label = ttk.Label(info_frame, text="", font=("Arial", 10))
        self.total_leds_label.grid(row=1, column=0, columnspan=2, pady=2)
        
        # === 行数調整エリア ===
        rows_frame = ttk.LabelFrame(screen_frame, text="行数調整", padding="5")
        rows_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        
        # 行数表示と調整ボタン
        ttk.Label(rows_frame, text="行数:").grid(row=0, column=0, sticky=tk.W)
        self.rows_display = ttk.Label(rows_frame, text="10", font=("Arial", 12, "bold"))
        self.rows_display.grid(row=0, column=1, padx=5)
        
        # 行数追加ボタン（上・下）
        ttk.Button(rows_frame, text="▲ 上に1行追加", 
                  command=self.add_row_top, width=12).grid(row=0, column=2, padx=2)
        ttk.Button(rows_frame, text="▼ 下に1行追加", 
                  command=self.add_row_bottom, width=12).grid(row=0, column=3, padx=2)
        
        # 行数削除ボタン
        ttk.Button(rows_frame, text="上から1行削除", 
                  command=self.remove_row_top, width=12).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(rows_frame, text="下から1行削除", 
                  command=self.remove_row_bottom, width=12).grid(row=1, column=3, padx=2, pady=2)
        
        # 複数行追加
        ttk.Label(rows_frame, text="複数追加:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.rows_bulk_var = tk.IntVar(value=5)
        ttk.Spinbox(rows_frame, from_=2, to=20, textvariable=self.rows_bulk_var, width=5).grid(row=2, column=1, pady=(5, 0))
        ttk.Button(rows_frame, text="▲ 上に追加", 
                  command=self.add_rows_top_bulk, width=12).grid(row=2, column=2, padx=2, pady=(5, 0))
        ttk.Button(rows_frame, text="▼ 下に追加", 
                  command=self.add_rows_bottom_bulk, width=12).grid(row=2, column=3, padx=2, pady=(5, 0))
        
        # === 列数調整エリア ===
        cols_frame = ttk.LabelFrame(screen_frame, text="列数調整", padding="5")
        cols_frame.grid(row=1, column=2, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        # 列数表示と調整ボタン
        ttk.Label(cols_frame, text="列数:").grid(row=0, column=0, sticky=tk.W)
        self.cols_display = ttk.Label(cols_frame, text="65", font=("Arial", 12, "bold"))
        self.cols_display.grid(row=0, column=1, padx=5)
        
        # 列数追加ボタン（左・右）
        ttk.Button(cols_frame, text="◀ 左に1列追加", 
                  command=self.add_col_left, width=12).grid(row=0, column=2, padx=2)
        ttk.Button(cols_frame, text="▶ 右に1列追加", 
                  command=self.add_col_right, width=12).grid(row=0, column=3, padx=2)
        
        # 列数削除ボタン
        ttk.Button(cols_frame, text="左から1列削除", 
                  command=self.remove_col_left, width=12).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(cols_frame, text="右から1列削除", 
                  command=self.remove_col_right, width=12).grid(row=1, column=3, padx=2, pady=2)
        
        # 複数列追加
        ttk.Label(cols_frame, text="複数追加:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.cols_bulk_var = tk.IntVar(value=10)
        ttk.Spinbox(cols_frame, from_=2, to=50, textvariable=self.cols_bulk_var, width=5).grid(row=2, column=1, pady=(5, 0))
        ttk.Button(cols_frame, text="◀ 左に追加", 
                  command=self.add_cols_left_bulk, width=12).grid(row=2, column=2, padx=2, pady=(5, 0))
        ttk.Button(cols_frame, text="▶ 右に追加", 
                  command=self.add_cols_right_bulk, width=12).grid(row=2, column=3, padx=2, pady=(5, 0))
        
        # === 直接入力エリア ===
        direct_frame = ttk.LabelFrame(screen_frame, text="直接設定", padding="5")
        direct_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(direct_frame, text="行数:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(direct_frame, from_=1, to=100, textvariable=self.current_rows, 
                   width=8, command=self.on_direct_change).grid(row=0, column=1, padx=2)
        
        ttk.Label(direct_frame, text="列数:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        ttk.Spinbox(direct_frame, from_=1, to=200, textvariable=self.current_cols, 
                   width=8, command=self.on_direct_change).grid(row=0, column=3, padx=2)
        
        ttk.Label(direct_frame, text="ドローン間隔:").grid(row=0, column=4, sticky=tk.W, padx=(20, 0))
        ttk.Spinbox(direct_frame, from_=0.5, to=10.0, increment=0.1, textvariable=self.current_spacing, 
                   width=8, command=self.on_direct_change).grid(row=0, column=5, padx=2)
        ttk.Label(direct_frame, text="m").grid(row=0, column=6, sticky=tk.W)
        
        # 適用ボタン
        ttk.Button(direct_frame, text="設定を適用", 
                  command=self.apply_settings, width=15).grid(row=0, column=7, padx=10)
        
        # === リセット・プリセットエリア ===
        preset_frame = ttk.Frame(screen_frame)
        preset_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(preset_frame, text="10×65 標準", 
                  command=lambda: self.load_preset(10, 65)).grid(row=0, column=0, padx=2)
        ttk.Button(preset_frame, text="13×50 実測", 
                  command=lambda: self.load_preset(13, 50)).grid(row=0, column=1, padx=2)
        ttk.Button(preset_frame, text="15×70 大画面", 
                  command=lambda: self.load_preset(15, 70)).grid(row=0, column=2, padx=2)
        ttk.Button(preset_frame, text="20×100 特大", 
                  command=lambda: self.load_preset(20, 100)).grid(row=0, column=3, padx=2)
        
        ttk.Button(preset_frame, text="リセット", 
                  command=self.reset_to_default).grid(row=0, column=4, padx=10)
    
    # === 行数調整メソッド ===
    def add_row_top(self):
        """上に1行追加"""
        current = self.current_rows.get()
        self.current_rows.set(current + 1)
        self.update_display_info()
        print(f"上に1行追加: {current} → {current + 1}")
    
    def add_row_bottom(self):
        """下に1行追加"""
        current = self.current_rows.get()
        self.current_rows.set(current + 1)
        self.update_display_info()
        print(f"下に1行追加: {current} → {current + 1}")
    
    def remove_row_top(self):
        """上から1行削除"""
        current = self.current_rows.get()
        if current > 1:
            self.current_rows.set(current - 1)
            self.update_display_info()
            print(f"上から1行削除: {current} → {current - 1}")
    
    def remove_row_bottom(self):
        """下から1行削除"""
        current = self.current_rows.get()
        if current > 1:
            self.current_rows.set(current - 1)
            self.update_display_info()
            print(f"下から1行削除: {current} → {current - 1}")
    
    def add_rows_top_bulk(self):
        """上に複数行追加"""
        current = self.current_rows.get()
        add_count = self.rows_bulk_var.get()
        self.current_rows.set(current + add_count)
        self.update_display_info()
        print(f"上に{add_count}行追加: {current} → {current + add_count}")
    
    def add_rows_bottom_bulk(self):
        """下に複数行追加"""
        current = self.current_rows.get()
        add_count = self.rows_bulk_var.get()
        self.current_rows.set(current + add_count)
        self.update_display_info()
        print(f"下に{add_count}行追加: {current} → {current + add_count}")
    
    # === 列数調整メソッド ===
    def add_col_left(self):
        """左に1列追加"""
        current = self.current_cols.get()
        self.current_cols.set(current + 1)
        self.update_display_info()
        print(f"左に1列追加: {current} → {current + 1}")
    
    def add_col_right(self):
        """右に1列追加"""
        current = self.current_cols.get()
        self.current_cols.set(current + 1)
        self.update_display_info()
        print(f"右に1列追加: {current} → {current + 1}")
    
    def remove_col_left(self):
        """左から1列削除"""
        current = self.current_cols.get()
        if current > 1:
            self.current_cols.set(current - 1)
            self.update_display_info()
            print(f"左から1列削除: {current} → {current - 1}")
    
    def remove_col_right(self):
        """右から1列削除"""
        current = self.current_cols.get()
        if current > 1:
            self.current_cols.set(current - 1)
            self.update_display_info()
            print(f"右から1列削除: {current} → {current - 1}")
    
    def add_cols_left_bulk(self):
        """左に複数列追加"""
        current = self.current_cols.get()
        add_count = self.cols_bulk_var.get()
        self.current_cols.set(current + add_count)
        self.update_display_info()
        print(f"左に{add_count}列追加: {current} → {current + add_count}")
    
    def add_cols_right_bulk(self):
        """右に複数列追加"""
        current = self.current_cols.get()
        add_count = self.cols_bulk_var.get()
        self.current_cols.set(current + add_count)
        self.update_display_info()
        print(f"右に{add_count}列追加: {current} → {current + add_count}")
    
    # === ユーティリティメソッド ===
    def on_direct_change(self):
        """直接入力での変更時"""
        self.update_display_info()
    
    def update_display_info(self):
        """表示情報の更新"""
        rows = self.current_rows.get()
        cols = self.current_cols.get()
        spacing = self.current_spacing.get()
        total_leds = rows * cols
        
        # メイン表示更新
        self.display_label.config(text=f"LEDスクリーン: {rows}行 × {cols}列")
        self.total_leds_label.config(text=f"総LED数: {total_leds:,}個 | ドローン間隔: {spacing}m")
        
        # 個別表示更新
        self.rows_display.config(text=str(rows))
        self.cols_display.config(text=str(cols))
        
        # 面積計算
        width_m = (cols - 1) * spacing
        height_m = (rows - 1) * spacing
        area_m2 = width_m * height_m
        
        print(f"LEDスクリーン更新: {rows}×{cols} ({total_leds}個)")
        print(f"実サイズ: {width_m:.1f}m × {height_m:.1f}m (面積: {area_m2:.1f}㎡)")
    
    def load_preset(self, rows, cols):
        """プリセット読み込み"""
        self.current_rows.set(rows)
        self.current_cols.set(cols)
        self.update_display_info()
        print(f"プリセット適用: {rows}×{cols}")
    
    def reset_to_default(self):
        """デフォルトにリセット"""
        self.current_rows.set(10)
        self.current_cols.set(65)
        self.current_spacing.set(2.0)
        self.update_display_info()
        print("デフォルト設定にリセット")
    
    def apply_settings(self):
        """設定を適用"""
        rows = self.current_rows.get()
        cols = self.current_cols.get()
        spacing = self.current_spacing.get()
        
        # アプリケーションの設定を更新
        if hasattr(self.app, 'screen_configs'):
            self.app.screen_configs["カスタム"] = {
                "rows": rows,
                "cols": cols,
                "spacing": 30,  # GUI表示用
                "drone_spacing_m": spacing
            }
            
            # カスタム設定変数を更新
            if hasattr(self.app, 'custom_rows_var'):
                self.app.custom_rows_var.set(rows)
            if hasattr(self.app, 'custom_cols_var'):
                self.app.custom_cols_var.set(cols)
            if hasattr(self.app, 'custom_drone_spacing_var'):
                self.app.custom_drone_spacing_var.set(spacing)
            
            # プレビュー更新
            if hasattr(self.app, 'update_preview'):
                self.app.update_preview()
        
        print(f"設定適用完了: {rows}×{cols}, 間隔{spacing}m")
        print(f"総LED数: {rows * cols:,}個")

# テスト用のデモアプリケーション
def demo_enhanced_led_screen():
    """拡張LED画面設定のデモ"""
    
    class DemoApp:
        def __init__(self):
            self.screen_configs = {}
        
        def update_preview(self):
            print("プレビュー更新中...")
    
    root = tk.Tk()
    root.title("拡張LED画面設定 - デモ")
    root.geometry("800x600")
    
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # デモアプリインスタンス
    demo_app = DemoApp()
    
    # 拡張LED画面設定UI
    enhanced_ui = EnhancedLEDScreenSettings(main_frame, demo_app)
    
    print("拡張LED画面設定デモを開始します")
    print("各ボタンをクリックして動作を確認してください")
    
    root.mainloop()

if __name__ == "__main__":
    demo_enhanced_led_screen()