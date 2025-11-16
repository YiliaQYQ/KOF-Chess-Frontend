# settings.py (LAN版本)
import pygame

# -------- 基本设置 --------
pygame.init()

CELL_SIZE = 80
ROWS, COLS = 5, 6
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Board AI LAN Battle")

FONT = pygame.font.SysFont(None, 24)
FPS = 30

# -------- 棋子定义 --------
CHIP_NAMES = ["orichi", "yagami", "kula", "k", "mai", "kyo", "athena"]
CHIP_COLORS = {
    "orichi": (255, 0, 0),
    "yagami": (255, 165, 0),
    "kula": (0, 255, 0),
    "k": (0, 255, 255),
    "mai": (0, 0, 255),
    "kyo": (128, 0, 128),
    "athena": (255, 105, 180)
}

BACK_COLOR = (50, 50, 50)  # 背面颜色
MAX_TURNS = 60
TURN_TIME = 15

# -------- 无动作惩罚设置 --------
MAX_IDLE_TURNS = 5  # 连续无动作最大回合数

# -------- 网络设置 --------
DEFAULT_SERVER_HOST = "127.0.0.1"  # 默认服务器地址
DEFAULT_SERVER_PORT = 50007