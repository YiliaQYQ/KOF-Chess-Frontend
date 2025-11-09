import pygame
import random

# -------- 基本设置 --------
pygame.init()
CELL_SIZE = 80
ROWS, COLS = 5, 6
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Board AI LocalBattle")

FONT = pygame.font.SysFont(None, 24)
FPS = 30

# -------- 棋子定义 --------
CHIP_NAMES = ["orichi","yagami","kula","k","mai","kyo","athena"]
CHIP_COLORS = {
    "orichi": (255,0,0),
    "yagami": (255,165,0),
    "kula": (0,255,0),
    "k": (0,255,255),
    "mai": (0,0,255),
    "kyo": (128,0,128),
    "athena": (255,105,180)  # 粉色
}
BACK_COLOR = (50,50,50)  # 背面颜色（敌方/空位显示背面）

# -------- 棋子类 --------
class Chip:
    def __init__(self, name, is_player=True):
        self.name = name
        self.is_player = is_player
        # 当此棋子曾经“击败过”某个等级时，记录在这里（用于正面显示自身击败记录）
        # 对于被吃掉后仍要显示的背面信息，使用 defeat_board（见下）
        self.defeat = None

    def __repr__(self):
        return f"{'P' if self.is_player else 'A'}:{self.name}"

# 棋盘与 defeat_board（即使棋子被移除也显示）
board = [[None for _ in range(COLS)] for _ in range(ROWS)]
defeat_board = [[None for _ in range(COLS)] for _ in range(ROWS)]

# -------- 初始化棋盘，随机布局 --------
def random_init():
    # 每方棋子数量：orichi1, yagami2, kula2, k2, mai2, kyo4, athena2
    player_chips_list = ["orichi"]*1 + ["yagami"]*2 + ["kula"]*2 + ["k"]*2 + ["mai"]*2 + ["kyo"]*4 + ["athena"]*2
    enemy_chips_list  = ["orichi"]*1 + ["yagami"]*2 + ["kula"]*2 + ["k"]*2 + ["mai"]*2 + ["kyo"]*4 + ["athena"]*2

    positions = [(r,c) for r in range(ROWS) for c in range(COLS)]
    random.shuffle(positions)

    # 放玩家棋子
    for i, name in enumerate(player_chips_list):
        r,c = positions[i]
        board[r][c] = Chip(name, True)

    # 放AI棋子
    for i, name in enumerate(enemy_chips_list):
        r,c = positions[i+len(player_chips_list)]
        board[r][c] = Chip(name, False)

random_init()

# -------- 绘制棋盘（灰色底色，白/黑棋子） --------
def draw_board(selected=None):
    SCREEN.fill((150,150,150))  # 整体灰色背景

    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(SCREEN, (120,120,120), rect)  # 棋格浅灰
            pygame.draw.rect(SCREEN, (0,0,0), rect, 1)      # 棋格边框

            chip = board[r][c]

            if chip:
                # 我方棋子
                if chip.is_player:
                    # 白色棋子
                    pygame.draw.circle(SCREEN, (255,255,255), rect.center, CELL_SIZE//2-6)
                    # 彩色等级文字
                    text_color = CHIP_COLORS.get(chip.name, (0,0,0))
                    text = FONT.render(chip.name, True, text_color)
                    text_rect = text.get_rect(center=rect.center)
                    SCREEN.blit(text, text_rect)

                    # 选中高亮
                    if selected == (r, c):
                        pygame.draw.rect(SCREEN, (255,255,0), rect, 3)

                    # -------- 注释掉敌方视角我方棋子背面显示 defeat，避免残影 --------
                    # defeat_text = chip.defeat or defeat_board[r][c]
                    # if defeat_text:
                    #     text1 = FONT.render("defeat", True, (255,255,255))
                    #     text2 = FONT.render(defeat_text, True, (255,255,255))
                    #     SCREEN.blit(text1, (c*CELL_SIZE+5, r*CELL_SIZE+10))
                    #     SCREEN.blit(text2, (c*CELL_SIZE+5, r*CELL_SIZE+30))

                # 对方棋子
                else:
                    pygame.draw.circle(SCREEN, (0,0,0), rect.center, CELL_SIZE//2-6)
                    # 玩家视角看到敌方背面显示 defeat
                    defeat_text = chip.defeat or defeat_board[r][c]
                    if defeat_text:
                        text1 = FONT.render("defeat", True, (255,255,255))
                        text2 = FONT.render(defeat_text, True, (255,255,255))
                        SCREEN.blit(text1, (c*CELL_SIZE+5, r*CELL_SIZE+10))
                        SCREEN.blit(text2, (c*CELL_SIZE+5, r*CELL_SIZE+30))

            # 空格，如果 defeat_board 有记录，则显示背面
            else:
                if defeat_board[r][c]:
                    pygame.draw.circle(SCREEN, BACK_COLOR, rect.center, CELL_SIZE//2-6)
                    text1 = FONT.render("defeat", True, (255,255,255))
                    text2 = FONT.render(defeat_board[r][c], True, (255,255,255))
                    SCREEN.blit(text1, (c*CELL_SIZE+5, r*CELL_SIZE+10))
                    SCREEN.blit(text2, (c*CELL_SIZE+5, r*CELL_SIZE+30))

    # 回合数与计时器
    turn_text = FONT.render(f"Turn: {turn_count}/{MAX_TURNS}", True, (0,0,0))
    SCREEN.blit(turn_text, (10, HEIGHT-30))
    if not game_over and selected:
        timer_text = FONT.render(f"Time Left: {int(turn_timer)}s", True, (0,0,0))
        SCREEN.blit(timer_text, (WIDTH-140, HEIGHT-30))
    if game_over:
        over_text = FONT.render(f"Game Over! Winner: {winner}", True, (255,0,0))
        SCREEN.blit(over_text, (WIDTH//2-100, HEIGHT-30))

    pygame.display.flip()

# ---------- 攻击判定 ----------
def can_attack(attacker, defender):
    """返回True表示攻击者胜利"""
    hierarchy = ["kyo", "mai", "k", "kula", "yagami", "orichi"]

    # Athena 特殊融合
    if attacker.name == "athena" or defender.name == "athena":
        return False  # 外层单独处理

    # 特例：kyo vs orichi
    if attacker.name == "kyo" and defender.name == "orichi":
        return True
    if attacker.name == "orichi" and defender.name == "kyo":
        return False

    # 同级对决 → 攻击方胜
    if attacker.name == defender.name:
        return True

    # 按层级比较
    return hierarchy.index(attacker.name) > hierarchy.index(defender.name)

# -------- 动画：平滑移动（插值） --------
def animate_move(sr, sc, tr, tc, chip, steps=10):
    start_x, start_y = sc*CELL_SIZE, sr*CELL_SIZE
    end_x, end_y = tc*CELL_SIZE, tr*CELL_SIZE
    for i in range(1, steps+1):
        draw_board()
        x = start_x + (end_x - start_x) * i / steps
        y = start_y + (end_y - start_y) * i / steps
        color = CHIP_COLORS.get(chip.name, (0,0,0))
        pygame.draw.rect(SCREEN, color, (x+6, y+6, CELL_SIZE-12, CELL_SIZE-12))
        pygame.display.flip()
        pygame.time.delay(25)

# -------- 特殊动画：Athena 融合 / 同归于尽闪光 --------
def animate_athena_fusion(r1, c1, r2, c2, flashes=6):
    """
    两个格子交替闪烁白色/黄色，形成融合或同归于尽效果
    """
    for i in range(flashes):
        draw_board()
        color = (255, 255, 255) if i % 2 == 0 else (255, 255, 0)
        pygame.draw.rect(SCREEN, color, (c1*CELL_SIZE, r1*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(SCREEN, color, (c2*CELL_SIZE, r2*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.display.flip()
        pygame.time.delay(100)

# -------- 胜负判定（积分制，雅典娜不计分） --------
def check_winner():
    order = ["orichi","yagami","kula","k","mai","kyo"]
    player_counts = {name:0 for name in order}
    ai_counts = {name:0 for name in order}

    for r in range(ROWS):
        for c in range(COLS):
            chip = board[r][c]
            if chip and chip.name != "athena":
                if chip.is_player:
                    player_counts[chip.name] += 1
                else:
                    ai_counts[chip.name] += 1

    for name in order:
        if player_counts[name] > ai_counts[name]:
            return "Player"
        elif player_counts[name] < ai_counts[name]:
            return "AI"
    return "Draw"

# -------- 游戏主循环 + 玩家操作 + AI逻辑 --------
MAX_TURNS = 60
TURN_TIME = 15
turn_count = 0
turn_timer = TURN_TIME
last_tick = pygame.time.get_ticks()
game_over = False
winner = None
selected = None
running = True
clock = pygame.time.Clock()

# ---------- AI 行动逻辑 ----------
def ai_move_one_step():
    global defeat_board

    ai_positions = [(r, c) for r in range(ROWS) for c in range(COLS)
                    if board[r][c] and not board[r][c].is_player]

    random.shuffle(ai_positions)

    for sr, sc in ai_positions:
        chip = board[sr][sc]
        if not chip:
            continue

        # 获取相邻格
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(directions)

        for dr, dc in directions:
            r, c = sr + dr, sc + dc
            if not (0 <= r < ROWS and 0 <= c < COLS):
                continue

            target = board[r][c]

            # --- 空格：普通移动 ---
            if target is None:
                animate_move(sr, sc, r, c, chip)
                board[r][c] = chip
                board[sr][sc] = None
                print(f"[AI MOVE] {chip.name} moved to ({r},{c})")
                return

            # --- 敌方棋子：战斗或融合 ---
            elif target.is_player:
                if chip.name == "athena" or target.name == "athena":
                    print(f"[AI ATHENA FUSION] between {chip.name} and {target.name}")
                    animate_athena_fusion(sr, sc, r, c)
                    board[sr][sc] = None
                    board[r][c] = None
                    return

                elif can_attack(chip, target):
                    print(f"[AI ATTACK SUCCESS] {chip.name} defeated {target.name}")
                    animate_move(sr, sc, r, c, chip)
                    defeat_board[r][c] = target.name
                    board[r][c] = chip
                    board[sr][sc] = None
                    return

                else:
                    print(f"[AI ATTACK FAIL] {chip.name} lost to {target.name}")
                    defeat_board[sr][sc] = None  # 清空原位
                    board[sr][sc] = None  # 攻击失败则AI棋子消失
                    return

    print("[AI TURN] No valid move found.")

# -------- 主循环 --------
while running:
    draw_board(selected)

    if game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        clock.tick(FPS)
        continue

    # ---------- 玩家回合计时 ----------
    now = pygame.time.get_ticks()
    elapsed = (now - last_tick) / 1000
    last_tick = now
    if selected:
        turn_timer -= elapsed
        if turn_timer <= 0:
            selected = None
            draw_board()
            pygame.time.wait(500)
            ai_move_one_step()
            turn_count += 1
            turn_timer = TURN_TIME

    # ---------- 玩家鼠标操作 ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            x, y = event.pos
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

                # ---------- 相邻格移动或攻击 ----------
                if abs(sr - r) + abs(sc - c) == 1:
                    target_chip = board[r][c]

                    # ---------- 空格：普通移动 ----------
                    if target_chip is None:
                        animate_move(sr, sc, r, c, s_chip)
                        board[r][c] = s_chip
                        board[sr][sc] = None
                        print(f"[PLAYER MOVE] {s_chip.name} moved to ({r},{c})")

                    # ---------- 敌方棋子：战斗或融合 ----------
                    else:
                        if target_chip.is_player == s_chip.is_player:
                            pass  # 同阵营无效点击
                        else:
                            # --- 雅典娜融合 ---
                            if s_chip.name == "athena" or target_chip.name == "athena":
                                print(f"[ATHENA FUSION] between {s_chip.name} and {target_chip.name}")
                                animate_athena_fusion(sr, sc, r, c)
                                board[sr][sc] = None
                                board[r][c] = None

                            # --- 攻击成功 ---
                            elif can_attack(s_chip, target_chip):
                                print(f"[ATTACK SUCCESS] {s_chip.name} defeated {target_chip.name}")
                                animate_move(sr, sc, r, c, s_chip)
                                board[r][c] = s_chip
                                board[sr][sc] = None
                                # 对方背面记录 defeat 信息（我方视角可见）
                                defeat_board[r][c] = target_chip.name

                            # --- 攻击失败 ---
                            else:
                                print(f"[ATTACK FAIL] {s_chip.name} lost to {target_chip.name}")
                                animate_move(sr, sc, sr, sc, s_chip)
                                defeat_board[sr][sc] = s_chip.name
                                target_chip.defeat = s_chip.name
                                board[sr][sc] = None  # 清空原位

                    # ---------- 玩家回合结束 ----------
                    selected = None
                    turn_timer = TURN_TIME
                    draw_board()
                    pygame.time.wait(400)

                    # ---------- AI 行动一步 ----------
                    ai_move_one_step()
                    turn_count += 1
                    turn_timer = TURN_TIME

                    # ---------- 胜负检查 ----------
                    player_chips_exist = any(board[r][c] and board[r][c].is_player for r in range(ROWS) for c in range(COLS))
                    ai_chips_exist = any(board[r][c] and not board[r][c].is_player for r in range(ROWS) for c in range(COLS))
                    if turn_count >= MAX_TURNS or not player_chips_exist or not ai_chips_exist:
                        game_over = True
                        winner = check_winner()

                else:
                    # 点击非相邻格 → 取消选择或切换
                    if clicked and clicked.is_player:
                        selected = (r, c)
                    else:
                        selected = None
            else:
                if clicked and clicked.is_player:
                    selected = (r, c)

        clock.tick(FPS)


pygame.quit()
