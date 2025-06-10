import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time
from config import *
from objects import Torus, Pillar
from game_state import GameState
from utils import get_mouse_ray, get_pillar_index_at_pos, check_win_condition, draw_text


class GameApp:
    """封装整个游戏应用的主类。"""

    def __init__(self):
        """初始化游戏环境和状态。"""
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode(
            (self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Magnetic Circulation Hanoi Tower - 3D")
        self.setup_opengl()

        # 初始化字体
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()

        # 初始化游戏状态
        self.game_state = GameState()
        self.camera = {'yaw': 0.0, 'pitch': 0.0, 'distance': 25.0,
                       'right_dragging': False, 'last_mouse_pos': (0, 0)}

        self.running = True

    def setup_opengl(self):
        """配置OpenGL初始设置。"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.2, 0.2, 0.2, 1)
        # 设置投影矩阵
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.width / self.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_events(self):
        """处理所有的用户输入事件。"""
        current_time = time.time()
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            elif event.type == MOUSEBUTTONDOWN:
                self.handle_mouse_down(event, current_time)

            elif event.type == MOUSEBUTTONUP:
                self.handle_mouse_up(event, current_time)

            elif event.type == MOUSEMOTION:
                self.handle_mouse_motion(event)

    def handle_mouse_down(self, event, current_time):
        """处理鼠标按下事件。"""
        # 左键点击拖拽圆环
        if event.button == 1:
            # 如果游戏已经结束，则不处理鼠标事件
            if self.game_state.game_won:
                return
            mx, my = event.pos
            # 传递鼠标位置
            self.game_state.mouse_down_pos = (mx, my)
            # 获取鼠标射线
            ray_origin, ray_dir = get_mouse_ray(
                mx, my, self.width, self.height)
            # 检查是否点击了圆环
            topmost_ring_idx = self.game_state.find_topmost_colliding_torus(
                ray_origin, ray_dir)
            # 如果点击了圆环，开始拖拽
            if topmost_ring_idx != -1:
                self.game_state.start_dragging(
                    topmost_ring_idx, ray_origin, ray_dir)
                print(
                    f"DEBUG: Selected ring {topmost_ring_idx}, original pillar: {self.game_state.original_pillar_index}")
        # 右键点击移动视角
        elif event.button == 3:
            self.camera['right_dragging'] = True
            self.camera['last_mouse_pos'] = event.pos
        # 滚轮缩放调整远近
        elif event.button == 4:
            self.camera['distance'] = max(5, self.camera['distance'] - 1.0)
        elif event.button == 5:
            self.camera['distance'] = min(50, self.camera['distance'] + 1.0)

    def handle_mouse_up(self, event, current_time):
        """处理鼠标松开事件。"""
        # 左键松开放置圆环
        if event.button == 1:
            if self.game_state.dragged_torus_index != -1 and self.game_state.dragging:
                # 只在圆环高于柱子时才允许放置
                if self.game_state.tori[self.game_state.dragged_torus_index].position[1] >= FLOAT_HEIGHT:
                    self.game_state.place_torus(current_time)

            # 重置拖拽状态
            self.game_state.stop_dragging()

        elif event.button == 3:
            self.camera['right_dragging'] = False

    def handle_mouse_motion(self, event):
        """处理鼠标移动事件。"""
        # 如果能拖拽圆环并且能激活拖拽
        if self.game_state.dragged_torus_index != -1 and self.game_state.is_drag_active(event.pos):
            self.game_state.dragging = True
            mx, my = event.pos
            ray_origin, ray_dir = get_mouse_ray(
                mx, my, self.width, self.height)
            # 传递 event.pos 用于计算拖拽
            self.game_state.update_dragged_torus_position(
                ray_origin, ray_dir, event.pos)
        # 如果右键拖拽视角
        if self.camera['right_dragging']:
            mx, my = event.pos
            dx = mx - self.camera['last_mouse_pos'][0]
            dy = my - self.camera['last_mouse_pos'][1]
            self.camera['yaw'] += dx * 0.3
            self.camera['pitch'] = max(-89,
                                       min(89, self.camera['pitch'] + dy * 0.3))
            self.camera['last_mouse_pos'] = (mx, my)

    def update(self):
        """更新游戏状态，如动画和胜利条件。"""
        current_time = time.time()
        for torus in self.game_state.tori:
            torus.update_animation(current_time)

        if not self.game_state.game_won:
            if check_win_condition(self.game_state.tori, self.game_state.pillars, WIN_PILLAR_INDEX):
                self.game_state.game_won = True
                print(f"游戏胜利！总步数: {self.game_state.move_count}")

    def render(self):
        """渲染所有游戏对象和UI。R"""
        current_time = time.time()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # 相机变换
        glTranslatef(0, 0, -self.camera['distance'])
        glRotatef(self.camera['pitch'], 1, 0, 0)
        glRotatef(self.camera['yaw'], 0, 1, 0)

        # 绘制柱子和标签
        for pillar in self.game_state.pillars:
            pillar.draw()
            draw_text(
                pillar.label, (pillar.position[0], -0.5, pillar.position[1]), self.font_medium, (self.width, self.height))

        # 绘制圆环
        for i, torus in enumerate(self.game_state.tori):
            # 检查是否需要高亮显示
            is_highlighted_for_draw = (i == self.game_state.dragged_torus_index and torus.is_highlighted) or torus.animation_state in [
                'FLIPPING', 'DESCENDING']
            torus.draw(is_highlighted_for_draw)

        # 绘制UI文本
        self.render_ui(current_time)

        pygame.display.flip()

    def render_ui(self, current_time):
        """渲染UI元素，如错误信息、步数和胜利消息。"""
        # 绘制错误信息
        if self.game_state.display_error_message and (current_time - self.game_state.error_message_start_time < ERROR_MESSAGE_DURATION):
            draw_text(ERROR_MESSAGE_TEXT, (self.width // 2, self.height // 2 - 50),
                      self.font_large, (self.width, self.height), is_ui=True, color=(255, 0, 0))
        # 绘制步数
        move_text = f"Moves: {self.game_state.move_count}"
        draw_text(move_text, (10, 10), self.font_medium, (self.width,
                  self.height), is_ui=True, color=(255, 255, 255), align="topleft")
        # 绘制游戏胜利消息
        if self.game_state.game_won:
            win_message = "You Win!"
            win_moves_message = f"Total Moves: {self.game_state.move_count}"
            draw_text(win_message, (self.width // 2, self.height // 2 - 50),
                      self.font_large, (self.width, self.height), is_ui=True, color=(0, 255, 0))
            draw_text(win_moves_message, (self.width // 2, self.height // 2 + 10),
                      self.font_large, (self.width, self.height), is_ui=True, color=(0, 255, 0))

    def run(self):
        """游戏主循环。"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    app = GameApp()
    app.run()
