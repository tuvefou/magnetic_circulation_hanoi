import numpy as np
from config import *
from objects import Torus, Pillar
from utils import get_pillar_index_at_pos


class GameState:
    """封装游戏的所有动态状态。"""

    def __init__(self):
        # 创建柱子和圆环
        self.pillars = self._create_pillars()
        self.tori = self._create_tori()

        # 拖拽状态
        self.dragging = False
        self.dragged_torus_index = -1
        self.drag_offset = np.array([0.0, 0.0, 0.0])
        self.mouse_down_pos = (0, 0)
        self.original_drag_position = np.array([0.0, 0.0, 0.0])
        self.original_pillar_index = -1
        self.last_mouse_pos_for_drag = (0, 0)
        # 标记是否进入水平拖拽模式
        self.is_horizontal_drag_mode = False

        # 游戏进程状态
        self.move_count = 0
        self.game_won = False

        # UI 状态
        self.display_error_message = False
        self.error_message_start_time = 0.0

    def _create_pillars(self):
        """创建并返回柱子对象列表。"""
        pillars = []
        angles = [0, 120, 240]
        for i, angle in enumerate(angles):
            rad = np.radians(angle)
            x = PILLAR_RADIUS * np.cos(rad)
            z = PILLAR_RADIUS * np.sin(rad)
            pillars.append(Pillar(x, z, PILLAR_COLORS[i], PILLAR_LABELS[i]))
        return pillars

    def _create_tori(self):
        """在第一个柱子上创建并返回圆环对象列表。"""
        tori = []
        initial_pillar_x, initial_pillar_z = self.pillars[0].position
        # 按照内半径从大到小排序
        sorted_sizes = sorted(
            TORUS_SIZES, key=lambda item: item[1], reverse=True)

        last_y = 0.0
        last_inner_radius = 0.0
        # 初始圆环位置
        for i, (inner_radius, outer_radius) in enumerate(sorted_sizes):
            if i == 0:
                y = inner_radius
            else:
                y = last_y + last_inner_radius + inner_radius
            pos = [initial_pillar_x, y, initial_pillar_z]
            tori.append(Torus(inner_radius, outer_radius, pos))
            last_y = y
            last_inner_radius = inner_radius
        # 按照外半径排序
        tori.sort(key=lambda t: t.outer_radius)
        return tori

    def find_topmost_colliding_torus(self, ray_origin, ray_dir):
        """根据鼠标射线找到最顶层的可拾取圆环。"""
        topmost_ring_idx = -1
        topmost_ring_y = -float('inf')

        for i, torus in enumerate(self.tori):
            # 检查圆环是否处于空闲状态
            if torus.animation_state != 'IDLE':
                continue
            # 判断射线是否朝向圆环
            torus_center = np.array(torus.position)
            v = torus_center - ray_origin
            t_proj = np.dot(v, ray_dir)
            if t_proj < 0:
                continue
            # 计算射线与圆环中心的最近点
            closest_point_on_ray = ray_origin + t_proj * ray_dir
            dist_to_center = np.linalg.norm(
                torus_center - closest_point_on_ray)
            # 判断是否碰撞
            if dist_to_center < torus.outer_radius + torus.inner_radius:
                # 判断该圆环是否为该柱子“最顶层”的圆环
                is_topmost = True
                current_pillar_idx = get_pillar_index_at_pos(
                    torus.position[0], torus.position[2], self.pillars)
                # 获取该圆环当前在哪根柱子
                if current_pillar_idx != -1:
                    for other_torus in self.tori:
                        # 检查其他圆环是否在同一柱子上且高度更高
                        if other_torus is not torus:
                            # 获取其他圆环所在的柱子索引
                            other_pillar_idx = get_pillar_index_at_pos(
                                other_torus.position[0], other_torus.position[2], self.pillars)
                            # 如果其他圆环在同一柱子上且高度更高，则不是顶层圆环
                            if other_pillar_idx == current_pillar_idx and other_torus.position[1] > torus.position[1]:
                                is_topmost = False
                                break
                # 如果是最顶层的圆环，检查其高度
                if is_topmost and torus.position[1] > topmost_ring_y:
                    topmost_ring_y = torus.position[1]
                    topmost_ring_idx = i

        return topmost_ring_idx

    def start_dragging(self, torus_index, ray_origin, ray_dir):
        """开始拖拽一个圆环。"""

        self.dragged_torus_index = torus_index
        torus = self.tori[torus_index]
        # 存放原始位置
        self.original_drag_position = np.array(torus.position)
        self.original_pillar_index = get_pillar_index_at_pos(
            torus.position[0], torus.position[2], self.pillars)
        # 记录开始拖拽时鼠标位置（用于判断是“水平拖拽”还是“垂直拖拽”）。
        self.last_mouse_pos_for_drag = self.mouse_down_pos
        self.is_horizontal_drag_mode = False
        # 用于计算鼠标射线与“水平面”相交的位置（圆环所在的 Y 层面）。
        plane_normal = np.array([0, 1, 0])
        denom = np.dot(ray_dir, plane_normal)
        # 记录圆环中心相对鼠标命中点的偏移量（X/Z 方向），这样拖动时能让鼠标拖住的点与圆环保持一致。
        if abs(denom) > 1e-6:
            t = (torus.position[1] - ray_origin[1]) / denom
            hit_point = ray_origin + t * ray_dir
            self.drag_offset = torus.position - hit_point
            self.drag_offset[1] = 0.0

    def stop_dragging(self):
        """停止拖拽。"""
        if self.dragged_torus_index != -1:
            torus = self.tori[self.dragged_torus_index]
            # 如果拖拽未进入水平模式，则让它回到原位
            if not self.is_horizontal_drag_mode and self.dragging:
                torus.position = list(self.original_drag_position)

            torus.is_highlighted = False
        # 重置拖拽状态
        self.dragging = False
        self.dragged_torus_index = -1

    def is_drag_active(self, mouse_pos):
        """检查拖拽是否已激活（移动超过阈值）。"""
        return np.linalg.norm(np.array(mouse_pos) - np.array(self.mouse_down_pos)) > DRAG_THRESHOLD

    def update_dragged_torus_position(self, ray_origin, ray_dir, mouse_pos):
        """更新被拖拽圆环的位置，实现两段式拖拽。"""
        torus = self.tori[self.dragged_torus_index]
        # 计算鼠标移动的偏移量
        mouse_dy = self.last_mouse_pos_for_drag[1] - mouse_pos[1]
        self.last_mouse_pos_for_drag = mouse_pos
        # 垂直移动阶段，xz轴位置保持不变
        if not self.is_horizontal_drag_mode:
            new_y = torus.position[1] + mouse_dy * LIFT_SENSITIVITY
            new_y = max(self.original_drag_position[1], new_y)

            if new_y >= FLOAT_HEIGHT:
                self.is_horizontal_drag_mode = True
            else:
                # 保持在垂直提升阶段
                torus.position[1] = new_y
                torus.position[0] = self.original_drag_position[0]
                torus.position[2] = self.original_drag_position[2]
                torus.is_highlighted = False
        # 水平移动阶段， y轴位置保持在 FLOAT_HEIGHT
        else:
            torus.position[1] = FLOAT_HEIGHT
            plane_normal = np.array([0, 1, 0])
            denom = np.dot(ray_dir, plane_normal)
            if abs(denom) > 1e-6:
                t = (FLOAT_HEIGHT - ray_origin[1]) / denom
                hit = ray_origin + t * ray_dir
                target_pos_raw = hit + self.drag_offset
                torus.position[0] = target_pos_raw[0]
                torus.position[2] = target_pos_raw[2]
            # 检查当前拖拽位置的合法性
            self.check_highlight_validity()

    def check_highlight_validity(self):
        """检查当前拖拽到的位置是否合法，并更新高亮状态。"""
        torus = self.tori[self.dragged_torus_index]
        target_pillar_idx = get_pillar_index_at_pos(
            torus.position[0], torus.position[2], self.pillars)

        is_valid = False
        if target_pillar_idx != -1:
            is_valid = self.is_move_valid(
                self.dragged_torus_index, target_pillar_idx, check_only=True)

        torus.is_highlighted = is_valid

    def get_landing_y(self, torus, target_pillar_idx):
        """计算圆环在目标柱子上的着陆Y坐标。"""
        # 找出在该柱子上的其它圆环
        rings_on_pillar = [t for t in self.tori if t is not torus and get_pillar_index_at_pos(
            t.position[0], t.position[2], self.pillars) == target_pillar_idx]
        # 如果没有其它圆环，则返回圆环的内半径加上柱子的内半径
        if not rings_on_pillar:
            return torus.inner_radius
        # 如果有其它圆环，则返回最高圆环的高度加上当前圆环的内半径和外半径
        else:
            topmost_ring = max(rings_on_pillar, key=lambda t: t.position[1])
            return topmost_ring.position[1] + topmost_ring.inner_radius + torus.inner_radius + EPSILON

    def is_move_valid(self, moving_torus_idx, target_pillar_idx, check_only=False):
        """检查一个移动是否合法。"""
        moving_torus = self.tori[moving_torus_idx]
        # 如果不是原地翻转
        if self.original_pillar_index != target_pillar_idx:
            # 判断是否是顺时针 移动
            expected_next_pillar = (
                self.original_pillar_index + 1) % len(self.pillars)
            # 如果目标柱子不是下一个顺时针柱子，则非法
            if target_pillar_idx != expected_next_pillar:
                if not check_only:
                    print("Illegal move: Must move clockwise.")
                return False
        # 找出在该柱子上的其它圆环
        rings_on_target = [t for t in self.tori if t is not moving_torus and get_pillar_index_at_pos(
            t.position[0], t.position[2], self.pillars, threshold=0.9) == target_pillar_idx]
        # 先进行翻转
        future_flip_angle = (moving_torus.flip_angle + 180) % 360
        # 获取翻转后的圆环底部颜色
        moving_bottom_color = moving_torus.get_effective_bottom_color(
            angle_override=future_flip_angle)
        # 如果目标柱子上没有圆环，则可以放置
        if not rings_on_target:
            return True
        else:
            # 如果目标柱子上有圆环，获取顶部圆环
            topmost_on_target = max(
                rings_on_target, key=lambda t: t.position[1])
            # 检查大小是否合法
            if self.original_pillar_index != target_pillar_idx:
                if moving_torus.outer_radius > topmost_on_target.outer_radius:
                    if not check_only:
                        print(
                            "Illegal move: Cannot place larger ring on smaller one.")
                    return False
            # 检查颜色是否相同
            # 获取目标柱子顶部圆环的顶部颜色
            target_top_color = topmost_on_target.get_effective_top_color()
            # 相同则不合法
            if moving_bottom_color == target_top_color:
                if not check_only:
                    print("Illegal move: Color repulsion.")
                return False

        return True

    def place_torus(self, current_time):
        """放置被拖拽的圆环，检查规则并触发相应动画。"""
        torus = self.tori[self.dragged_torus_index]
        target_pillar_idx = get_pillar_index_at_pos(
            torus.position[0], torus.position[2], self.pillars)
        # 如果目标柱子索引有效且移动合法
        if target_pillar_idx != -1 and self.is_move_valid(self.dragged_torus_index, target_pillar_idx):
            target_pos_x = self.pillars[target_pillar_idx].position[0]
            target_pos_z = self.pillars[target_pillar_idx].position[1]
            target_y = self.get_landing_y(torus, target_pillar_idx)

            torus.position[0] = target_pos_x
            torus.position[2] = target_pos_z
            # 翻转并下降
            future_flip_angle = (torus.flip_angle + 180) % 360
            torus.start_flip_animation(current_time, future_flip_angle)
            torus.start_descent_animation(current_time, target_y)
            # 步数加一
            self.move_count += 1
        else:
            # 如果移动不合法，触发错误动画
            torus.start_error_revert(current_time, self.original_drag_position)
            self.display_error_message = True
            self.error_message_start_time = current_time
