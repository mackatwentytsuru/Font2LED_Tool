"""
Blender LED JSON Importer
Font2LEDツールで生成したJSONファイルをBlenderにインポートするスクリプト

使い方:
1. Blenderで10x65のLEDドローングリッドを事前に作成
2. Blenderのスクリプトエディタでこのファイルを開く
3. json_pathを適切に設定
4. スクリプトを実行
"""

import bpy
import json
import os
from pathlib import Path

class LEDAnimationImporter:
    """Font2LED JSONをBlenderにインポート"""
    
    def __init__(self, drones_collection_name: str = "Drones"):
        self.drones_collection = bpy.data.collections.get(drones_collection_name)
        self.drone_grid = {}
        self.grid_params = None
        
        if self.drones_collection:
            self._analyze_grid()
        else:
            print(f"Warning: Collection '{drones_collection_name}' not found")
    
    def _analyze_grid(self):
        """ドローングリッドの配置を解析"""
        drones = [obj for obj in self.drones_collection.objects 
                  if obj.type == 'MESH' and 'Drone' in obj.name]
        
        if not drones:
            print("No drones found in collection")
            return
        
        # 座標の範囲を取得
        x_coords = [obj.location.x for obj in drones]
        z_coords = [obj.location.z for obj in drones]
        
        x_min, x_max = min(x_coords), max(x_coords)
        z_min, z_max = min(z_coords), max(z_coords)
        
        # グリッド間隔を推定
        x_unique = sorted(list(set(x_coords)))
        z_unique = sorted(list(set(z_coords)))
        
        x_spacing = x_unique[1] - x_unique[0] if len(x_unique) > 1 else 1.471
        z_spacing = z_unique[1] - z_unique[0] if len(z_unique) > 1 else 1.5
        
        self.grid_params = {
            'x_min': x_min,
            'x_max': x_max,
            'z_min': z_min,
            'z_max': z_max,
            'x_spacing': x_spacing,
            'z_spacing': z_spacing,
            'cols': len(x_unique),
            'rows': len(z_unique)
        }
        
        # グリッドマッピングを構築
        for drone in drones:
            grid_x = round((drone.location.x - x_min) / x_spacing)
            grid_y = round((drone.location.z - z_min) / z_spacing)
            self.drone_grid[(grid_x, grid_y)] = drone
        
        print(f"Grid analysis complete:")
        print(f"  Size: {self.grid_params['cols']}x{self.grid_params['rows']}")
        print(f"  Spacing: {x_spacing:.3f} x {z_spacing:.3f}")
        print(f"  Mapped drones: {len(self.drone_grid)}")
    
    def import_animation(self, json_path: str):
        """JSONファイルからアニメーションをインポート"""
        if not os.path.exists(json_path):
            print(f"Error: File not found: {json_path}")
            return False
        
        # JSONを読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        frames = data.get('frames', [])
        
        print(f"Loading animation:")
        print(f"  Grid: {metadata.get('grid_width')}x{metadata.get('grid_height')}")
        print(f"  Frames: {len(frames)}")
        print(f"  Font: {metadata.get('font')}")
        
        # 各フレームを処理
        for frame_data in frames:
            self._apply_frame(frame_data)
        
        # タイムラインマーカーを作成
        self._create_markers(frames)
        
        print("Import completed!")
        return True
    
    def _apply_frame(self, frame_data: dict):
        """単一フレームのデータを適用"""
        frame_num = frame_data['frame']
        text = frame_data.get('text', '')
        pixels = frame_data.get('pixels', [])
        
        # フレームを設定
        bpy.context.scene.frame_set(frame_num)
        
        # まず全ドローンを消灯
        self._clear_all_drones(frame_num)
        
        # ピクセルデータを適用
        applied = 0
        for pixel in pixels:
            x, y = pixel['x'], pixel['y']
            
            # Y座標を反転（JSONは上が0、Blenderは下が0）
            grid_y = 9 - y  # 10行のグリッドなので9から引く
            
            if (x, grid_y) in self.drone_grid:
                drone = self.drone_grid[(x, grid_y)]
                color = (pixel['r'], pixel['g'], pixel['b'])
                intensity = pixel.get('intensity', 1.0)
                
                self._set_drone_emission(drone, color, intensity, frame_num)
                applied += 1
        
        print(f"Frame {frame_num}: '{text}' - {applied}/{len(pixels)} pixels applied")
    
    def _clear_all_drones(self, frame: int):
        """全ドローンを消灯状態に"""
        for drone in self.drone_grid.values():
            self._set_drone_emission(drone, (0, 0, 0), 0, frame)
    
    def _set_drone_emission(self, drone, color: tuple, intensity: float, frame: int):
        """ドローンのEmission設定とキーフレーム"""
        if not drone.data or not drone.data.materials:
            return
        
        mat = drone.data.materials[0]
        if not mat or not mat.use_nodes:
            return
        
        # Emissionノードを探す
        emission_node = None
        for node in mat.node_tree.nodes:
            if node.type == 'EMISSION':
                emission_node = node
                break
        
        if not emission_node:
            return
        
        # 値を設定
        emission_node.inputs[0].default_value = (*color, 1.0)
        emission_node.inputs[1].default_value = min(intensity, 1.0)  # 実機制限
        
        # キーフレームを挿入
        emission_node.inputs[0].keyframe_insert(data_path="default_value", frame=frame)
        emission_node.inputs[1].keyframe_insert(data_path="default_value", frame=frame)
    
    def _create_markers(self, frames: list):
        """タイムラインマーカーを作成"""
        scene = bpy.context.scene
        
        # 既存のマーカーをクリア（オプション）
        # scene.timeline_markers.clear()
        
        for frame_data in frames:
            frame_num = frame_data['frame']
            text = frame_data.get('text', f'Frame {frame_num}')
            
            # 既存のマーカーを確認
            existing = None
            for marker in scene.timeline_markers:
                if marker.frame == frame_num:
                    existing = marker
                    break
            
            if existing:
                existing.name = text
            else:
                scene.timeline_markers.new(name=text, frame=frame_num)

# 実行関数
def import_led_animation(json_path: str = None):
    """メイン実行関数"""
    
    # デフォルトパス
    if json_path is None:
        # Font2LED_Toolフォルダのデフォルトファイルを探す
        default_path = "H:/Yuki Tsuruoka Dropbox/鶴岡悠生/Claude/0722-windous/Font2LED_Tool/led_animation.json"
        if os.path.exists(default_path):
            json_path = default_path
        else:
            print("Please specify json_path")
            return
    
    print(f"Importing from: {json_path}")
    
    # インポーターを初期化
    importer = LEDAnimationImporter("Drones")
    
    # アニメーションをインポート
    success = importer.import_animation(json_path)
    
    if success:
        # ビューポートを更新
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        print("\nImport successful!")
        print("Check the timeline for text markers.")

# スクリプト実行
if __name__ == "__main__":
    # JSONファイルのパスを指定
    # json_path = "H:/Yuki Tsuruoka Dropbox/鶴岡悠生/Claude/0722-windous/Font2LED_Tool/led_animation.json"
    import_led_animation()  # デフォルトパスを使用