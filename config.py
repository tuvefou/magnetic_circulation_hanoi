import numpy as np

# --- 游戏常量 ---
# 精度容忍值
EPSILON = 0.02
ANGLE_TOLERANCE = 5.0  # degrees

# 颜色规则常量
COLOR_RED = 0
COLOR_BLUE = 1

# 翻转、下降、错误信息、错误停滞、恢复
FLIP_DURATION = 0.3
DESCENT_DURATION = 0.3
ERROR_MESSAGE_DURATION = 1.0
ERROR_PAUSE_DURATION = 1.0
REVERT_ANIMATION_DURATION = 0.3

# 常态暗度
DARK_FACTOR = 0.6

# 游戏设置

# 鼠标拖拽阈值
DRAG_THRESHOLD = 5

# 拖拽灵敏度和高度常量
# 垂直拖拽灵敏度
LIFT_SENSITIVITY = 0.05
# 超出柱子后的浮动高度偏移
FLOAT_HEIGHT_OFFSET = 1.0

# 柱子设置
# 黄、紫、绿
PILLAR_COLORS = [(1, 1, 0), (0.6, 0, 0.8), (0, 1, 0)]
PILLAR_LABELS = ["A", "B", "C"]
PILLAR_RADIUS = 6.0
PILLAR_HEIGHT = 5.0
# 圆环在空中平移时的固定Y值
FLOAT_HEIGHT = PILLAR_HEIGHT + FLOAT_HEIGHT_OFFSET

# 圆环尺寸
TORUS_SIZES = [(0.5, 1.0), (0.6, 1.2), (0.7, 1.4)]

# 游戏规则设置
# 目标胜利柱子是 C (索引2)
WIN_PILLAR_INDEX = 2

# UI 文本
ERROR_MESSAGE_TEXT = "Illegal Operation"
