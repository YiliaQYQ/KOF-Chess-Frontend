# server.py
# 简单的局域网房间服务器（转发两端消息并在两端建立初始同步）
import socket
import threading
import argparse
import random
from network import send_json, recv_json

HOST = '0.0.0.0'
PORT = 50007  # 可改端口

def handle_client(conn, addr, label, other_conn):
    """
    仅作为接收与转发线程的占位（具体逻辑在主线程的转发循环中）
    """
    pass

def relay_loop(conn_a, conn_b):
    """
    主转发循环：不停读取两端消息并转发给对端。
    结构：每条消息为 JSON，包含 "type" 字段。Server 不改动消息体（除了 start）。
    """
    sockets = {'A': conn_a, 'B': conn_b}
    conns = [conn_a, conn_b]
    labels = {conn_a: 'A', conn_b: 'B'}

    def forward_from(src_sock, dst_sock):
        while True:
            msg = recv_json(src_sock)
            if msg is None:
                # 对端断开，通知另一端并结束
                try:
                    send_json(dst_sock, {"type":"peer_disconnect"})
                except:
                    pass
                return
            # 在消息中加入来源信息，便于客户端判断是谁发的
            msg['_from'] = labels.get(src_sock, None)
            try:
                send_json(dst_sock, msg)
            except Exception:
                return

    # 启动两个线程，各自从一个 socket 读取并转发到另一个
    t1 = threading.Thread(target=forward_from, args=(conn_a, conn_b), daemon=True)
    t2 = threading.Thread(target=forward_from, args=(conn_b, conn_a), daemon=True)
    t1.start()
    t2.start()
    # 等待线程结束（任一端断开，线程会结束）
    t1.join()
    t2.join()

def start_server(listen_ip='0.0.0.0', listen_port=50007):
    print(f"[SERVER] Starting relay server on {listen_ip}:{listen_port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((listen_ip, listen_port))
    s.listen(2)
    print("[SERVER] Waiting for Player A to connect...")
    conn_a, addr_a = s.accept()
    print(f"[SERVER] Player A connected from {addr_a}")
    send_json(conn_a, {"type":"welcome","side":"A"})

    print("[SERVER] Waiting for Player B to connect...")
    conn_b, addr_b = s.accept()
    print(f"[SERVER] Player B connected from {addr_b}")
    send_json(conn_b, {"type":"welcome","side":"B"})

    # 随机决定先手（A 或 B），并发送初始 start 消息（server 不含棋盘数据，客户端本地生成）
    first = random.choice(["A","B"])
    start_msg = {"type":"start","first": first}
    print(f"[SERVER] Both connected — first: {first}. Broadcasting start.")
    send_json(conn_a, start_msg)
    send_json(conn_b, start_msg)

    # 进入转发循环（收到一方 move/delta，则转发给另一方）
    try:
        relay_loop(conn_a, conn_b)
    finally:
        conn_a.close()
        conn_b.close()
        s.close()
        print("[SERVER] Server closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LAN relay server for Board AI LocalBattle")
    parser.add_argument("--host", default="0.0.0.0", help="listen ip")
    parser.add_argument("--port", type=int, default=50007, help="listen port")
    args = parser.parse_args()
    start_server(args.host, args.port)
