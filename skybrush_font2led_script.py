"""
Skybrush LED Effects Script for Font2LED
Font2LEDで生成したテキストアニメーションをSkybrush LED Effectsで使用するスクリプト

使用方法:
1. Skybrush LED EffectsでFUNCTION（スクリプト）タイプを選択
2. このスクリプトをロード
3. 開始フレーム: 500、継続時間: 100フレームで設定
"""

import json
import os
import math

# Font2LEDで生成したJSONファイルのパス
JSON_PATH = r"H:\Yuki Tsuruoka Dropbox\鶴岡悠生\Claude\0722-windous\Font2LED_Tool\led_animation.json"

# グローバル変数でデータをキャッシュ
_cached_data = None

def load_font2led_data():
    """JSONデータを読み込んでキャッシュ"""
    global _cached_data
    if _cached_data is None:
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                _cached_data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            _cached_data = {"frames": []}
    return _cached_data

def get_text_frame(time_fraction):
    """時間比率から適切なテキストフレームを取得"""
    data = load_font2led_data()
    frames = data.get("frames", [])
    
    if not frames:
        return None
    
    # 時間比率に基づいてフレームを選択
    # 5つのテキストを100フレームに均等配分（各20フレーム）
    frame_index = int(time_fraction * len(frames))
    if frame_index >= len(frames):
        frame_index = len(frames) - 1
    
    return frames[frame_index]

def font2led_effect(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """
    Skybrush LED Effects用の関数
    
    Args:
        frame: 現在のフレーム番号
        time_fraction: エフェクトの進行度（0.0-1.0）
        drone_index: ドローンのインデックス
        formation_index: フォーメーションインデックス
        position: ドローンの位置 (x, y, z)
        drone_count: ドローン総数
        
    Returns:
        (r, g, b, a) タプル（0.0-1.0の範囲）
    """
    
    # デフォルトは黒（消灯）
    default_color = (0.0, 0.0, 0.0, 1.0)
    
    # テキストフレームを取得
    text_frame = get_text_frame(time_fraction)
    if not text_frame:
        return default_color
    
    # ドローンの位置をグリッド座標に変換
    # 10x65グリッドを想定（実際は50x13にマッピング）
    # 位置の正規化（-73.5 ~ 73.5 → 0 ~ 49）
    grid_x = int((position[0] + 73.5) / 3.0)
    # 位置の正規化（11.16 ~ 47.16 → 0 ~ 12）
    grid_z = int((position[2] - 11.16) / 3.0)
    
    # 65x10から50x13へのスケーリング
    x_scale = 50 / 65.0
    z_scale = 13 / 10.0
    
    # このドローンが点灯すべきかチェック
    pixels = text_frame.get("pixels", [])
    
    for pixel in pixels:
        # 元の座標（65x10グリッド）
        orig_x = pixel["x"]
        orig_z = 9 - pixel["y"]  # Y座標反転
        
        # スケーリングして50x13グリッドに変換
        mapped_x = int(round(orig_x * x_scale))
        mapped_z = int(round(orig_z * z_scale))
        
        # 位置が一致するか確認（許容誤差±1）
        if abs(grid_x - mapped_x) <= 0 and abs(grid_z - mapped_z) <= 0:
            # このピクセルの色を返す
            return (
                pixel["r"],
                pixel["g"],
                pixel["b"],
                1.0  # アルファは常に1.0
            )
    
    # 該当するピクセルがない場合は黒
    return default_color

# Skybrush用のメイン関数
def main(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """Skybrushから呼び出されるメイン関数"""
    return font2led_effect(frame, time_fraction, drone_index, formation_index, position, drone_count)

# テスト用
if __name__ == "__main__":
    # テスト実行
    print("Testing Font2LED Skybrush Script...")
    
    # データ読み込みテスト
    data = load_font2led_data()
    print(f"Loaded {len(data.get('frames', []))} frames")
    
    # 色計算テスト
    test_positions = [
        (0, 0, 24),      # 中央付近
        (-73.5, 0, 11.16),  # 左下
        (73.5, 0, 47.16),   # 右上
    ]
    
    for pos in test_positions:
        color = font2led_effect(
            frame=550,
            time_fraction=0.0,
            drone_index=0,
            formation_index=0,
            position=pos,
            drone_count=650
        )
        print(f"Position {pos}: Color {color}")