#!/usr/bin/env python3
"""
右ボタン問題の徹底的調査
ユーザー報告：右に追加→左に列追加、右から削除→左から削除
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from font2led_gui import Font2LEDApp

def detailed_state_inspection(app, action_name):
    """アプリケーション状態の詳細調査"""
    print(f"\n=== {action_name} 後の詳細状態 ===")
    
    # 基本状態
    cols = app.custom_cols_var.get()
    x_offset = app.x_offset_adjustment
    
    print(f"列数: {cols}")
    print(f"x_offset_adjustment: {x_offset}")
    
    # LEDデータがある場合の詳細
    if hasattr(app, 'current_led_data') and app.current_led_data:
        led_data = app.current_led_data
        text_width = led_data.get('width', 0)
        text_height = led_data.get('height', 0)
        pixels = led_data.get('pixels', [])
        
        print(f"LEDデータ:")
        print(f"  文字サイズ: {text_width}x{text_height}")
        print(f"  ピクセル数: {len(pixels)}")
        
        # 実際の表示領域計算
        if text_width > 0:
            # プレビューでの計算をシミュレート
            x_offset_calc = (cols - text_width) // 2 + x_offset
            
            print(f"  表示位置計算: ({cols} - {text_width}) // 2 + {x_offset} = {x_offset_calc}")
            
            # 実際のピクセル位置を確認
            if pixels:
                min_x = min(p[0] for p in pixels)
                max_x = max(p[0] for p in pixels)
                actual_left = min_x + x_offset_calc
                actual_right = max_x + x_offset_calc
                
                print(f"  実際の表示範囲: X={actual_left}～{actual_right}")
                print(f"  スクリーン範囲: X=0～{cols-1}")
                
                # はみ出し確認
                if actual_left < 0:
                    print(f"  ⚠️ 左側にはみ出し: {actual_left}")
                if actual_right >= cols:
                    print(f"  ⚠️ 右側にはみ出し: {actual_right} >= {cols}")
    
    # プレビューキャンバスの状態（もしあれば）
    if hasattr(app, 'preview_canvas') and app.preview_canvas:
        try:
            canvas_width = app.preview_canvas.winfo_width()
            canvas_height = app.preview_canvas.winfo_height()
            print(f"プレビューキャンバス: {canvas_width}x{canvas_height}")
        except:
            print("プレビューキャンバス: 未初期化")

def investigate_right_button_step_by_step():
    """右ボタンのステップバイステップ調査"""
    print("右ボタン問題 - 徹底調査開始")
    print("=" * 80)
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        app = Font2LEDApp(root)
        
        # テスト文字設定
        test_text = "小津ちゃん"
        led_data = app.text_to_led_matrix(test_text)
        app.current_led_data = led_data
        
        print(f"テスト環境:")
        print(f"  文字: '{test_text}'")
        print(f"  文字サイズ: {led_data['width']}x{led_data['height']}")
        
        # 初期状態の詳細確認
        detailed_state_inspection(app, "初期状態")
        
        print("\n" + "=" * 80)
        print("右に追加ボタンのステップ実行")
        print("=" * 80)
        
        # 右に追加を1回実行して詳細確認
        for step in range(3):
            print(f"\n--- ステップ {step + 1}: 右に追加ボタン実行 ---")
            
            # 実行前状態
            before_cols = app.custom_cols_var.get()
            before_x = app.x_offset_adjustment
            
            print(f"実行前: 列数={before_cols}, x_offset={before_x}")
            
            # 右に追加を実行
            print("右に追加ボタン実行中...")
            app.add_col_right()
            print("右に追加ボタン実行完了")
            
            # 実行後状態
            after_cols = app.custom_cols_var.get()
            after_x = app.x_offset_adjustment
            
            print(f"実行後: 列数={after_cols}, x_offset={after_x}")
            
            # 変化確認
            cols_change = after_cols - before_cols
            x_change = after_x - before_x
            
            print(f"変化: 列数{cols_change:+d}, x_offset{x_change:+d}")
            
            # ユーザーが見る効果の分析
            if cols_change > 0 and x_change == 0:
                print("期待される効果: 右側に空白列追加（テキスト位置変わらず）")
            elif cols_change > 0 and x_change > 0:
                print("実際の効果: 左側に空白列追加（テキストが右にシフト）")
            else:
                print(f"予期しない効果: 列数{cols_change:+d}, オフセット{x_change:+d}")
            
            # 詳細状態確認
            detailed_state_inspection(app, f"右に追加 {step + 1}回目")
            
            # プレビュー更新があった場合の確認
            print("\nプレビュー更新確認...")
            try:
                app.update_preview_if_exists()
                print("プレビュー更新実行完了")
            except Exception as e:
                print(f"プレビュー更新エラー: {e}")
        
        print("\n" + "=" * 80)
        print("右から削除ボタンのステップ実行")
        print("=" * 80)
        
        # 右から削除を実行して詳細確認
        for step in range(2):
            print(f"\n--- ステップ {step + 1}: 右から削除ボタン実行 ---")
            
            # 実行前状態
            before_cols = app.custom_cols_var.get()
            before_x = app.x_offset_adjustment
            
            print(f"実行前: 列数={before_cols}, x_offset={before_x}")
            
            # 右から削除を実行
            print("右から削除ボタン実行中...")
            app.remove_col_right()
            print("右から削除ボタン実行完了")
            
            # 実行後状態
            after_cols = app.custom_cols_var.get()
            after_x = app.x_offset_adjustment
            
            print(f"実行後: 列数={after_cols}, x_offset={after_x}")
            
            # 変化確認
            cols_change = after_cols - before_cols
            x_change = after_x - before_x
            
            print(f"変化: 列数{cols_change:+d}, x_offset{x_change:+d}")
            
            # ユーザーが見る効果の分析
            if cols_change < 0 and x_change == 0:
                print("期待される効果: 右側の列削除（テキスト位置変わらず）")
            elif cols_change < 0 and x_change < 0:
                print("実際の効果: 左側の列削除（テキストが左にシフト）")
            else:
                print(f"予期しない効果: 列数{cols_change:+d}, オフセット{x_change:+d}")
            
            # 詳細状態確認
            detailed_state_inspection(app, f"右から削除 {step + 1}回目")
        
        print("\n" + "=" * 80)
        print("左ボタンとの比較検証")
        print("=" * 80)
        
        # 左に追加で比較
        print(f"\n--- 比較: 左に追加ボタン実行 ---")
        before_cols = app.custom_cols_var.get()
        before_x = app.x_offset_adjustment
        
        print(f"実行前: 列数={before_cols}, x_offset={before_x}")
        app.add_col_left()
        
        after_cols = app.custom_cols_var.get()
        after_x = app.x_offset_adjustment
        
        print(f"実行後: 列数={after_cols}, x_offset={after_x}")
        print(f"変化: 列数{after_cols - before_cols:+d}, x_offset{after_x - before_x:+d}")
        
        return True
        
    except Exception as e:
        print(f"調査エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        root.destroy()

def investigate_x_offset_effect():
    """x_offset_adjustmentの実際の効果を調査"""
    print("\n" + "=" * 80)
    print("x_offset_adjustment効果調査")
    print("=" * 80)
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        app = Font2LEDApp(root)
        
        # テスト設定
        led_data = app.text_to_led_matrix("テスト")
        app.current_led_data = led_data
        
        print(f"テスト文字サイズ: {led_data['width']}x{led_data['height']}")
        
        # 異なるx_offset値での効果確認
        test_configs = [
            (20, 0),   # 基準
            (20, 1),   # x_offset +1
            (20, 2),   # x_offset +2
            (20, -1),  # x_offset -1（負の値）
            (25, 0),   # 列数増加
            (25, 1),   # 列数増加 + x_offset
        ]
        
        for cols, x_offset in test_configs:
            print(f"\n--- 設定: 列数={cols}, x_offset={x_offset} ---")
            
            app.custom_cols_var.set(cols)
            app.x_offset_adjustment = x_offset
            
            # プレビューでの実際の計算をシミュレート
            text_width = led_data['width']
            center_x = (cols - text_width) // 2
            actual_x = center_x + x_offset
            
            print(f"計算: ({cols} - {text_width}) // 2 + {x_offset} = {actual_x}")
            
            # テキストの表示範囲
            left_edge = actual_x
            right_edge = actual_x + text_width - 1
            
            print(f"テキスト表示範囲: X={left_edge}～{right_edge}")
            print(f"スクリーン範囲: X=0～{cols-1}")
            
            # はみ出し判定
            if left_edge < 0:
                print(f"⚠️ 左側はみ出し: {left_edge}")
            if right_edge >= cols:
                print(f"⚠️ 右側はみ出し: {right_edge}")
            
            # 効果の説明
            if x_offset > 0:
                print(f"効果: テキストが左側から{x_offset}ピクセル右にシフト")
            elif x_offset < 0:
                print(f"効果: テキストが中央から{abs(x_offset)}ピクセル左にシフト")
            else:
                print("効果: テキストがスクリーン中央に配置")
        
        return True
        
    except Exception as e:
        print(f"x_offset調査エラー: {e}")
        return False
    
    finally:
        root.destroy()

def main():
    """メイン調査実行"""
    print("Font2LED Tool - 右ボタン問題徹底調査")
    print("目的: ユーザー報告の問題を再現・分析・原因特定")
    print("")
    print("ユーザー報告:")
    print("1. 右に追加ボタン→左に列が追加される")
    print("2. 右から削除ボタン→左から削除される")
    print("")
    
    # ステップバイステップ調査
    investigate_right_button_step_by_step()
    
    # x_offset効果調査
    investigate_x_offset_effect()
    
    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    main()