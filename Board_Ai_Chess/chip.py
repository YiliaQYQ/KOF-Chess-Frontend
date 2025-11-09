# chip.py
class Chip:
    """
    棋子类，包含：
      - name: 棋子名字（kyo / mai / orichi 等）
      - is_player: 是否为玩家一方
    
    注意: defeat 信息统一由 board.defeat_board 管理,不在棋子对象中存储
    """
    def __init__(self, name, is_player=True):
        self.name = name
        self.is_player = is_player

    def __repr__(self):
        return f"{'P' if self.is_player else 'A'}:{self.name}"