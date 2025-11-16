# network.py
# 通用网络辅助：发送/接收 JSON（4 字节长度前缀）
import json
import struct
import socket

def send_json(sock: socket.socket, obj: dict):
    """
    将 JSON 对象发送到 socket，前置 4 字节大端长度。
    使用时捕获异常（连接断开等）。
    """
    try:
        data = json.dumps(obj).encode('utf-8')
        length = struct.pack('>I', len(data))
        sock.sendall(length + data)
    except Exception as e:
        # 上层处理异常（断线等）
        raise

def recv_json(sock: socket.socket):
    """
    从 socket 读取 4 字节长度，然后读取完整 payload 并解析为 JSON。
    若连接关闭则返回 None 或抛异常（上层处理）。
    """
    # 读取 4 字节长度
    try:
        length_bytes = recv_all(sock, 4)
        if not length_bytes:
            return None
        length = struct.unpack('>I', length_bytes)[0]
        payload = recv_all(sock, length)
        if not payload:
            return None
        return json.loads(payload.decode('utf-8'))
    except Exception:
        # 上层处理
        return None

def recv_all(sock: socket.socket, n: int):
    """
    从 socket 中读取恰好 n 字节（或在 EOF 时返回 None）。
    """
    data = b''
    while len(data) < n:
        try:
            chunk = sock.recv(n - len(data))
        except Exception:
            return None
        if not chunk:
            return None
        data += chunk
    return data
