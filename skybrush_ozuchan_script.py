"""
Font2LED - 小津ちゃん LED表示スクリプト
Skybrush LED Effects用（520-550フレーム）
"""

# エンベッドされたLEDデータ（実際のJSONから）
LED_DATA = {
    "metadata": {
        "grid_width": 65,
        "grid_height": 10,
        "frame_count": 1,
        "font": "JF-Dot-k12x10",
        "created": "2025-01-26T16:58:55.853117"
    },
    "frames": [
        {
            "frame": 0,
            "text": "小津ちゃん",
            "pixels": []  # ここは実際のJSONデータから取得する必要があります
        }
    ]
}

def main(frame, time_fraction, drone_index, formation_index, position, drone_count):
    """
    Skybrush LED Effects メイン関数
    
    10×65 LEDスクリーン用
    X範囲: -97.5 ~ 97.5 (65列 × 3.0間隔)
    Z範囲: 0 ~ 27 (10行 × 3.0間隔)
    """
    
    # デフォルト色（消灯）
    default_color = (0.0, 0.0, 0.0, 1.0)
    
    # ドローンの位置を取得
    x = position[0]
    z = position[2]
    
    # グリッド座標に変換（10×65配列）
    # X: 65列（-97.5から97.5、3.0間隔）
    # Z: 10行（0から27、3.0間隔）
    
    col = int((x + 97.5) / 3.0)  # 0-64
    row = int(z / 3.0)  # 0-9
    
    # 範囲チェック
    if not (0 <= col < 65 and 0 <= row < 10):
        return default_color
    
    # JSONデータのピクセルをチェック
    frames = LED_DATA.get("frames", [])
    if frames:
        current_frame = frames[0]  # 今回は1フレームのみ
        
        # 実際のピクセルデータがある場合はここでチェック
        pixels = current_frame.get("pixels", [])
        for pixel in pixels:
            if pixel["x"] == col and pixel["y"] == row:
                return (pixel["r"], pixel["g"], pixel["b"], 1.0)
    
    # テスト用：「小」の字の簡易パターン（中央に表示）
    # 実際にはJSONのピクセルデータを使用
    if 25 <= col <= 40 and 2 <= row <= 7:
        # 「小」の字の簡易形状
        if row == 2 and 30 <= col <= 35:  # 上横線
            return (1.0, 0.2, 0.2, 1.0)  # 赤
        elif col == 32 and 3 <= row <= 6:  # 縦線
            return (1.0, 0.2, 0.2, 1.0)  # 赤
        elif row == 7 and (col == 29 or col == 35):  # 下の点
            return (1.0, 0.2, 0.2, 1.0)  # 赤
    
    return default_color