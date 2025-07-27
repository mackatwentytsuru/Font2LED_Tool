#!/usr/bin/env python3
"""
ユーザーの視覚的体験と技術的動作のギャップ分析
なぜユーザーが「右に追加→左に列追加」と感じるのか
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from font2led_gui import Font2LEDApp

def analyze_visual_perception():
    """ユーザーの視覚的認識を分析"""
    print("ユーザー視覚体験分析")
    print("=" * 80)
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        app = Font2LEDApp(root)
        
        # 実際のテストシナリオ
        test_text = "小津ちゃん"
        led_data = app.text_to_led_matrix(test_text)
        app.current_led_data = led_data
        
        text_width = led_data['width']  # 29
        
        print(f"テスト文字: '{test_text}' ({text_width}ピクセル幅)")
        print("")
        
        # シナリオ1: 初期状態
        cols = 65
        x_offset = 0
        
        app.custom_cols_var.set(cols)
        app.x_offset_adjustment = x_offset
        
        center_pos = (cols - text_width) // 2 + x_offset  # (65-29)//2 + 0 = 18
        left_edge = center_pos
        right_edge = center_pos + text_width - 1  # 18 + 29 - 1 = 46
        
        print("=== 初期状態 ===")
        print(f"スクリーン: 65列 (0-64)")
        print(f"テキスト位置: {left_edge}-{right_edge}")
        print(f"左側余白: {left_edge}列")
        print(f"右側余白: {cols - 1 - right_edge}列")
        
        # ユーザーの視点での確認
        left_space_before = left_edge
        right_space_before = cols - 1 - right_edge
        
        print("")
        print("=== 右に追加ボタンを押した後 ===")
        
        # 右に追加の実行
        new_cols = cols + 1  # 66
        new_x_offset = x_offset  # 0（変更されない）
        
        app.custom_cols_var.set(new_cols)
        app.x_offset_adjustment = new_x_offset
        
        new_center_pos = (new_cols - text_width) // 2 + new_x_offset  # (66-29)//2 + 0 = 18
        new_left_edge = new_center_pos
        new_right_edge = new_center_pos + text_width - 1  # 18 + 29 - 1 = 46
        
        print(f"スクリーン: {new_cols}列 (0-{new_cols-1})")
        print(f"テキスト位置: {new_left_edge}-{new_right_edge}")
        print(f"左側余白: {new_left_edge}列")
        print(f"右側余白: {new_cols - 1 - new_right_edge}列")
        
        # ユーザーが見る変化
        left_space_after = new_left_edge
        right_space_after = new_cols - 1 - new_right_edge
        
        left_change = left_space_after - left_space_before
        right_change = right_space_after - right_space_before
        
        print("")
        print("=== ユーザーが見る変化 ===")
        print(f"左側余白: {left_space_before} → {left_space_after} ({left_change:+d})")
        print(f"右側余白: {right_space_before} → {right_space_after} ({right_change:+d})")
        print(f"テキスト位置: {left_edge}-{right_edge} → {new_left_edge}-{new_right_edge}")
        
        # 問題分析
        print("")
        print("=== 問題分析 ===")
        if left_change == 0 and right_change > 0:
            print("✅ 技術的には正しい: テキスト位置維持、右側に余白追加")
            print("")
            print("❓ ユーザーが混乱する理由:")
            print("1. テキストの左端位置が変わらない")
            print("2. 視覚的には「右に追加」の効果が分かりにくい")
            print("3. スクリーンサイズ変更よりもテキスト移動の方が目立つ")
        else:
            print("🔍 予期しない動作が検出されました")
        
        # シナリオ2: 左に追加との比較
        print("")
        print("=== 左に追加ボタンとの比較 ===")
        
        # 元の状態に戻す
        app.custom_cols_var.set(65)
        app.x_offset_adjustment = 0
        
        # 左に追加を実行
        app.add_col_left()
        
        left_cols = app.custom_cols_var.get()  # 66
        left_x_offset = app.x_offset_adjustment  # 1
        
        left_center_pos = (left_cols - text_width) // 2 + left_x_offset  # (66-29)//2 + 1 = 19
        left_left_edge = left_center_pos
        left_right_edge = left_center_pos + text_width - 1  # 19 + 29 - 1 = 47
        
        print(f"左に追加後:")
        print(f"スクリーン: {left_cols}列")
        print(f"テキスト位置: {left_left_edge}-{left_right_edge}")
        print(f"左側余白: {left_left_edge}列")
        print(f"右側余白: {left_cols - 1 - left_right_edge}列")
        
        # 初期状態との比較
        left_space_change = left_left_edge - left_edge
        right_space_change = (left_cols - 1 - left_right_edge) - right_space_before
        
        print("")
        print("初期状態からの変化:")
        print(f"左側余白: {left_edge} → {left_left_edge} ({left_space_change:+d})")
        print(f"右側余白: {right_space_before} → {left_cols - 1 - left_right_edge} ({right_space_change:+d})")
        print(f"テキスト移動: {left_edge}-{right_edge} → {left_left_edge}-{left_right_edge}")
        
        print("")
        print("=== 結論 ===")
        print("左に追加: テキストが明確に右に移動（視覚的に分かりやすい）")
        print("右に追加: テキスト位置変わらず（視覚的に分かりにくい）")
        
        return True
        
    except Exception as e:
        print(f"分析エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        root.destroy()

def propose_solution():
    """ユーザー体験改善のソリューション提案"""
    print("")
    print("=" * 80)
    print("ユーザー体験改善案")
    print("=" * 80)
    
    print("""
【現在の問題】
ユーザーが「右に追加」と期待する動作と実際の動作にギャップがある

【ユーザーの期待】
「右に追加」→ テキストが左にシフトして右側に空白ができる

【現在の動作】
「右に追加」→ テキスト位置維持、右側に空白追加（視覚的に分かりにくい）

【解決案】

案1: 右ボタンのロジック変更（ユーザーの期待に合わせる）
-----------------------------------------------------------
def add_col_right(self):
    # 列数を増やし、テキストを左にシフト（右側に空白を作る）
    current = self.custom_cols_var.get()
    self.custom_cols_var.set(current + 1)
    # x_offset_adjustmentを減らしてテキストを左にシフト
    self.x_offset_adjustment = max(0, self.x_offset_adjustment - 1)

def remove_col_right(self):
    # 列数を減らし、テキストを右にシフト（右側から削除）
    current = self.custom_cols_var.get()
    if current > 1:
        self.custom_cols_var.set(current - 1)
        # 必要に応じてテキストを右にシフト
        self.x_offset_adjustment += 1

案2: UIラベルの変更（現在の動作に合わせる）
-------------------------------------------
「右に追加」→「右側拡張」
「右から削除」→「右側縮小」
「左に追加」→「左側拡張」
「左から削除」→「左側縮小」

案3: 視覚的フィードバックの改善
-------------------------------
- プレビューでスクリーン境界を明確に表示
- 追加された領域をハイライト表示
- 操作説明テキストの追加

【推奨案】
案1と案3の組み合わせ：
- 右ボタンをユーザーの直感に合わせて修正
- 視覚的フィードバックで操作結果を明確化
""")

def main():
    """メイン分析実行"""
    print("Font2LED Tool - 視覚的体験分析")
    print("目的: なぜユーザーが右ボタンを「左に追加」と感じるのかを解明")
    print("")
    
    # 視覚的認識分析
    analyze_visual_perception()
    
    # 解決案提案
    propose_solution()

if __name__ == "__main__":
    main()