# main_lan.py (LAN 客户端)
import pygame
import socket
import threading
import argparse
from settings import *
from board import board, defeat_board, random_init, draw_board, can_attack, check_winner, should_update_defeat
from animations import animate_move, animate_athena_fusion, animate_defeat_update, animate_attack_failed
from network import send_json, recv_json

class LANClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.sock = None
        self.my_side = None  # 'A' or 'B'
        self.current_turn = None  # 'A' or 'B'
        self.connected = False
        self.peer_disconnected = False
        self.game_started = False
        
        # 消息队列（从网络线程接收）
        self.message_queue = []
        self.message_lock = threading.Lock()
        
    def connect(self):
        """连接到服务器"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_host, self.server_port))
            print(f"[CLIENT] Connected to server {self.server_host}:{self.server_port}")
            self.connected = True
            
            # 启动接收线程
            recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
            recv_thread.start()
            return True
        except Exception as e:
            print(f"[CLIENT] Connection failed: {e}")
            return False
    
    def receive_loop(self):
        """接收消息的线程"""
        while self.connected:
            try:
                msg = recv_json(self.sock)
                if msg is None:
                    print("[CLIENT] Server disconnected")
                    self.connected = False
                    break
                
                with self.message_lock:
                    self.message_queue.append(msg)
            except Exception as e:
                print(f"[CLIENT] Receive error: {e}")
                self.connected = False
                break
    
    def send_move(self, from_pos, to_pos, action_type, defeat_info=None):
        """发送移动消息"""
        msg = {
            "type": "move",
            "from": from_pos,
            "to": to_pos,
            "action": action_type
        }
        if defeat_info:
            msg["defeat"] = defeat_info
        try:
            send_json(self.sock, msg)
            return True
        except Exception as e:
            print(f"[CLIENT] Send error: {e}")
            return False
    
    def get_messages(self):
        """获取所有待处理消息"""
        with self.message_lock:
            msgs = self.message_queue.copy()
            self.message_queue.clear()
        return msgs
    
    def close(self):
        """关闭连接"""
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass

def apply_opponent_move(msg):
    """应用对方的移动到本地棋盘"""
    sr, sc = msg["from"]
    tr, tc = msg["to"]
    action = msg["action"]
    
    chip = board[sr][sc]
    target = board[tr][tc]
    
    if action == "move":
        # 普通移动
        animate_move(sr, sc, tr, tc, chip)
        board[tr][tc], board[sr][sc] = chip, None
        
    elif action == "attack_success":
        # 攻击成功
        if should_update_defeat(chip.defeat, target.name):
            chip.defeat = target.name
        animate_move(sr, sc, tr, tc, chip)
        board[tr][tc], board[sr][sc] = chip, None
        if "defeat" in msg and msg["defeat"]:
            animate_defeat_update(tr, tc, draw_board)
            
    elif action == "attack_fail":
        # 攻击失败
        animate_attack_failed(sr, sc, tr, tc, chip, draw_board)
        board[sr][sc] = None
        if "defeat" in msg and msg["defeat"]:
            if should_update_defeat(target.defeat, chip.name):
                target.defeat = chip.name
            animate_defeat_update(tr, tc, draw_board)
            
    elif action == "fusion":
        # Athena 融合
        animate_athena_fusion(sr, sc, tr, tc, draw_board)
        board[sr][sc] = board[tr][tc] = None

def main():
    parser = argparse.ArgumentParser(description="LAN Battle Client")
    parser.add_argument("--host", default=DEFAULT_SERVER_HOST, help="Server IP")
    parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help="Server Port")
    args = parser.parse_args()
    
    # 创建客户端并连接
    client = LANClient(args.host, args.port)
    if not client.connect():
        print("[CLIENT] Failed to connect to server. Exiting.")
        return
    
    # 等待服务器消息
    print("[CLIENT] Waiting for game to start...")
    waiting_for_start = True
    seed = None
    
    while waiting_for_start:
        msgs = client.get_messages()
        for msg in msgs:
            if msg["type"] == "welcome":
                client.my_side = msg["side"]
                print(f"[CLIENT] You are Player {client.my_side}")
            elif msg["type"] == "start":
                client.current_turn = msg["first"]
                seed = msg.get("seed", None)
                client.game_started = True
                waiting_for_start = False
                print(f"[CLIENT] Game starting! First turn: {client.current_turn}")
                break
        pygame.time.delay(100)
    
    # 初始化游戏
    random_init(seed)
    clock = pygame.time.Clock()
    running = True
    selected = None
    game_over = False
    winner = None
    turn_count = 0
    turn_timer = TURN_TIME
    last_tick = pygame.time.get_ticks()
    
    # 无动作惩罚
    player_idle_count = 0
    opponent_idle_count = 0
    
    # 等待对方标志
    waiting_for_peer = (client.current_turn != client.my_side)
    
    while running:
        # 检查是否是我的回合
        is_my_turn = (client.current_turn == client.my_side)
        
        draw_board(selected, turn_count, turn_timer, game_over, winner, 
                   waiting_for_peer, client.my_side, client.current_turn)
        
        if game_over:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
            clock.tick(FPS)
            continue
        
        # 处理网络消息
        msgs = client.get_messages()
        for msg in msgs:
            if msg["type"] == "move":
                # 对方的移动
                apply_opponent_move(msg)
                # 切换回合
                client.current_turn = client.my_side
                waiting_for_peer = False
                turn_count += 1
                turn_timer = TURN_TIME
                opponent_idle_count = 0
                
                # 检查游戏结束
                if turn_count >= MAX_TURNS or \
                   not any(b and b.is_player for row in board for b in row) or \
                   not any(b and not b.is_player for row in board for b in row):
                    game_over = True
                    winner = check_winner()
                    
            elif msg["type"] == "peer_disconnect":
                print("[CLIENT] Opponent disconnected")
                client.peer_disconnected = True
                game_over = True
                winner = f"You (opponent left)"
        
        # 时间流逝
        if is_my_turn and not waiting_for_peer:
            now = pygame.time.get_ticks()
            elapsed = (now - last_tick) / 1000
            last_tick = now
            
            if selected:
                turn_timer -= elapsed
                if turn_timer <= 0:
                    # 超时，跳过回合
                    selected = None
                    player_idle_count += 1
                    
                    if player_idle_count >= MAX_IDLE_TURNS:
                        game_over = True
                        winner = "Opponent (You Idle)"
                        continue
                    
                    # 发送空消息表示跳过
                    client.send_move([0,0], [0,0], "idle")
                    client.current_turn = "A" if client.my_side == "B" else "B"
                    waiting_for_peer = True
                    turn_count += 1
                    turn_timer = TURN_TIME
        
        # 处理玩家输入（仅在自己回合）
        if is_my_turn and not waiting_for_peer:
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
                            action_executed = False
                            action_type = None
                            defeat_info = None
                            
                            if target_chip is None:
                                # 移动
                                animate_move(sr, sc, r, c, s_chip)
                                board[r][c], board[sr][sc] = s_chip, None
                                action_type = "move"
                                action_executed = True
                                
                            elif target_chip.is_player != s_chip.is_player:
                                if s_chip.name == "athena" or target_chip.name == "athena":
                                    # 融合
                                    animate_athena_fusion(sr, sc, r, c, draw_board)
                                    board[sr][sc] = board[r][c] = None
                                    action_type = "fusion"
                                    action_executed = True
                                    
                                elif can_attack(s_chip, target_chip):
                                    # 攻击成功
                                    defeat_updated = should_update_defeat(s_chip.defeat, target_chip.name)
                                    if defeat_updated:
                                        s_chip.defeat = target_chip.name
                                        defeat_info = target_chip.name
                                    animate_move(sr, sc, r, c, s_chip)
                                    board[r][c], board[sr][sc] = s_chip, None
                                    action_type = "attack_success"
                                    action_executed = True
                                    
                                else:
                                    # 攻击失败
                                    animate_attack_failed(sr, sc, r, c, s_chip, draw_board)
                                    board[sr][sc] = None
                                    defeat_updated = should_update_defeat(target_chip.defeat, s_chip.name)
                                    if defeat_updated:
                                        target_chip.defeat = s_chip.name
                                        defeat_info = s_chip.name
                                        animate_defeat_update(r, c, draw_board)
                                    action_type = "attack_fail"
                                    action_executed = True
                            
                            if action_executed:
                                # 发送移动消息
                                client.send_move([sr, sc], [r, c], action_type, defeat_info)
                                selected = None
                                player_idle_count = 0
                                
                                # 切换回合
                                client.current_turn = "A" if client.my_side == "B" else "B"
                                waiting_for_peer = True
                                turn_timer = TURN_TIME
                        else:
                            selected = (r, c) if clicked and clicked.is_player else None
                    else:
                        if clicked and clicked.is_player:
                            selected = (r, c)
        else:
            # 不是我的回合，只处理退出事件
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
        
        clock.tick(FPS)
    
    client.close()
    pygame.quit()

if __name__ == "__main__":
    main()