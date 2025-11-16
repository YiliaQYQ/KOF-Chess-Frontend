# ai.py (智能版本 - 信息受限)
import random
from settings import ROWS, COLS
from board import board, defeat_board, can_attack, should_update_defeat, get_chip_level
from animations import animate_move, animate_athena_fusion, animate_ai_select, animate_defeat_update, animate_attack_failed

# 棋子价值评估（用于决策）
CHIP_VALUES = {
    "orichi": 100,
    "yagami": 80,
    "kula": 60,
    "k": 40,
    "mai": 20,
    "kyo": 10,
    "athena": 50  # 特殊价值
}

# AI 的记忆系统：记录观察到的玩家棋子信息
ai_memory = {}  # {(r,c): {"known_level": int, "confidence": float, "observations": []}}

def estimate_player_chip_value(r, c):
    """
    估算玩家棋子的价值（AI 只能通过有限信息推断）
    
    AI 可以知道：
    1. 该位置是否有玩家棋子（能看到白色圆圈）
    2. 如果 AI 曾攻击失败，能看到自己棋子的 defeat 信息
    3. 历史观察记录
    
    AI 不能知道：
    - 玩家棋子的具体名称
    - 玩家棋子的准确等级
    """
    player_chip = board[r][c]
    if not player_chip or not player_chip.is_player:
        return 0
    
    # 检查 AI 的记忆中是否有这个位置的信息
    if (r, c) in ai_memory:
        memory = ai_memory[(r, c)]
        # 根据已知等级估算价值
        known_level = memory.get("known_level", 3)  # 默认假设中等级
        confidence = memory.get("confidence", 0.3)
        # 价值 = 等级 × 10，但带有不确定性
        estimated_value = known_level * 10 * confidence + 30 * (1 - confidence)
        return estimated_value
    
    # 如果没有信息，返回默认中等价值（保守估计）
    return 30

def update_ai_memory_from_defeat(ai_chip_pos, player_chip_pos, ai_chip_name):
    """
    当 AI 攻击失败后，更新对玩家棋子的认知
    AI 知道：玩家的这个棋子击败了我的 XXX，所以它至少是 XXX 等级或更高
    """
    if player_chip_pos not in ai_memory:
        ai_memory[player_chip_pos] = {
            "known_level": 0,
            "confidence": 0.0,
            "observations": []
        }
    
    # AI 被击败，说明玩家棋子至少和 AI 同级或更高
    ai_level = get_chip_level(ai_chip_name)
    memory = ai_memory[player_chip_pos]
    
    # 更新已知等级（至少是击败我的等级）
    if ai_level > memory["known_level"]:
        memory["known_level"] = ai_level
        memory["confidence"] = 0.7  # 比较确定
    
    memory["observations"].append(f"defeated_{ai_chip_name}")

def update_ai_memory_from_observation(player_pos, ai_pos, result):
    """
    从战斗观察更新记忆
    result: 'ai_win', 'ai_lose', 'unknown'
    """
    if result == "ai_lose":
        # AI 输了，说明玩家棋子比较强
        if player_pos not in ai_memory:
            ai_memory[player_pos] = {"known_level": 4, "confidence": 0.5, "observations": []}
        else:
            ai_memory[player_pos]["known_level"] = max(ai_memory[player_pos]["known_level"], 4)

def get_all_possible_actions(is_ai=True):
    """
    获取所有可能的行动及其评分
    返回: [(score, sr, sc, tr, tc, action_type), ...]
    action_type: 'attack', 'move', 'fusion', 'probe'
    """
    actions = []
    positions = [(r, c) for r in range(ROWS) for c in range(COLS)
                 if board[r][c] and (not board[r][c].is_player if is_ai else board[r][c].is_player)]
    
    for sr, sc in positions:
        chip = board[sr][sc]
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        
        for dr, dc in directions:
            r, c = sr + dr, sc + dc
            if not (0 <= r < ROWS and 0 <= c < COLS):
                continue
            
            target = board[r][c]
            
            if target is None:
                # 移动到空格 - 评估位置价值
                score = evaluate_move(chip, sr, sc, r, c)
                actions.append((score, sr, sc, r, c, 'move'))
                
            elif target.is_player != chip.is_player:
                # 面对玩家棋子
                if chip.name == "athena" or target.name == "athena":
                    # Athena 融合（AI 能看到 Athena 的粉色圆圈？不，也看不到）
                    # AI 只能尝试融合，不知道对方是不是 Athena
                    score = evaluate_fusion(chip, target, r, c)
                    actions.append((score, sr, sc, r, c, 'fusion_attempt'))
                elif can_attack(chip, target):
                    # AI 不知道能否攻击成功，只能评估风险
                    score = evaluate_attack_attempt(chip, target, r, c)
                    actions.append((score, sr, sc, r, c, 'attack_attempt'))
                else:
                    # AI 不知道会失败，但可以评估风险
                    score = evaluate_attack_attempt(chip, target, r, c)
                    actions.append((score, sr, sc, r, c, 'attack_attempt'))
    
    return actions

def evaluate_attack_attempt(attacker, defender_chip, defender_r, defender_c):
    """
    评估攻击尝试（AI 不知道结果，只能评估风险）
    """
    score = 0
    
    # 估算对手价值（基于 AI 的记忆/观察）
    estimated_defender_value = estimate_player_chip_value(defender_r, defender_c)
    
    # 自己的价值
    attacker_value = CHIP_VALUES.get(attacker.name, 10)
    
    # 风险评估
    attacker_level = get_chip_level(attacker.name)
    
    # 如果对手价值未知，保守估计
    if (defender_r, defender_c) not in ai_memory:
        # 未知对手，中等风险
        risk_factor = 0.5
    else:
        memory = ai_memory[(defender_r, defender_c)]
        known_level = memory.get("known_level", 3)
        confidence = memory.get("confidence", 0.3)
        
        # 如果已知对手等级高，风险大
        if known_level > attacker_level:
            risk_factor = 0.2  # 高风险，很可能失败
        elif known_level < attacker_level:
            risk_factor = 0.9  # 低风险，可能成功
        else:
            risk_factor = 0.5  # 中等风险
    
    # 期望价值 = 预期收益 - 预期损失
    expected_gain = estimated_defender_value * risk_factor  # 成功的收益
    expected_loss = attacker_value * (1 - risk_factor)      # 失败的损失
    
    score = expected_gain - expected_loss
    
    # 如果是低价值棋子，可以冒险试探
    if attacker_value <= 20:  # kyo, mai
        score += 20  # 鼓励用低价值棋子试探
    
    # 中心位置加成
    if is_center_position(defender_r, defender_c):
        score += 10
    
    return score

def evaluate_fusion(attacker, defender_chip, defender_r, defender_c):
    """评估融合尝试（AI 不确定对方是否是 Athena）"""
    # Athena 融合风险评估
    attacker_value = CHIP_VALUES.get(attacker.name, 50)
    estimated_defender_value = estimate_player_chip_value(defender_r, defender_c)
    
    # 如果估算对方价值很高，融合可能划算
    if estimated_defender_value > attacker_value * 1.5:
        return 40
    else:
        return -20  # 不确定，保守

def evaluate_move(chip, sr, sc, tr, tc):
    """评估移动到空格的价值"""
    score = 0
    
    # 1. 目标位置价值
    if is_center_position(tr, tc):
        score += 20  # 中心位置价值高
    
    # 2. 靠近已知弱点（AI 记忆中的低等级玩家棋子）
    for (pr, pc), memory in ai_memory.items():
        if board[pr][pc] and board[pr][pc].is_player:
            known_level = memory.get("known_level", 3)
            confidence = memory.get("confidence", 0.3)
            if known_level < get_chip_level(chip.name):
                # 靠近我能打败的对手
                distance = abs(tr - pr) + abs(tc - pc)
                score += max(0, (10 - distance * 2)) * confidence
    
    # 3. 远离已知强敌
    threat_level = get_threat_level(chip, tr, tc)
    score -= threat_level * 10
    
    # 4. 控制重要区域
    if is_strategic_position(tr, tc):
        score += 15
    
    # 5. 靠近未知的玩家棋子（试探）
    nearest_unknown = get_nearest_unknown_player(tr, tc)
    if nearest_unknown and nearest_unknown <= 2:
        # 用低价值棋子靠近未知目标试探
        if CHIP_VALUES.get(chip.name, 50) <= 30:
            score += 15
    
    return score

def get_nearest_unknown_player(r, c):
    """获取到最近未知玩家棋子的距离"""
    min_distance = 999
    for tr in range(ROWS):
        for tc in range(COLS):
            target = board[tr][tc]
            if target and target.is_player:
                if (tr, tc) not in ai_memory or ai_memory[(tr, tc)]["confidence"] < 0.5:
                    distance = abs(r - tr) + abs(c - tc)
                    min_distance = min(min_distance, distance)
    return min_distance if min_distance < 999 else None

def get_position_from_board(chip):
    """获取棋子在棋盘上的位置"""
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == chip:
                return r, c
    return None, None

def is_center_position(r, c):
    """判断是否是中心区域"""
    center_r, center_c = ROWS // 2, COLS // 2
    return abs(r - center_r) <= 1 and abs(c - center_c) <= 1

def is_strategic_position(r, c):
    """判断是否是战略位置（边界、角落）"""
    if r == 0 or r == ROWS - 1 or c == 0 or c == COLS - 1:
        return True
    return False

def get_threat_level(chip, r, c):
    """评估位置的威胁等级（基于 AI 记忆）"""
    threat = 0
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            enemy = board[nr][nc]
            if enemy and enemy.is_player:
                # 检查 AI 记忆中对这个敌人的了解
                if (nr, nc) in ai_memory:
                    memory = ai_memory[(nr, nc)]
                    known_level = memory.get("known_level", 3)
                    confidence = memory.get("confidence", 0.3)
                    my_level = get_chip_level(chip.name)
                    
                    if known_level >= my_level:
                        threat += confidence * 5  # 确定的威胁
                else:
                    threat += 2  # 未知敌人，中等威胁
    
    return threat

def ai_move_one_step(draw_board):
    """
    AI 智能单步逻辑（信息受限版本）
    返回: True 表示 AI 执行了动作, False 表示 AI 无动作可执行
    """
    # 获取所有可能的行动并评分
    actions = get_all_possible_actions(is_ai=True)
    
    if not actions:
        return False  # 无动作可执行
    
    # 按分数排序（降序）
    actions.sort(reverse=True, key=lambda x: x[0])
    
    # 选择最佳行动（加入一些随机性）
    if random.random() < 0.8 or len(actions) == 1:
        best_action = actions[0]
    else:
        best_action = random.choice(actions[:min(3, len(actions))])
    
    score, sr, sc, tr, tc, action_type = best_action
    chip = board[sr][sc]
    target = board[tr][tc]
    
    # 执行行动
    animate_ai_select(sr, sc, draw_board)
    
    if action_type == 'move':
        # 移动
        animate_move(sr, sc, tr, tc, chip)
        board[tr][tc], board[sr][sc] = chip, None
        return True
        
    elif action_type in ['attack_attempt', 'fusion_attempt']:
        # 尝试攻击（不知道结果）
        if chip.name == "athena" or target.name == "athena":
            # Athena 融合
            animate_athena_fusion(sr, sc, tr, tc, draw_board)
            board[sr][sc] = board[tr][tc] = None
            return True
        elif can_attack(chip, target):
            # 攻击成功（AI 事后才知道）
            defeat_updated = False
            if should_update_defeat(chip.defeat, target.name):
                chip.defeat = target.name
                defeat_updated = True
            animate_move(sr, sc, tr, tc, chip)
            board[tr][tc], board[sr][sc] = chip, None
            if defeat_updated:
                animate_defeat_update(tr, tc, draw_board)
            # 更新记忆：成功击败了这个位置的玩家
            update_ai_memory_from_observation((tr, tc), (sr, sc), "ai_win")
            return True
        else:
            # 攻击失败（AI 从失败中学习）
            animate_attack_failed(sr, sc, tr, tc, chip, draw_board)
            board[sr][sc] = None
            # 更新记忆：这个玩家棋子很强
            update_ai_memory_from_defeat((sr, sc), (tr, tc), chip.name)
            return True
    
    return False