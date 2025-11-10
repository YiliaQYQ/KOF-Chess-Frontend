# ai.py
import random
from settings import ROWS, COLS
from board import board, defeat_board, can_attack, should_update_defeat
from animations import animate_move, animate_athena_fusion, animate_ai_select, animate_defeat_update, animate_attack_failed

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
                # AI 选中棋子闪光 3 秒
                animate_ai_select(sr, sc, draw_board)
                # 移动到空格（defeat 信息跟随棋子）
                animate_move(sr, sc, r, c, chip)
                board[r][c], board[sr][sc] = chip, None
                return True  # 执行了移动动作
                
            elif target.is_player:
                # AI 选中棋子闪光 3 秒
                animate_ai_select(sr, sc, draw_board)
                
                # 攻击玩家棋子
                if chip.name == "athena" or target.name == "athena":
                    # Athena 融合
                    animate_athena_fusion(sr, sc, r, c, draw_board)
                    board[sr][sc] = board[r][c] = None
                    return True  # 执行了融合动作
                    
                elif can_attack(chip, target):
                    # 攻击成功 - 先更新 defeat 信息，再播放动画
                    defeat_updated = False
                    if should_update_defeat(chip.defeat, target.name):
                        chip.defeat = target.name
                        defeat_updated = True
                    animate_move(sr, sc, r, c, chip)
                    board[r][c], board[sr][sc] = chip, None
                    # 如果 defeat 更新了，显示更新动画
                    if defeat_updated:
                        animate_defeat_update(r, c, draw_board)
                    return True  # 执行了攻击动作
                    
                else:
                    # 攻击失败 - 播放撞击消散动画
                    animate_attack_failed(sr, sc, r, c, chip, draw_board)
                    # AI 棋子消失（动画中已处理）
                    board[sr][sc] = None
                    return True  # 执行了失败的攻击动作
    
    # 遍历完所有棋子和方向都没有可执行的动作
    return False