#!/usr/bin/env python3
"""
中心計算ロジックの詳細分析
奇数・偶数で動作が変わる原因を特定
"""

def analyze_center_calculation():
    """中心計算の詳細分析"""
    print("中心計算ロジックの詳細分析")
    print("=" * 80)
    
    text_width = 17  # テキスト幅
    x_offset = 0     # オフセット
    
    print(f"テキスト幅: {text_width}ピクセル")
    print(f"x_offset: {x_offset}")
    print()
    
    # 列数20から25まで分析
    for cols in range(20, 26):
        center_calc = (cols - text_width) // 2
        actual_left = center_calc + x_offset
        actual_right = actual_left + text_width - 1
        
        left_space = actual_left
        right_space = cols - 1 - actual_right
        
        print(f"列数 {cols}:")
        print(f"  center_calc = ({cols} - {text_width}) // 2 = {cols - text_width} // 2 = {center_calc}")
        print(f"  actual_left = {center_calc} + {x_offset} = {actual_left}")
        print(f"  actual_right = {actual_left} + {text_width} - 1 = {actual_right}")
        print(f"  左側余白: {left_space}")
        print(f"  右側余白: {cols} - 1 - {actual_right} = {right_space}")
        
        # 視覚化
        visual = ['.'] * cols
        for i in range(actual_left, min(actual_right + 1, cols)):
            if i >= 0:
                visual[i] = '#'
        print(f"  視覚: {''.join(visual)}")
        print()
    
    print("=" * 80)
    print("問題の原因分析")
    print("=" * 80)
    
    print("\n整数除算による切り捨ての影響:")
    print("- (20 - 17) // 2 = 3 // 2 = 1")
    print("- (21 - 17) // 2 = 4 // 2 = 2")
    print("- (22 - 17) // 2 = 5 // 2 = 2")
    print("- (23 - 17) // 2 = 6 // 2 = 3")
    
    print("\n結果:")
    print("- 20列→21列: center_calc が 1→2 に変化 (左に1ピクセルシフト)")
    print("- 21列→22列: center_calc が 2→2 で不変 (右側に1列追加)")
    print("- 22列→23列: center_calc が 2→3 に変化 (左に1ピクセルシフト)")
    
    print("\nこれが「1回目は左、2回目は右」という動作の原因！")
    
    print("\n" + "=" * 80)
    print("解決策の検討")
    print("=" * 80)
    
    print("\n案1: x_offsetを使って補正")
    print("右に追加時:")
    print("- 奇数→偶数: x_offset を -1 して左シフトを相殺")
    print("- 偶数→奇数: x_offset は変更なし")
    
    print("\n案2: 常に右側に追加されるよう調整")
    print("右に追加時:")
    print("- 列数増加後、テキスト位置が変わらないようx_offsetを調整")
    
    # 解決策のシミュレーション
    print("\n" + "=" * 80)
    print("解決策のシミュレーション")
    print("=" * 80)
    
    def simulate_right_add_fixed(cols, text_width, x_offset):
        """修正版の右に追加シミュレーション"""
        # 現在の位置を記録
        old_center = (cols - text_width) // 2
        old_left = old_center + x_offset
        
        # 列数を増やす
        new_cols = cols + 1
        new_center = (new_cols - text_width) // 2
        
        # 位置を維持するためのx_offset調整
        new_x_offset = x_offset + (old_center - new_center)
        new_left = new_center + new_x_offset
        
        return new_cols, new_x_offset, new_left
    
    print("\n修正版シミュレーション:")
    cols = 20
    x_off = 0
    
    for i in range(5):
        old_cols = cols
        old_x_off = x_off
        
        cols, x_off, left_pos = simulate_right_add_fixed(cols, text_width, x_off)
        
        print(f"{i+1}回目: {old_cols}列→{cols}列, x_offset {old_x_off}→{x_off}, 左端位置 {left_pos}")

if __name__ == "__main__":
    analyze_center_calculation()