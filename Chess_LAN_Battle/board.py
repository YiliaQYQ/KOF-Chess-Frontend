# board.py (LAN版本)
import random
import pygame
from settings import *
from chip import Chip
from animations import animate_move, animate_athena_fusion

board = [[None for _ in range(COLS)] for _ in range(ROWS)]
defeat_board = [[None for _ in range(COLS)] for _ in range(ROWS)]

# 棋子等级排序（从高到低）
CHIP_HIERARCHY = ["orichi", "yagami", "kula", "k", "mai", "kyo"]

def get_chip_level(chip_name):
    """获取棋子等级（数字越大等级越高）"""
    if chip_name == "athena":
        return -1  # Athena 不参与等级比较
    if chip_name in CHIP_HIERARCHY:
        return len(CHIP_HIERARCHY) - CHIP_HIERARCHY.index(chip_name)
    return 0

def should_update_defeat(current_defeat, new_defeat):
    """判断是否应该更新 defeat 信息（只有击败更高等级才更新）"""
    if current_defeat is None:
        return True
    if new_defeat == "athena":
        return False
    if current_defeat == "athena":
        return True
    
    current_level = get_chip_level(current_defeat)
    new_level = get_chip_level(new_defeat)
    return new_level > current_level

def random_init(seed=None):
    """初始化棋盘（使用种子确保双方一致）"""
    if seed is not None:
        random.seed(seed)
    
    global board, defeat_board
    board = [[None for _ in range(COLS)] for _ in range(ROWS)]
    defeat_board = [[None for _ in range(COLS)] for _ in range(ROWS)]
    
    player_list = ["orichi"]*1 + ["yagami"]*2 + ["kula"]*2 + ["k"]*2 + ["mai"]*2 + ["kyo"]*4 + ["athena"]*2
    enemy_list  = ["orichi"]*1 + ["yagami"]*2 + ["kula"]*2 + ["k"]*2 + ["mai"]*2 + ["kyo"]*4 + ["athena"]*2
    positions = [(r,c) for r in range(ROWS) for c in range(COLS)]
    random.shuffle(positions)
    
    for i, name in enumerate(player_list):
        r, c = positions[i]
        board[r][c] = Chip(name, True)
    for i, name in enumerate(enemy_list):
        r, c = positions[i+len(player_list)]
        board[r][c] = Chip(name, False)

def draw_board(selected=None, turn_count=0, turn_timer=0, game_over=False, winner=None, 
               waiting_for_peer=False, my_side=None, current_turn=None):
    """
    绘制棋盘（LAN版本）
    waiting_for_peer: 是否在等待对方行动
    my_side: 我的身份 'A' 或 'B'
    current_turn: 当前回合 'A' 或 'B'
    """
    SCREEN.fill((150,150,150))
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(SCREEN, (120,120,120), rect)
            pygame.draw.rect(SCREEN, (0,0,0), rect, 1)
            chip = board[r][c]

            if chip:
                if chip.is_player:
                    # 玩家棋子 - 显示正面
                    pygame.draw.circle(SCREEN, (255,255,255), rect.center, CELL_SIZE//2-6)
                    color = CHIP_COLORS.get(chip.name, (0,0,0))
                    text = FONT.render(chip.name, True, color)
                    SCREEN.blit(text, text.get_rect(center=rect.center))
                    if selected == (r, c):
                        pygame.draw.rect(SCREEN, (255,255,0), rect, 3)
                else:
                    # 对方棋子 - 显示背面
                    pygame.draw.circle(SCREEN, (0,0,0), rect.center, CELL_SIZE//2-6)
                    if chip.defeat:
                        defeat_text = FONT.render("defeat", True, (255,255,255))
                        name_text = FONT.render(chip.defeat, True, (255,255,255))
                        SCREEN.blit(defeat_text, (c*CELL_SIZE+5, r*CELL_SIZE+10))
                        SCREEN.blit(name_text, (c*CELL_SIZE+5, r*CELL_SIZE+30))

    # 显示回合信息
    turn_text = FONT.render(f"Turn: {turn_count}/{MAX_TURNS}", True, (0,0,0))
    SCREEN.blit(turn_text, (10, HEIGHT-30))
    
    # 显示计时器
    if not game_over and selected and not waiting_for_peer:
        timer_text = FONT.render(f"Time Left: {int(turn_timer)}s", True, (0,0,0))
        SCREEN.blit(timer_text, (WIDTH-140, HEIGHT-30))
    
    # 显示当前状态
    if waiting_for_peer:
        status_text = FONT.render("Waiting for opponent...", True, (255, 100, 0))
        SCREEN.blit(status_text, (WIDTH//2-100, HEIGHT-60))
    elif not game_over and my_side and current_turn:
        if my_side == current_turn:
            status_text = FONT.render("Your Turn", True, (0, 255, 0))
        else:
            status_text = FONT.render("Opponent's Turn", True, (255, 0, 0))
        SCREEN.blit(status_text, (WIDTH//2-60, HEIGHT-60))
    
    # 显示游戏结束信息
    if game_over:
        over_text = FONT.render(f"Game Over! Winner: {winner}", True, (255,0,0))
        SCREEN.blit(over_text, (WIDTH//2-100, HEIGHT-30))
    
    pygame.display.flip()

def can_attack(attacker, defender):
    """判断能否击败"""
    hierarchy = ["kyo", "mai", "k", "kula", "yagami", "orichi"]
    if attacker.name == "athena" or defender.name == "athena":
        return False
    if attacker.name == "kyo" and defender.name == "orichi":
        return True
    if attacker.name == "orichi" and defender.name == "kyo":
        return False
    if attacker.name == defender.name:
        return True
    return hierarchy.index(attacker.name) > hierarchy.index(defender.name)

def check_winner():
    """判定胜负"""
    order = ["orichi","yagami","kula","k","mai","kyo"]
    player_counts = {n:0 for n in order}
    ai_counts = {n:0 for n in order}
    for r in range(ROWS):
        for c in range(COLS):
            chip = board[r][c]
            if chip and chip.name != "athena":
                (player_counts if chip.is_player else ai_counts)[chip.name] += 1
    for n in order:
        if player_counts[n] > ai_counts[n]: return "Player"
        elif player_counts[n] < ai_counts[n]: return "Opponent"
    return "Draw"

def get_board_state():
    """获取当前棋盘状态（用于同步验证）"""
    state = []
    for r in range(ROWS):
        for c in range(COLS):
            chip = board[r][c]
            if chip:
                state.append({
                    "pos": [r, c],
                    "name": chip.name,
                    "is_player": chip.is_player,
                    "defeat": chip.defeat
                })
    return state