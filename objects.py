import numpy as np
from OpenGL.GL import *
from config import *


class Torus:
    def __init__(self, inner_radius, outer_radius, initial_position):
        """初始化一个圆环对象。"""
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.position = list(initial_position)
        self.flip_angle = 0.0
        # 'IDLE', 'FLIPPING', 'DESCENDING', 'ERROR_PAUSE', 'REVERTING'
        # 常态 , 翻转中 , 下降中 , 错误暂停 , 恢复中
        self.animation_state = 'IDLE'
        # 常态下无高亮状态
        self.is_highlighted = False

        # 动画状态变量
        # 翻转起始时间
        self.flip_start_time = 0.0
        # 翻转目标角度
        self.flip_target_angle = 0.0
        # 翻转起始角度
        self.flip_initial_angle = 0.0
        # 下降起始时间
        self.descent_start_time = 0.0
        # 下降初始Y位置
        self.descent_initial_y = 0.0
        # 下降目标Y位置
        self.descent_target_y = 0.0
        # 错误暂停起始时间
        self.error_pause_start_time = 0.0
        # 错误恢复动画持续时间
        self.revert_start_time = 0.0
        # 错误恢复动画初始位置
        self.revert_initial_pos = [0.0, 0.0, 0.0]
        # 错误恢复目标位置
        self.target_revert_position = [0.0, 0.0, 0.0]

    def draw(self, is_highlighted=False):
        """绘制圆环。"""
        # 更新高亮状态
        self.is_highlighted = is_highlighted
        # 保存当前矩阵
        glPushMatrix()
        # 绘图位置移动圆环中心点
        glTranslatef(*self.position)
        # 绕x轴旋转，让圆环从平面朝上变成立体朝外
        glRotatef(90, 1, 0, 0)
        # 绕y轴旋转
        glRotatef(self.flip_angle, 0, 1, 0)

        # 圆环表面建模：双层循环绘制四边形带
        for i in range(30):
            glBegin(GL_QUAD_STRIP)
            for j in range(31):
                for k in [i, i + 1]:
                    # 计算圆环表面点的参数
                    # k 是环的索引，j 是圆环表面点的索引
                    s = k % 30 + 0.5
                    t = j % 30
                    theta = 2 * np.pi * s / 30
                    phi = 2 * np.pi * t / 30
                    # 计算圆环表面点的坐标
                    x = (self.outer_radius + self.inner_radius *
                         np.cos(phi)) * np.cos(theta)
                    y = (self.outer_radius + self.inner_radius *
                         np.cos(phi)) * np.sin(theta)
                    z = self.inner_radius * np.sin(phi)
                    # 颜色基于角度的正弦值变化
                    base_color = (1.0, 0.0, 0.0) if np.sin(
                        phi) >= 0 else (0.0, 0.0, 1.0)
                    # 如果是高亮状态，使用原色，否则使用暗色
                    if self.is_highlighted:
                        glColor3f(*base_color)
                    else:
                        # 使用暗色调
                        glColor3f(base_color[0] * DARK_FACTOR, base_color[1]
                                  * DARK_FACTOR, base_color[2] * DARK_FACTOR)
                    # 绘制顶点
                    glVertex3f(x, y, z)
            glEnd()
        glPopMatrix()

    def get_effective_top_color(self, angle_override=None):
        """获取当前有效的顶部颜色。"""
        # 如果提供了角度覆盖，则使用它，否则使用当前翻转角度
        angle = angle_override if angle_override is not None else self.flip_angle
        # 检查角度是否接近180度
        # 如果接近180度，则返回蓝色，否则返回红色
        if np.isclose(angle % 360, 180.0, atol=ANGLE_TOLERANCE):
            return COLOR_BLUE
        return COLOR_RED

    def get_effective_bottom_color(self, angle_override=None):
        """获取当前有效的底部颜色。"""
        # 如果提供了角度覆盖，则使用它，否则使用当前翻转角度
        angle = angle_override if angle_override is not None else self.flip_angle
        # 检查角度是否接近180度
        # 如果接近180度，则返回红色，否则返回蓝色
        if np.isclose(angle % 360, 180.0, atol=ANGLE_TOLERANCE):
            return COLOR_RED
        return COLOR_BLUE

    def update_animation(self, current_time):
        """根据当前时间更新动画。"""
        # 如果当前状态是翻转中
        if self.animation_state == 'FLIPPING':
            # 计算翻转进度，进度最大为1.0，超过则视为完成
            progress = min(
                1.0, (current_time - self.flip_start_time) / FLIP_DURATION)
            # 使用平滑的余弦函数来计算进度，使得动画在开始和结束时更平滑
            smoothed_progress = 0.5 - 0.5 * np.cos(progress * np.pi)
            self.flip_angle = self.flip_initial_angle + \
                (self.flip_target_angle - self.flip_initial_angle) * smoothed_progress
            # 如果进度达到1.0，表示翻转完成
            if progress >= 1.0:
                # 将角度归一化到0-360度范围内
                self.flip_angle = self.flip_target_angle % 360
                # 圆环状态变成下降
                self.animation_state = 'DESCENDING'
                # 记录下降的起始时间
                self.descent_start_time = current_time
        # 如果当前状态是下降中
        elif self.animation_state == 'DESCENDING':
            progress = min(
                1.0, (current_time - self.descent_start_time) / DESCENT_DURATION)
            # 使用平滑的余弦函数来计算下降进度
            smoothed_progress = 0.5 - 0.5 * np.cos(progress * np.pi)
            self.position[1] = self.descent_initial_y + \
                (self.descent_target_y - self.descent_initial_y) * smoothed_progress
            if progress >= 1.0:
                self.position[1] = self.descent_target_y
                self.animation_state = 'IDLE'

        elif self.animation_state == 'ERROR_PAUSE':
            if (current_time - self.error_pause_start_time) >= ERROR_PAUSE_DURATION:
                self.animation_state = 'REVERTING'
                self.revert_start_time = current_time
                self.revert_initial_pos = list(self.position)

        elif self.animation_state == 'REVERTING':
            progress = min(
                1.0, (current_time - self.revert_start_time) / REVERT_ANIMATION_DURATION)
            smoothed_progress = 0.5 - 0.5 * np.cos(progress * np.pi)

            # 先处理x和z轴的平移 (索引0和2)
            for i in [0, 2]:
                self.position[i] = self.revert_initial_pos[i] + (
                    self.target_revert_position[i] - self.revert_initial_pos[i]) * smoothed_progress

            # 当x和z轴的平移完成后，开始处理y轴的平移
            if progress >= 1.0:
                # 切换到新的动画状态，专门处理y轴平移
                self.animation_state = 'REVERTING_Y'
                self.y_revert_start_time = current_time
                self.y_revert_initial_pos = self.position[1]
                self.target_y_revert_position = self.target_revert_position[1]

        # 添加新的动画状态处理y轴平移
        elif self.animation_state == 'REVERTING_Y':
            y_progress = min(
                1.0, (current_time - self.y_revert_start_time) / REVERT_ANIMATION_DURATION)
            smoothed_y_progress = 0.5 - 0.5 * np.cos(y_progress * np.pi)

            # 处理y轴的平移
            self.position[1] = self.y_revert_initial_pos + (
                self.target_y_revert_position - self.y_revert_initial_pos) * smoothed_y_progress

            if y_progress >= 1.0:
                # y轴平移完成，设置最终位置并回到空闲状态
                self.position[1] = self.target_y_revert_position
                self.animation_state = 'IDLE'

    # 翻转动画
    def start_flip_animation(self, current_time, target_angle):
        self.animation_state = 'FLIPPING'
        self.flip_start_time = current_time
        self.flip_initial_angle = self.flip_angle
        self.flip_target_angle = target_angle
    # 下降动画

    def start_descent_animation(self, current_time, target_y):
        self.descent_start_time = current_time
        self.descent_initial_y = self.position[1]
        self.descent_target_y = target_y
    # 错误恢复动画

    def start_error_revert(self, current_time, original_xyz):
        self.animation_state = 'ERROR_PAUSE'
        self.error_pause_start_time = current_time
        self.target_revert_position = list(original_xyz)


class Pillar:
    def __init__(self, x, z, color, label):
        """初始化一个柱子对象。"""
        self.position = (x, z)
        self.color = color
        self.label = label
        self.height = PILLAR_HEIGHT

    def draw(self):
        """绘制圆柱体。"""
        glPushMatrix()
        glTranslatef(self.position[0], 0, self.position[1])
        glColor3f(*self.color)
        slices = 30
        for i in range(slices):
            # 计算每个切片的角度
            # theta1 和 theta2 分别是当前切片和下一个切片的角度
            theta1 = 2 * np.pi * i / slices
            theta2 = 2 * np.pi * (i + 1) / slices
            x1, z1 = 0.3 * np.cos(theta1), 0.3 * np.sin(theta1)
            x2, z2 = 0.3 * np.cos(theta2), 0.3 * np.sin(theta2)
            glBegin(GL_QUADS)
            # 绘制柱子的侧面
            glVertex3f(x1, 0, z1)
            glVertex3f(x2, 0, z2)
            glVertex3f(x2, self.height, z2)
            glVertex3f(x1, self.height, z1)

            glEnd()
        glPopMatrix()
