import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from config import *


def get_mouse_ray(mx, my, width, height):
    """根据鼠标屏幕坐标计算世界坐标中的射线。"""
    # 获取当前视口
    viewport = glGetIntegerv(GL_VIEWPORT)
    # 获取当前的模型视图矩阵和投影矩阵，用于从裁剪空间和世界空间的转换。
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    # 鼠标的 Y 坐标转换为 OpenGL 的坐标系：OpenGL 原点在左下角，而通常屏幕坐标原点在左上角，所以要进行垂直翻转。
    real_y = viewport[3] - my
    # 使用 gluUnProject 将鼠标坐标转换为世界坐标中的近点和远点。
    near = gluUnProject(mx, real_y, 0.0, modelview, projection, viewport)
    far = gluUnProject(mx, real_y, 1.0, modelview, projection, viewport)
    # 计算射线方向
    direction = np.array(far) - np.array(near)
    # 归一化方向向量
    direction /= np.linalg.norm(direction)
    return np.array(near), direction


def get_pillar_index_at_pos(x, z, pillars, threshold=0.7):
    """获取给定(x, z)坐标所在的柱子索引。"""
    for idx, pillar in enumerate(pillars):
        px, pz = pillar.position
        # 检查与柱子中心的距离是否小于阈值，
        if np.linalg.norm([x - px, z - pz]) < threshold:
            return idx
    return -1


def check_win_condition(tori, pillars, target_pillar_idx):
    """检查是否满足胜利条件。"""
    # 检查目标柱子上的圆环数量是否与目标柱子的圆环数量相同
    rings_on_target_pillar = [
        torus for torus in tori
        if get_pillar_index_at_pos(torus.position[0], torus.position[2], pillars) == target_pillar_idx
    ]

    if len(rings_on_target_pillar) != len(tori):
        return False
    # 检查圆环的外半径是否按从大到小排序
    rings_on_target_pillar.sort(key=lambda x: x.position[1])
    # 获取目标柱子上圆环的外半径，并按从大到小排序
    expected_outer_radii = sorted([t.outer_radius for t in tori], reverse=True)
    # 检查每个圆环的外半径是否与预期相符
    for i, torus in enumerate(rings_on_target_pillar):
        # 检查圆环的外半径是否接近预期值
        if not np.isclose(torus.outer_radius, expected_outer_radii[i], atol=0.01):
            return False

    return True


def draw_text(text, position, font, screen_size, is_ui=False, color=(255, 255, 255), align="center"):
    """在OpenGL上下文中绘制2D文本。"""
    width, height = screen_size
    text_surface = font.render(text, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    # 如果是UI文本，则使用pygame的坐标系统
    if is_ui:
        if align == "center":
            text_rect = text_surface.get_rect(center=position)
        elif align == "topleft":
            text_rect = text_surface.get_rect(topleft=position)
        else:
            text_rect = text_surface.get_rect(center=position)  # 默认为居中

        x, y = text_rect.left, text_rect.top
    else:
        # 将世界坐标投影到屏幕
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        screen_x, screen_y, _ = gluProject(
            position[0], position[1], position[2], modelview, projection, viewport)

        text_rect = text_surface.get_rect(
            center=(int(screen_x), height - int(screen_y)))
        x, y = text_rect.left, text_rect.top

    # 切换到2D绘图模式
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # 绘制像素
    glWindowPos2d(x, height - y - text_surface.get_height())
    glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                 GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    # 恢复矩阵
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
