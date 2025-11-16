# animations.py
import pygame
from settings import SCREEN, CELL_SIZE, CHIP_COLORS, FONT, HEIGHT, WIDTH

def animate_move(sr, sc, tr, tc, chip, steps=10):
    """
    平滑移动动画
    - 玩家棋子：显示棋子原色
    - AI 棋子：统一显示黄色（隐藏等级信息）
    """
    from board import board, draw_board
    
    start_x, start_y = sc * CELL_SIZE, sr * CELL_SIZE
    end_x, end_y = tc * CELL_SIZE, tr * CELL_SIZE
    
    # 临时移除起点的棋子，避免重复绘制
    temp_chip = board[sr][sc]
    board[sr][sc] = None
    
    for i in range(1, steps + 1):
        # 重绘整个棋盘
        draw_board()
        
        # 计算移动位置
        x = start_x + (end_x - start_x) * i / steps
        y = start_y + (end_y - start_y) * i / steps
        
        # AI 棋子统一用黄色，玩家棋子显示原色
        if chip.is_player:
            color = CHIP_COLORS.get(chip.name, (0, 0, 0))
        else:
            color = (255, 200, 0)  # AI 棋子统一黄色
        
        # 绘制移动中的棋子
        pygame.draw.rect(SCREEN, color, (x + 6, y + 6, CELL_SIZE - 12, CELL_SIZE - 12))
        pygame.display.flip()
        pygame.time.delay(25)
    
    # 恢复棋子到起点（调用方会处理最终位置）
    board[sr][sc] = temp_chip

def animate_attack_failed(sr, sc, tr, tc, attacker, draw_board):
    """
    攻击失败动画：
    1. 攻击方向目标冲刺
    2. 撞击闪光（红色）
    3. 攻击方消散（逐渐缩小透明）
    4. 防守方显示 defeat 更新
    
    注意：AI 棋子移动时统一显示黄色
    """
    from board import board
    
    start_x, start_y = sc * CELL_SIZE, sr * CELL_SIZE
    target_x, target_y = tc * CELL_SIZE, tr * CELL_SIZE
    
    # 确定移动颜色：AI 棋子用黄色，玩家棋子用原色
    if attacker.is_player:
        move_color = CHIP_COLORS.get(attacker.name, (0, 0, 0))
    else:
        move_color = (255, 200, 0)  # AI 棋子统一黄色
    
    # 临时移除起点的棋子
    temp_chip = board[sr][sc]
    board[sr][sc] = None
    
    # 第一阶段：冲刺动画（快速移动 80% 距离）
    steps = 8
    for i in range(1, steps + 1):
        draw_board()
        progress = i / steps * 0.8  # 只移动 80% 距离
        x = start_x + (target_x - start_x) * progress
        y = start_y + (target_y - start_y) * progress
        pygame.draw.rect(SCREEN, move_color, (x + 6, y + 6, CELL_SIZE - 12, CELL_SIZE - 12))
        pygame.display.flip()
        pygame.time.delay(30)
    
    # 第二阶段：撞击闪光（红白闪烁）
    for i in range(6):
        draw_board()
        color = (255, 0, 0) if i % 2 == 0 else (255, 255, 255)
        # 在目标格闪光
        pygame.draw.rect(SCREEN, color, (target_x, target_y, CELL_SIZE, CELL_SIZE), 5)
        # 攻击方在 80% 位置
        attack_x = start_x + (target_x - start_x) * 0.8
        attack_y = start_y + (target_y - start_y) * 0.8
        pygame.draw.rect(SCREEN, move_color, (attack_x + 6, attack_y + 6, CELL_SIZE - 12, CELL_SIZE - 12))
        pygame.draw.rect(SCREEN, color, (attack_x + 6, attack_y + 6, CELL_SIZE - 12, CELL_SIZE - 12), 3)
        pygame.display.flip()
        pygame.time.delay(100)
    
    # 第三阶段：消散动画（逐渐缩小）
    for i in range(8, 0, -1):
        draw_board()
        scale = i / 8  # 从 1.0 缩小到 0
        attack_x = start_x + (target_x - start_x) * 0.8
        attack_y = start_y + (target_y - start_y) * 0.8
        size = int((CELL_SIZE - 12) * scale)
        offset = (CELL_SIZE - 12 - size) // 2
        if size > 0:
            pygame.draw.rect(SCREEN, move_color, 
                           (attack_x + 6 + offset, attack_y + 6 + offset, size, size))
        pygame.display.flip()
        pygame.time.delay(50)
    
    # 不恢复棋子（因为攻击失败，棋子已消失）

def animate_athena_fusion(r1, c1, r2, c2, draw_board, flashes=6):
    """雅典娜融合 / 同归于尽特效"""
    for i in range(flashes):
        draw_board()
        color = (255, 255, 255) if i % 2 == 0 else (255, 255, 0)
        pygame.draw.rect(SCREEN, color, (c1 * CELL_SIZE, r1 * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(SCREEN, color, (c2 * CELL_SIZE, r2 * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.display.flip()
        pygame.time.delay(100)

def animate_ai_select(r, c, draw_board, flashes=6):
    """AI 选中棋子的闪光动画（3秒，闪烁6次）"""
    for i in range(flashes):
        draw_board()
        # 黄色和白色交替闪烁
        color = (255, 255, 0) if i % 2 == 0 else (255, 255, 255)
        pygame.draw.rect(SCREEN, color, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE), 5)
        pygame.display.flip()
        pygame.time.delay(500)  # 每次闪烁持续 500ms，共 3 秒

def animate_defeat_update(r, c, draw_board, flashes=4):
    """defeat 信息更新闪光提示（2秒，闪烁4次）"""
    for i in range(flashes):
        draw_board()
        # 红色和黄色交替闪烁，提示 defeat 信息更新
        color = (255, 0, 0) if i % 2 == 0 else (255, 255, 0)
        pygame.draw.rect(SCREEN, color, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE), 5)
        pygame.display.flip()
        pygame.time.delay(500)  # 每次闪烁持续 500ms，共 2 秒