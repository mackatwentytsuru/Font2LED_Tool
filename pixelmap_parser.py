#!/usr/bin/env python3
"""
ピクセルマップパーサー
HTMLファイルやその他の形式からピクセルマップデータを抽出
"""

import re
import json
import numpy as np
from PIL import Image
from bs4 import BeautifulSoup
import os

class PixelMapParser:
    """ピクセルマップデータのパーサー"""
    
    def __init__(self):
        self.supported_formats = {
            '.html': self.parse_html,
            '.htm': self.parse_html,
            '.png': self.parse_image,
            '.jpg': self.parse_image,
            '.jpeg': self.parse_image,
            '.gif': self.parse_image,
            '.bmp': self.parse_image,
            '.txt': self.parse_text,
            '.json': self.parse_json
        }
    
    def parse_file(self, filepath):
        """ファイルからピクセルマップを解析"""
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {ext}")
        
        return self.supported_formats[ext](filepath)
    
    def parse_html(self, filepath):
        """HTMLファイルからpixelMapデータを抽出"""
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # scriptタグ内のpixelMapを探す
        pixel_data = None
        color_map = None
        
        for script in soup.find_all('script'):
            if script.string and 'pixelMap' in script.string:
                # pixelMap配列を抽出
                pattern = r'const\s+pixelMap\s*=\s*(\[[\s\S]*?\]);'
                match = re.search(pattern, script.string)
                if match:
                    array_string = match.group(1)
                    # JavaScript配列をPython配列に変換
                    try:
                        pixel_data = json.loads(array_string)
                    except json.JSONDecodeError:
                        # 改行やコメントを処理
                        cleaned = re.sub(r'//.*$', '', array_string, flags=re.MULTILINE)
                        cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)
                        pixel_data = json.loads(cleaned)
                
                # カラーマップを抽出
                color_pattern = r'const\s+colors\s*=\s*({[\s\S]*?});'
                color_match = re.search(color_pattern, script.string)
                if color_match:
                    color_string = color_match.group(1)
                    # JavaScriptオブジェクトをJSON形式に変換
                    color_string = re.sub(r"(\d+):", r'"\1":', color_string)
                    color_string = re.sub(r"'", '"', color_string)
                    try:
                        color_map = json.loads(color_string)
                    except:
                        # デフォルトカラーマップ
                        color_map = self._extract_colors_from_css(soup)
        
        if pixel_data is None:
            raise ValueError("pixelMap data not found in HTML file")
        
        # numpy配列に変換
        pixel_array = np.array(pixel_data)
        
        # カラーマップが見つからない場合、CSSから推測
        if color_map is None:
            color_map = self._extract_colors_from_css(soup)
        
        return self._convert_to_led_format(pixel_array, color_map)
    
    def _extract_colors_from_css(self, soup):
        """CSSからカラー情報を抽出"""
        color_map = {
            0: '#FFFFFF',  # white
            1: '#2E7D32',  # dark-green
            2: '#66BB6A',  # light-green
            3: '#E53935',  # red
            4: '#FF6B6B',  # pink
            5: '#000000'   # black
        }
        
        # styleタグから色情報を取得
        for style in soup.find_all('style'):
            if style.string:
                # .dark-green { background-color: #2E7D32; } パターンを抽出
                pattern = r'\.(\w+)\s*{\s*background-color:\s*(#[0-9A-Fa-f]{6})'
                matches = re.findall(pattern, style.string)
                
                # クラス名から数値へのマッピング
                class_to_num = {
                    'white': 0,
                    'dark-green': 1,
                    'light-green': 2,
                    'red': 3,
                    'pink': 4,
                    'black': 5
                }
                
                for class_name, color in matches:
                    if class_name in class_to_num:
                        color_map[class_to_num[class_name]] = color
        
        return color_map
    
    def parse_image(self, filepath):
        """画像ファイルからピクセルデータを抽出"""
        img = Image.open(filepath)
        
        # 画像が大きすぎる場合は警告
        if img.width > 100 or img.height > 100:
            print(f"Warning: Large image ({img.width}x{img.height}). Consider resizing.")
        
        # RGBAに変換
        img = img.convert('RGBA')
        
        # numpy配列に変換
        pixel_array = np.array(img)
        
        # LED形式に変換
        led_data = {
            'width': img.width,
            'height': img.height,
            'pixels': [],
            'colors': {}
        }
        
        # ユニークな色を抽出
        unique_colors = {}
        color_index = 0
        
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixel_array[y, x]
                
                # 透明ピクセルはスキップ
                if a < 128:
                    continue
                
                # RGBを正規化（0-1）
                color_key = (r/255.0, g/255.0, b/255.0)
                
                # 新しい色の場合は登録
                if color_key not in unique_colors:
                    unique_colors[color_key] = color_index
                    led_data['colors'][f"color_{color_index}"] = color_key
                    color_index += 1
                
                # ピクセルを追加
                led_data['pixels'].append({
                    'x': x,
                    'y': y,
                    'color_id': unique_colors[color_key]
                })
        
        return led_data
    
    def parse_text(self, filepath):
        """テキストファイルからピクセルマップを解析"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2D配列として解析
        lines = content.strip().split('\n')
        pixel_array = []
        
        for line in lines:
            # カンマ区切りまたはスペース区切りを想定
            if ',' in line:
                row = [int(x.strip()) for x in line.split(',')]
            else:
                row = [int(x) for x in line.split()]
            pixel_array.append(row)
        
        pixel_array = np.array(pixel_array)
        
        # デフォルトカラーマップ
        color_map = {
            0: '#FFFFFF',
            1: '#FF0000',
            2: '#00FF00',
            3: '#0000FF',
            4: '#FFFF00',
            5: '#FF00FF',
            6: '#00FFFF',
            7: '#000000'
        }
        
        return self._convert_to_led_format(pixel_array, color_map)
    
    def parse_json(self, filepath):
        """JSONファイルからピクセルマップを解析"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'pixelMap' in data:
            pixel_array = np.array(data['pixelMap'])
            color_map = data.get('colors', {})
        elif 'pixels' in data:
            # Font2LED形式の場合
            return data
        else:
            raise ValueError("Invalid JSON format")
        
        return self._convert_to_led_format(pixel_array, color_map)
    
    def _convert_to_led_format(self, pixel_array, color_map):
        """ピクセル配列をFont2LED形式に変換"""
        height, width = pixel_array.shape
        
        led_data = {
            'width': width,
            'height': height,
            'pixels': [],
            'colors': {}
        }
        
        # カラーマップを変換（16進数→RGB）
        for key, hex_color in color_map.items():
            if isinstance(hex_color, str) and hex_color.startswith('#'):
                r = int(hex_color[1:3], 16) / 255.0
                g = int(hex_color[3:5], 16) / 255.0
                b = int(hex_color[5:7], 16) / 255.0
                led_data['colors'][str(key)] = (r, g, b)
            else:
                led_data['colors'][str(key)] = hex_color
        
        # ピクセルデータを収集
        for y in range(height):
            for x in range(width):
                value = int(pixel_array[y, x])
                if value != 0:  # 0は背景（白）とみなす
                    led_data['pixels'].append({
                        'x': x,
                        'y': y,
                        'color_id': value
                    })
        
        return led_data


if __name__ == "__main__":
    # テスト
    parser = PixelMapParser()
    
    # テスト用のHTMLファイルを作成
    test_html = """
    <script>
        const pixelMap = [
            [0,0,1,1,0,0],
            [0,1,2,2,1,0],
            [1,2,3,3,2,1],
            [1,2,3,3,2,1],
            [0,1,2,2,1,0],
            [0,0,1,1,0,0]
        ];
        
        const colors = {
            1: '#FF0000',
            2: '#00FF00',
            3: '#0000FF'
        };
    </script>
    """
    
    with open('test_pixelmap.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    try:
        result = parser.parse_file('test_pixelmap.html')
        print("Parse result:")
        print(f"Size: {result['width']}x{result['height']}")
        print(f"Pixels: {len(result['pixels'])}")
        print(f"Colors: {result['colors']}")
    finally:
        import os
        if os.path.exists('test_pixelmap.html'):
            os.remove('test_pixelmap.html')