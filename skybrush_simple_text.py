"""
Skybrush LED Effects - Simple Text Display
シンプルなテキスト表示スクリプト（Font2LEDデータ使用）
"""

import json
import os

# JSONデータを直接埋め込む（外部ファイル依存を避ける）
# Font2LEDで生成したデータをここにペースト
TEXT_DATA = None

def load_embedded_data():
    """埋め込みデータまたは外部JSONを読み込む"""
    global TEXT_DATA
    
    if TEXT_DATA is None:
        # 外部JSONファイルから読み込み
        json_path = r"H:\Yuki Tsuruoka Dropbox\鶴岡悠生\Claude\0722-windous\Font2LED_Tool\led_animation.json"
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                TEXT_DATA = json.load(f)
        except:
            # フォールバック：基本的なテストパターン
            TEXT_DATA = {
                "frames": [{
                    "text": "TEST",
                    "pixels": []
                }]
            }
    
    return TEXT_DATA

def main(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """
    Skybrush LED Effects メイン関数
    
    500フレームから100フレーム間で動作することを想定
    5つのテキストを20フレームずつ表示
    """
    
    # データを読み込み
    data = load_embedded_data()
    frames = data.get("frames", [])
    
    if not frames:
        return (0.0, 0.0, 0.0, 1.0)
    
    # どのテキストを表示するか決定
    # time_fraction: 0.0-1.0を5分割
    text_index = min(int(time_fraction * len(frames)), len(frames) - 1)
    current_frame = frames[text_index]
    
    # 実際のグリッド座標（50x13）
    # X範囲: -73.5 ~ 73.5 (3.0間隔)
    # Z範囲: 11.164 ~ 47.164 (3.0間隔)
    x = position[0]
    z = position[2]
    
    # グリッドインデックスに変換（0-49, 0-12）
    grid_x = int(round((x + 73.5) / 3.0))
    grid_z = int(round((z - 11.164) / 3.0))
    
    # 範囲チェック
    if grid_x < 0 or grid_x >= 50 or grid_z < 0 or grid_z >= 13:
        return (0.0, 0.0, 0.0, 1.0)
    
    # 65x10 → 50x13 のマッピング
    # Font2LEDは65x10でデータを生成しているので変換が必要
    scale_x = 50.0 / 65.0  # 0.769
    scale_z = 13.0 / 10.0  # 1.3
    
    # ピクセルデータをチェック
    for pixel in current_frame.get("pixels", []):
        # 元の座標（65x10グリッド）
        orig_x = pixel["x"]
        orig_y = pixel["y"]
        
        # Y座標を反転してZ座標に（Font2LEDは上が0、Blenderは下が0）
        orig_z = 9 - orig_y
        
        # 50x13グリッドにスケーリング
        target_x = int(round(orig_x * scale_x))
        target_z = int(round(orig_z * scale_z))
        
        # 一致チェック
        if grid_x == target_x and grid_z == target_z:
            # この位置のドローンを点灯
            return (
                pixel.get("r", 1.0),
                pixel.get("g", 1.0),
                pixel.get("b", 1.0),
                1.0
            )
    
    # 該当なしは消灯
    return (0.0, 0.0, 0.0, 1.0)