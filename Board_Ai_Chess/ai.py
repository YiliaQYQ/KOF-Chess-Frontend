# ai.py
import random
from settings import ROWS, COLS
from board import board, defeat_board, can_attack
from animations import animate_move, animate_athena_fusion

def ai_move_one_step(draw_board):
    """
    AI 单步逻辑
    返回: True 表示 AI 执行了动作, False 表示 AI 无动作可执行
    """
    ai_positions = [(r, c) for r in range(ROWS) for c in range(COLS)
                    if board[r][c] and not board[r][c].is_player]
    random.shuffle(ai_positions)
    
    for sr, sc in ai_positions:
        chip = board[sr][sc]
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(directions)
        
        for dr, dc in directions:
            r, c = sr + dr, sc + dc
            if not (0 <= r < ROWS and 0 <= c < COLS):
                continue
            target = board[r][c]

            if target is None:
                # 移动到空格
                animate_move(sr, sc, r, c, chip)
                board[r][c], board[sr][sc] = chip, None
                return True  # 执行了移动动作
                
            elif target.is_player:
                # 攻击玩家棋子
                if chip.name == "athena" or target.name == "athena":
                    # Athena 融合
                    animate_athena_fusion(sr, sc, r, c, draw_board)
                    board[sr][sc] = board[r][c] = None
                    return True  # 执行了融合动作
                    
                elif can_attack(chip, target):
                    # 攻击成功
                    animate_move(sr, sc, r, c, chip)
                    board[r][c], board[sr][sc] = chip, None
                    # AI 攻击成功后，在 AI 棋子背面记录被击败的玩家棋子名称
                    defeat_board[r][c] = target.name
                    return True  # 执行了攻击动作
                    
                else:
                    # 攻击失败
                    board[sr][sc] = None
                    defeat_board[sr][sc] = chip.name
                    return True  # 执行了失败的攻击动作
    
    # 遍历完所有棋子和方向都没有可执行的动作
    return False