# -*- coding: utf-8 -*-
"""五子棋核心邏輯（純 Python，無相依套件——同一份檔案直接被 Pyodide 載入瀏覽器執行）。

規則：15x15、黑先、五連即勝（含超過五連）。
功能：落子、勝負判定（四方向）、悔棋 undo(n)、啟發式 AI（攻守雙評分）。
測試：tests/test_gomoku.py（13 案例，fail-then-pass 已驗證）。
"""
import json

EMPTY, BLACK, WHITE = 0, 1, 2
SIZE = 15
DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Game:
    def __init__(self):
        self.board = [[EMPTY] * SIZE for _ in range(SIZE)]
        self.history = []
        self.current = BLACK
        self.winner = None  # None / BLACK / WHITE / "draw"

    # ── 落子與勝負 ──────────────────────────────────────────
    def place(self, r, c):
        """落子。成功回 True；已分勝負、出界、佔位皆回 False。"""
        if self.winner is not None:
            return False
        if not (0 <= r < SIZE and 0 <= c < SIZE) or self.board[r][c] != EMPTY:
            return False
        self.board[r][c] = self.current
        self.history.append((r, c))
        if self._wins(r, c):
            self.winner = self.current
        elif len(self.history) == SIZE * SIZE:
            self.winner = "draw"
        else:
            self.current = WHITE if self.current == BLACK else BLACK
        return True

    def _wins(self, r, c):
        color = self.board[r][c]
        for dr, dc in DIRS:
            count = 1
            for s in (1, -1):
                nr, nc = r + dr * s, c + dc * s
                while 0 <= nr < SIZE and 0 <= nc < SIZE and self.board[nr][nc] == color:
                    count += 1
                    nr += dr * s
                    nc += dc * s
            if count >= 5:
                return True
        return False

    # ── 悔棋 ────────────────────────────────────────────────
    def undo(self, n=1):
        """悔 n 手，回實際撤銷數。人機模式由前端呼叫 undo(1) 後視 current 決定是否再 undo(1)，
        保證悔棋後回到人類（黑）行棋——見 index.html 悔棋 handler 與 test_undo_after_human_win_*。"""
        undone = 0
        for _ in range(n):
            if not self.history:
                break
            r, c = self.history.pop()
            self.current = self.board[r][c]  # 該手的落子者重新行棋
            self.board[r][c] = EMPTY
            self.winner = None
            undone += 1
        return undone

    # ── AI（啟發式：攻守雙評分，自方權重 1.1 保證「能贏就贏、否則先擋」）──
    def ai_move(self):
        """回傳當前行棋方的最佳 (r, c)。空盤開中心。"""
        if not self.history:
            return SIZE // 2, SIZE // 2
        me = self.current
        opp = WHITE if me == BLACK else BLACK
        best, best_score = None, -1.0
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] != EMPTY or not self._near_stone(r, c):
                    continue
                score = self._score(r, c, me) * 1.1 + self._score(r, c, opp)
                if score > best_score:
                    best_score, best = score, (r, c)
        if best is None:  # 理論上不可達（有子必有鄰空格），防禦性後備
            best = next(((r, c) for r in range(SIZE) for c in range(SIZE)
                         if self.board[r][c] == EMPTY), None)
        return best

    def _near_stone(self, r, c, dist=2):
        for dr in range(-dist, dist + 1):
            for dc in range(-dist, dist + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and self.board[nr][nc] != EMPTY:
                    return True
        return False

    def _score(self, r, c, color):
        """假設 color 落在 (r,c)，四方向連子數 × 開口數的加權總分。"""
        total = 0
        for dr, dc in DIRS:
            count, open_ends = 1, 0
            for s in (1, -1):
                nr, nc = r + dr * s, c + dc * s
                while 0 <= nr < SIZE and 0 <= nc < SIZE and self.board[nr][nc] == color:
                    count += 1
                    nr += dr * s
                    nc += dc * s
                if 0 <= nr < SIZE and 0 <= nc < SIZE and self.board[nr][nc] == EMPTY:
                    open_ends += 1
            if count >= 5:
                total += 10_000_000          # 成五
            elif count == 4:
                total += 100_000 if open_ends == 2 else (10_000 if open_ends else 0)
            elif count == 3:
                total += 1_000 if open_ends == 2 else (100 if open_ends else 0)
            elif count == 2:
                total += 100 if open_ends == 2 else (10 if open_ends else 0)
            else:
                total += 1
        return total

    # ── 給前端 JS 的狀態序列化 ──────────────────────────────
    def state(self):
        return json.dumps({
            "board": self.board,
            "current": self.current,
            "winner": self.winner,
            "moves": len(self.history),
            "last": list(self.history[-1]) if self.history else None,
        })
