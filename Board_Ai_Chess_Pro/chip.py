# chip.py
class Chip:
    """
    棋子类，包含：
      - name: 棋子名字（kyo / mai / orichi 等）
      - is_player: 是否为玩家一方
      - defeat: 曾击败的棋子名称（用于背面显示，跟随棋子移动）
    """
    def __init__(self, name, is_player=True):
        self.name = name
        self.is_player = is_player
        self.defeat = None  # 记录击败过的最高等级棋子

    def __repr__(self):
        return f"{'P' if self.is_player else 'A'}:{self.name}"