#!/usr/bin/env python3
"""
Font2LED - JF-Dot-k12x10 フォントをLEDマトリックスデータに変換
日本語ピクセルフォントを10x65 LEDドローンディスプレイ用に変換するツール
"""

import freetype
import numpy as np
from PIL import Image, ImageDraw
import json
from typing import List, Dict, Tuple, Optional
import os
import sys
from datetime import datetime

class Font2LED:
    """JF-Dot-k12x10フォントをLEDマトリックスに変換"""
    
    def __init__(self, font_path: str = None):
        """
        Args:
            font_path: フォントファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        if font_path is None:
            # デフォルトのフォントパスを試す
            default_paths = [
                r"C:\Users\macka\Downloads\JF-Dot-k12x10\JF-Dot-k12x10.ttf",
                "../JF-Dot-k12x10/JF-Dot-k12x10.ttf",
                r"..\JF-Dot-k12x10\JF-Dot-k12x10.ttf",
                "./JF-Dot-k12x10.ttf",
                r"H:\Yuki Tsuruoka Dropbox\鶴岡悠生\Claude\0722-windous\JF-Dot-k12x10\JF-Dot-k12x10.ttf"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    font_path = path
                    break
            else:
                print("Tried paths:")
                for p in default_paths:
                    print(f"  - {p}")
                raise FileNotFoundError("JF-Dot-k12x10.ttf font file not found. Please check the font file location.")
        
        self.font_path = font_path
        self.face = freetype.Face(font_path)
        # JF-Dot-k12x10は12x10ピクセル
        self.face.set_pixel_sizes(12, 10)
        self.char_cache = {}
        
        print(f"Loaded font: {os.path.basename(font_path)}")
    
    def get_char_bitmap(self, char: str) -> np.ndarray:
        """文字のビットマップを取得"""
        if char in self.char_cache:
            return self.char_cache[char]
        
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
                
                # 10x12の固定サイズに正規化
                normalized = np.zeros((10, 12), dtype=np.uint8)
                h, w = result.shape
                # 下揃えで配置（高さが異なる場合も対応）
                if w <= 12:
                    if h < 10:
                        # 高さが10未満の場合は下揃え
                        normalized[10-h:10, :w] = result
                    elif h == 10:
                        # 高さがちょうど10の場合
                        normalized[:, :w] = result
                    else:
                        # 高さが10を超える場合は下から10行を取る
                        normalized[:, :w] = result[h-10:h, :w]
                else:
                    # 幅が12を超える場合はクロップ
                    if h < 10:
                        normalized[10-h:10, :12] = result[:, :12]
                    elif h == 10:
                        normalized[:, :12] = result[:, :12]
                    else:
                        normalized[:, :12] = result[h-10:h, :12]
                
                result = normalized
            else:
                # 空白文字の場合
                result = np.zeros((10, 12), dtype=np.uint8)
            
        except Exception as e:
            print(f"Warning: Failed to load character '{char}': {e}")
            result = np.zeros((10, 12), dtype=np.uint8)
        
        self.char_cache[char] = result
        return result
    
    def text_to_led_matrix(self, text: str, spacing: int = 1) -> Dict:
        """
        テキストをLEDマトリックスデータに変換
        
        Returns:
            {
                "width": 実際の幅,
                "height": 10,
                "pixels": [(x, y), ...] # 点灯するピクセルの座標リスト
                "matrix": numpy array
            }
        """
        if not text:
            return {"width": 0, "height": 10, "pixels": [], "matrix": np.zeros((10, 0))}
        
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
                bitmaps.append(np.zeros((10, 4), dtype=np.uint8))
                total_width += 4
            
            if i < len(text) - 1:
                total_width += spacing
        
        # 全体のマトリックスを作成
        matrix = np.zeros((10, total_width), dtype=np.uint8)
        x_offset = 0
        
        for i, bitmap in enumerate(bitmaps):
            h, w = bitmap.shape
            matrix[:h, x_offset:x_offset+w] = bitmap
            x_offset += w
            if i < len(bitmaps) - 1:
                x_offset += spacing
        
        # 点灯ピクセルの座標を抽出
        pixels = []
        for y in range(10):
            for x in range(total_width):
                if matrix[y, x] > 0:
                    pixels.append((x, y))
        
        return {
            "width": total_width,
            "height": 10,
            "pixels": pixels,
            "matrix": matrix
        }
    
    def create_led_animation_json(self, 
                                 texts: List[str], 
                                 colors: List[Tuple[float, float, float]] = None,
                                 frame_interval: int = 30,
                                 center: bool = True) -> Dict:
        """
        複数のテキストからアニメーションJSON作成
        
        Args:
            texts: 表示するテキストのリスト
            colors: 各テキストの色（RGB 0.0-1.0）
            frame_interval: フレーム間隔
            center: テキストを中央揃えにするか
        """
        if colors is None:
            colors = [(1.0, 1.0, 1.0)] * len(texts)
        elif len(colors) < len(texts):
            # 色が足りない場合は白で補完
            colors = list(colors) + [(1.0, 1.0, 1.0)] * (len(texts) - len(colors))
        
        frames = []
        
        for i, (text, color) in enumerate(zip(texts, colors)):
            led_data = self.text_to_led_matrix(text)
            
            # フレームデータを構築
            frame = {
                "frame": i * frame_interval,
                "text": text,
                "pixels": []
            }
            
            # センタリング計算（65列の中央に配置）
            if center:
                x_offset = max(0, (65 - led_data["width"]) // 2)
            else:
                x_offset = 0
            
            for x, y in led_data["pixels"]:
                # グリッド範囲内のピクセルのみ追加
                led_x = x + x_offset
                if 0 <= led_x < 65 and 0 <= y < 10:
                    frame["pixels"].append({
                        "x": led_x,
                        "y": y,
                        "r": color[0],
                        "g": color[1],
                        "b": color[2],
                        "intensity": 1.0
                    })
            
            frames.append(frame)
        
        # メタデータを含む完全なJSONデータ
        return {
            "metadata": {
                "grid_width": 65,
                "grid_height": 10,
                "frame_count": len(frames),
                "font": "JF-Dot-k12x10",
                "frame_interval": frame_interval,
                "created": datetime.now().isoformat(),
                "centered": center
            },
            "frames": frames
        }
    
    def preview_text(self, text: str, 
                    scale: int = 20, 
                    color: Tuple[int, int, int] = (255, 255, 255),
                    show_grid: bool = True) -> Image.Image:
        """テキストのプレビュー画像を生成"""
        led_data = self.text_to_led_matrix(text)
        
        # 画像サイズ（65x10のLEDグリッド）
        img_width = 65 * scale
        img_height = 10 * scale
        
        # 黒背景の画像を作成
        image = Image.new('RGB', (img_width, img_height), 'black')
        draw = ImageDraw.Draw(image)
        
        # グリッド線を描画
        if show_grid:
            grid_color = (40, 40, 40)
            for x in range(0, img_width + 1, scale):
                draw.line([(x, 0), (x, img_height)], fill=grid_color)
            for y in range(0, img_height + 1, scale):
                draw.line([(0, y), (img_width, y)], fill=grid_color)
        
        # テキストをセンタリング
        x_offset = (65 - led_data["width"]) // 2
        
        # LEDピクセルを描画
        for x, y in led_data["pixels"]:
            led_x = x + x_offset
            if 0 <= led_x < 65:
                x1 = led_x * scale + 2
                y1 = y * scale + 2
                x2 = x1 + scale - 4
                y2 = y1 + scale - 4
                
                # 円形のLED
                draw.ellipse([x1, y1, x2, y2], fill=color)
        
        # 情報テキストを追加
        info_y = img_height + 5
        # 画像を少し大きくして情報を含める
        info_image = Image.new('RGB', (img_width, img_height + 30), 'black')
        info_image.paste(image, (0, 0))
        info_draw = ImageDraw.Draw(info_image)
        
        info_draw.text((10, info_y), f"Text: {text}", fill=(200, 200, 200))
        info_draw.text((img_width - 150, info_y), 
                      f"Size: {led_data['width']}x10", fill=(200, 200, 200))
        
        return info_image
    
    def save_preview_grid(self, texts: List[str], 
                         colors: List[Tuple[int, int, int]] = None,
                         output_path: str = "preview_grid.png",
                         scale: int = 10):
        """複数のテキストをグリッド形式でプレビュー"""
        if colors is None:
            colors = [(255, 255, 255)] * len(texts)
        
        # 各テキストのプレビューを生成
        previews = []
        for text, color in zip(texts, colors):
            preview = self.preview_text(text, scale=scale, color=color, show_grid=True)
            previews.append(preview)
        
        if not previews:
            return
        
        # グリッドレイアウトで結合
        preview_height = previews[0].height
        total_height = preview_height * len(previews)
        
        grid_image = Image.new('RGB', (previews[0].width, total_height), 'black')
        
        for i, preview in enumerate(previews):
            grid_image.paste(preview, (0, i * preview_height))
        
        grid_image.save(output_path)
        print(f"Saved preview grid: {output_path}")

def main():
    """メイン実行関数"""
    # Font2LEDツールの初期化
    converter = Font2LED()
    
    # サンプルテキスト
    sample_texts = [
        "かっきー",
        "みーきゅん", 
        "真夏日よ",
        "NOGIZAKA46",
        "乃木坂46"
    ]
    
    sample_colors = [
        (1.0, 0.3, 0.3),  # 赤
        (0.3, 1.0, 0.3),  # 緑
        (0.3, 0.3, 1.0),  # 青
        (1.0, 1.0, 0.3),  # 黄
        (1.0, 0.3, 1.0),  # マゼンタ
    ]
    
    # 1. 個別プレビュー生成
    print("=== Generating individual previews ===")
    for i, text in enumerate(sample_texts):
        color_rgb = tuple(int(c * 255) for c in sample_colors[i])
        preview = converter.preview_text(text, scale=15, color=color_rgb)
        filename = f"preview_{i+1}_{text}.png"
        preview.save(filename)
        print(f"Saved: {filename}")
    
    # 2. グリッドプレビュー生成
    print("\n=== Generating preview grid ===")
    converter.save_preview_grid(
        sample_texts, 
        colors=[tuple(int(c * 255) for c in color) for color in sample_colors],
        output_path="preview_all.png",
        scale=10
    )
    
    # 3. アニメーションJSON生成
    print("\n=== Generating animation JSON ===")
    animation_data = converter.create_led_animation_json(
        texts=sample_texts,
        colors=sample_colors,
        frame_interval=60,  # 2秒間隔（30fps）
        center=True
    )
    
    # JSON保存
    output_json = "led_animation.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(animation_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved: {output_json}")
    print(f"Total frames: {len(animation_data['frames'])}")
    
    # 統計情報表示
    print("\n=== Animation Statistics ===")
    for frame in animation_data['frames']:
        print(f"Frame {frame['frame']:3d}: '{frame['text']}' - {len(frame['pixels'])} pixels")
    
    print("\nConversion completed successfully!")
    print(f"Next step: Import '{output_json}' into Blender using the LED JSON importer script.")

if __name__ == "__main__":
    main()