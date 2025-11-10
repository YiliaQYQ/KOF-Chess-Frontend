# main.py
import pygame
from settings import *
from board import board, defeat_board, random_init, draw_board, can_attack, check_winner, should_update_defeat
from ai import ai_move_one_step
from animations import animate_move, animate_athena_fusion, animate_defeat_update, animate_attack_failed

def main():
    random_init()
    clock = pygame.time.Clock()
    running = True
    selected = None
    game_over = False
    winner = None
    turn_count = 0
    turn_timer = TURN_TIME
    last_tick = pygame.time.get_ticks()
    
    # 无动作惩罚相关变量
    player_idle_count = 0  # 玩家连续无动作计数
    ai_idle_count = 0       # AI 连续无动作计数
    player_made_action = False  # 玩家本回合是否有动作
    ai_made_action = False      # AI 本回合是否有动作
    
    # AI 延迟相关变量
    waiting_for_ai = False      # 是否正在等待 AI 行动
    ai_wait_start_time = 0      # AI 等待开始时间
    AI_WAIT_DELAY = 2.0         # 玩家行动后等待 2 秒再让 AI 行动

    while running:
        draw_board(selected, turn_count, turn_timer, game_over, winner)

        if game_over:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
            clock.tick(FPS)
            continue

        # 时间流逝
        now = pygame.time.get_ticks()
        elapsed = (now - last_tick) / 1000
        last_tick = now
        
        # 检查是否在等待 AI 行动
        if waiting_for_ai:
            ai_elapsed = (now - ai_wait_start_time) / 1000
            if ai_elapsed >= AI_WAIT_DELAY:
                # 等待时间到，执行 AI 行动
                waiting_for_ai = False
                ai_made_action = ai_move_one_step(draw_board)
                if ai_made_action:
                    ai_idle_count = 0  # AI 有动作,重置计数
                else:
                    ai_idle_count += 1  # AI 无动作,计数+1
                    
                # 检查 AI 是否连续5回合无动作
                if ai_idle_count >= MAX_IDLE_TURNS:
                    game_over = True
                    winner = "Player (AI Idle)"
                    continue
                    
                turn_count += 1
                turn_timer = TURN_TIME
        
        # 玩家回合计时
        if selected and not waiting_for_ai:
            turn_timer -= elapsed
            if turn_timer <= 0:
                # 玩家超时,视为无动作
                selected = None
                player_made_action = False
                player_idle_count += 1
                
                # 检查玩家是否连续5回合无动作
                if player_idle_count >= MAX_IDLE_TURNS:
                    game_over = True
                    winner = "AI (Player Idle)"
                    continue
                
                # 开始等待 AI 行动
                waiting_for_ai = True
                ai_wait_start_time = pygame.time.get_ticks()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and not game_over:
                x, y = e.pos
                r, c = y // CELL_SIZE, x // CELL_SIZE
                if not (0 <= r < ROWS and 0 <= c < COLS):
                    continue
                clicked = board[r][c]
                if selected:
                    sr, sc = selected
                    s_chip = board[sr][sc]
                    if s_chip is None:
                        selected = None
                        continue
                    if abs(sr - r) + abs(sc - c) == 1:
                        target_chip = board[r][c]
                        
                        # 记录玩家执行了动作
                        action_executed = False
                        
                        if target_chip is None:
                            # 移动（defeat 信息跟随棋子）
                            animate_move(sr, sc, r, c, s_chip)
                            board[r][c], board[sr][sc] = s_chip, None
                            action_executed = True
                            
                        elif target_chip.is_player != s_chip.is_player:
                            # 攻击或融合
                            if s_chip.name == "athena" or target_chip.name == "athena":
                                # Athena 融合
                                animate_athena_fusion(sr, sc, r, c, draw_board)
                                board[sr][sc] = board[r][c] = None
                                action_executed = True
                            elif can_attack(s_chip, target_chip):
                                # 玩家攻击成功 - 不更新玩家棋子的 defeat（玩家不显示 defeat）
                                animate_move(sr, sc, r, c, s_chip)
                                board[r][c], board[sr][sc] = s_chip, None
                                action_executed = True
                            else:
                                # 玩家攻击失败 - 播放撞击消散动画
                                animate_attack_failed(sr, sc, r, c, s_chip, draw_board)
                                board[sr][sc] = None
                                defeat_updated = False
                                # 只有击败更高等级才更新 AI 棋子的 defeat 信息
                                if should_update_defeat(target_chip.defeat, s_chip.name):
                                    target_chip.defeat = s_chip.name
                                    defeat_updated = True
                                # 如果 defeat 更新了，显示更新动画
                                if defeat_updated:
                                    animate_defeat_update(r, c, draw_board)
                                action_executed = True
                        
                        if action_executed:
                            player_made_action = True
                            player_idle_count = 0  # 玩家有动作,重置计数
                        
                        selected = None
                        turn_timer = TURN_TIME
                        
                        # 开始等待 AI 行动（5秒延迟）
                        waiting_for_ai = True
                        ai_wait_start_time = pygame.time.get_ticks()
                        
                        # 检查常规胜负条件
                        if turn_count >= MAX_TURNS or \
                           not any(b and b.is_player for row in board for b in row) or \
                           not any(b and not b.is_player for row in board for b in row):
                            game_over = True
                            winner = check_winner()
                    else:
                        selected = (r, c) if clicked and clicked.is_player else None
                else:
                    if clicked and clicked.is_player:
                        selected = (r, c)
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()