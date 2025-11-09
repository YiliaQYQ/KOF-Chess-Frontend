# board.py
import random
import pygame
from settings import *
from chip import Chip
from animations import animate_move, animate_athena_fusion

board = [[None for _ in range(COLS)] for _ in range(ROWS)]
defeat_board = [[None for _ in range(COLS)] for _ in range(ROWS)]

def random_init():
    """初始化棋盘"""
    player_list = ["orichi"]*1 + ["yagami"]*2 + ["kula"]*2 + ["k"]*2 + ["mai"]*2 + ["kyo"]*4 + ["athena"]*2
    enemy_list  = ["orichi"]*1 + ["yagami"]*2 + ["kula"]*2 + ["k"]*2 + ["mai"]*2 + ["kyo"]*4 + ["athena"]*2
    positions = [(r,c) for r in range(ROWS) for c in range(COLS)]
    random.shuffle(positions)
    for i, name in enumerate(player_list):
        r,c = positions[i]
        board[r][c] = Chip(name, True)
    for i, name in enumerate(enemy_list):
        r,c = positions[i+len(player_list)]
        board[r][c] = Chip(name, False)

def draw_board(selected=None, turn_count=0, turn_timer=0, game_over=False, winner=None):
    """绘制棋盘"""
    SCREEN.fill((150,150,150))
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(SCREEN, (120,120,120), rect)
            pygame.draw.rect(SCREEN, (0,0,0), rect, 1)
            chip = board[r][c]

            if chip:
                if chip.is_player:
                    # 玩家棋子 - 显示正面(白色圆 + 棋子名称)
                    pygame.draw.circle(SCREEN, (255,255,255), rect.center, CELL_SIZE//2-6)
                    color = CHIP_COLORS.get(chip.name, (0,0,0))
                    text = FONT.render(chip.name, True, color)
                    SCREEN.blit(text, text.get_rect(center=rect.center))
                    if selected == (r, c):
                        pygame.draw.rect(SCREEN, (255,255,0), rect, 3)
                else:
                    # AI 棋子 - 显示背面(黑色圆 + defeat 信息)
                    pygame.draw.circle(SCREEN, (0,0,0), rect.center, CELL_SIZE//2-6)
                    
                    # 统一从 defeat_board 读取 defeat 信息
                    defeat_name = defeat_board[r][c]
                    if defeat_name:
                        # 显示双行: "defeat" + 被击败棋子名
                        defeat_text = FONT.render("defeat", True, (255,255,255))
                        name_text = FONT.render(defeat_name, True, (255,255,255))
                        SCREEN.blit(defeat_text, (c*CELL_SIZE+5, r*CELL_SIZE+10))
                        SCREEN.blit(name_text, (c*CELL_SIZE+5, r*CELL_SIZE+30))
            # else: 空格不显示任何内容（包括 defeat 信息）
            # 空格保持空白，defeat_board 数据仅在有棋子时显示

    # 显示回合信息
    turn_text = FONT.render(f"Turn: {turn_count}/{MAX_TURNS}", True, (0,0,0))
    SCREEN.blit(turn_text, (10, HEIGHT-30))
    
    # 显示计时器
    if not game_over and selected:
        timer_text = FONT.render(f"Time Left: {int(turn_timer)}s", True, (0,0,0))
        SCREEN.blit(timer_text, (WIDTH-140, HEIGHT-30))
    
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
        elif player_counts[n] < ai_counts[n]: return "AI"
    return "Draw"