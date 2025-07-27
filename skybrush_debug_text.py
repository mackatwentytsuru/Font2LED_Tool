"""
Skybrush LED Effects - Debug Text Display
デバッグ機能付きテキスト表示スクリプト
"""

import json
import os

# デバッグ用カウンター
debug_counter = 0

def load_data():
    """JSONデータを読み込む"""
    json_path = r"H:\Yuki Tsuruoka Dropbox\鶴岡悠生\Claude\0722-windous\Font2LED_Tool\led_animation.json"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return {"frames": []}

def main(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """
    Skybrush LED Effects メイン関数（デバッグ版）
    
    LEDエンプティの座標系を使用:
    - 65列×10行のグリッド
    - X座標: 47.1 ~ -47.1（右から左）
    - Z座標: 58.9 ~ 45.7（下から上）
    """
    global debug_counter
    
    # 最初の数回だけデバッグ出力
    if debug_counter < 3:
        print(f"Debug {debug_counter}: drone_index={drone_index}, pos=({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})")
        debug_counter += 1
    
    # デバッグ用：エラー時の色
    error_color = (0.0, 0.0, 0.2, 1.0)  # 薄い青
    
    # データを読み込み
    data = load_data()
    frames = data.get("frames", [])
    
    if not frames:
        return error_color
    
    # テキストフレームを選択
    text_index = min(int(time_fraction * len(frames)), len(frames) - 1)
    current_frame = frames[text_index]
    
    # LEDエンプティの座標から列と行を計算
    x = position[0]  # X座標
    z = position[2]  # Z座標（position[2]がZ！）
    
    # 座標範囲（実測値）
    x_min = -47.1  # 左端（列65）
    x_max = 47.1   # 右端（列1）
    z_min = 45.7   # 上端（行10）
    z_max = 58.9   # 下端（行1）
    
    # グリッド位置を計算（0-64, 0-9）
    # X座標は左から右（180度回転を修正）
    grid_x = 64 - int(round((x_max - x) / ((x_max - x_min) / 64)))
    # Z座標は上下反転
    grid_z = 9 - int(round((z - z_min) / ((z_max - z_min) / 9)))
    
    # デバッグ出力
    if debug_counter == 3:
        print(f"Grid mapping: pos({x:.1f}, {z:.1f}) -> grid({grid_x}, {grid_z})")
        debug_counter += 1
        debug_counter += 1
    
    # デバッグ: グリッドの隅を確認（一時的にコメントアウト）
    # if grid_x == 0 and grid_z == 0:  # 右上
    #     return (1.0, 0.0, 0.0, 1.0)  # 赤
    # if grid_x == 64 and grid_z == 0:  # 左上
    #     return (0.0, 1.0, 0.0, 1.0)  # 緑
    # if grid_x == 0 and grid_z == 9:  # 右下
    #     return (0.0, 0.0, 1.0, 1.0)  # 青
    # if grid_x == 64 and grid_z == 9:  # 左下
    #     return (1.0, 1.0, 0.0, 1.0)  # 黄色
    
    # 範囲外チェック
    if grid_x < 0 or grid_x >= 65 or grid_z < 0 or grid_z >= 10:
        return (0.5, 0.0, 0.0, 1.0)  # 暗い赤でエラー表示
    
    # Font2LEDデータのマッピング
    # 65x10グリッドなのでスケーリング不要
    
    # ピクセルチェック
    for pixel in current_frame.get("pixels", []):
        pixel_x = pixel["x"]  # 0-64
        pixel_y = pixel["y"]  # 0-9
        
        # Font2LEDのY座標（上が0）をグリッドZ座標（上が0）に直接対応
        if grid_x == pixel_x and grid_z == pixel_y:
            # マッチしたピクセルの色を返す
            return (
                pixel.get("r", 1.0),
                pixel.get("g", 1.0),
                pixel.get("b", 1.0),
                1.0
            )
    
    # デフォルトは消灯（黒）
    return (0.0, 0.0, 0.0, 1.0)

# テスト関数
def test():
    """スタンドアロンテスト"""
    print("Testing skybrush_debug_text.py...")
    
    # テスト位置
    test_positions = [
        (0, 0, 29.164),     # 中央付近
        (-73.5, 0, 11.164), # 左下隅
        (73.5, 0, 47.164),  # 右上隅
    ]
    
    for pos in test_positions:
        color = main(
            frame=550,
            time_fraction=0.0,
            drone_index=0,
            formation_index=0,
            position=pos,
            drone_count=650
        )
        print(f"Position {pos} -> Color {color}")

if __name__ == "__main__":
    test()