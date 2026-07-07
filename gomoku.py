# -*- coding: utf-8 -*-
"""五子棋核心邏輯（純 Python，無相依套件——同一份檔案直接被 Pyodide 載入瀏覽器執行）。

規則：15x15、黑先。預設連珠規則（renju=True）：黑方恰五勝、禁手（長連/四四/雙活三）
禁止落子、五最大（成五同時成禁判黑勝）；白方無限制、白長連亦勝。
renju=False 為自由規則：雙方五連以上皆勝、無禁手。
規範來源：https://587.renju.org.tw/teach/teach018.htm
功能：落子、勝負判定、禁手判定 forbidden()、悔棋 undo(n)、啟發式 AI（黑方自動避禁）。
測試：tests/test_gomoku.py（26 案例，fail-then-pass 已驗證）。
"""
import json

EMPTY, BLACK, WHITE = 0, 1, 2
SIZE = 15
DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Game:
    def __init__(self, renju=True):
        self.board = [[EMPTY] * SIZE for _ in range(SIZE)]
        self.history = []
        self.current = BLACK
        self.winner = None  # None / BLACK / WHITE / "draw"
        self.renju = renju
        self.reject_reason = None  # 最近一次 place 被拒的禁手原因（給前端顯示）

    # ── 落子與勝負 ──────────────────────────────────────────
    def place(self, r, c):
        """落子。成功回 True；已分勝負、出界、佔位、禁手皆回 False。
        禁手拒絕時 reject_reason 會帶原因字串。"""
        self.reject_reason = None
        if self.winner is not None:
            return False
        if not (0 <= r < SIZE and 0 <= c < SIZE) or self.board[r][c] != EMPTY:
            return False
        if self.renju and self.current == BLACK:
            reason = self.forbidden(r, c)
            if reason is not None:
                self.reject_reason = reason
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

    def _run(self, r, c, dr, dc):
        """通過 (r,c) 沿 ±(dr,dc) 的同色連續子數（含自身）。"""
        color = self.board[r][c]
        count = 1
        for s in (1, -1):
            nr, nc = r + dr * s, c + dc * s
            while 0 <= nr < SIZE and 0 <= nc < SIZE and self.board[nr][nc] == color:
                count += 1
                nr += dr * s
                nc += dc * s
        return count

    def _wins(self, r, c):
        color = self.board[r][c]
        exact_five = self.renju and color == BLACK  # 連珠：黑方恰五才勝（長連是禁手）
        for dr, dc in DIRS:
            n = self._run(r, c, dr, dc)
            if n == 5 or (not exact_five and n >= 5):
                return True
        return False

    # ── 連珠禁手判定（僅黑方） ──────────────────────────────
    def forbidden(self, r, c, _depth=0):
        """黑方於 (r,c) 落子是否禁手。回 '長連禁手'/'四四禁手'/'三三禁手' 或 None。
        規則：五最大（成五不算禁）；活三的活四點不可同時形成五或禁手（遞迴判定）。"""
        if not self.renju or not (0 <= r < SIZE and 0 <= c < SIZE):
            return None
        if self.board[r][c] != EMPTY:
            return None
        self.board[r][c] = BLACK
        try:
            runs = [self._run(r, c, dr, dc) for dr, dc in DIRS]
            if any(n == 5 for n in runs):
                return None            # 五最大：成五同時成禁 → 黑勝
            if any(n >= 6 for n in runs):
                return "長連禁手"
            fours = set()
            for dr, dc in DIRS:
                fours |= self._fours(r, c, dr, dc)
            if len(fours) >= 2:
                return "四四禁手"
            threes = sum(1 for dr, dc in DIRS
                         if self._is_live_three(r, c, dr, dc, _depth))
            if threes >= 2:
                return "三三禁手"
            return None
        finally:
            self.board[r][c] = EMPTY

    def _fours(self, r, c, dr, dc):
        """(r,c) 已為黑。回傳該方向所有「四」的黑子集合（frozenset 去重：
        活四兩個成五點屬同一個四）。四＝五格窗含 4 黑 1 空，且補上空點成『恰五』。"""
        found = set()
        for off in range(-4, 1):
            cells = [(r + dr * (off + i), c + dc * (off + i)) for i in range(5)]
            if not all(0 <= x < SIZE and 0 <= y < SIZE for x, y in cells):
                continue
            blacks = [p for p in cells if self.board[p[0]][p[1]] == BLACK]
            empties = [p for p in cells if self.board[p[0]][p[1]] == EMPTY]
            if len(blacks) != 4 or len(empties) != 1:
                continue
            er, ec = empties[0]
            self.board[er][ec] = BLACK
            makes_exact_five = self._run(er, ec, dr, dc) == 5
            self.board[er][ec] = EMPTY
            if makes_exact_five:
                found.add(frozenset(blacks))
        return found

    def _has_live_four(self, r, c, dr, dc):
        """(r,c) 為黑。該方向通過 (r,c) 是否為活四：恰四連、兩端皆空且兩端補子皆成恰五。"""
        if self._run(r, c, dr, dc) != 4:
            return False
        for s in (1, -1):
            nr, nc = r, c
            while (0 <= nr + dr * s < SIZE and 0 <= nc + dc * s < SIZE
                   and self.board[nr + dr * s][nc + dc * s] == BLACK):
                nr += dr * s
                nc += dc * s
            er, ec = nr + dr * s, nc + dc * s
            if not (0 <= er < SIZE and 0 <= ec < SIZE) or self.board[er][ec] != EMPTY:
                return False
            self.board[er][ec] = BLACK
            exact_five = self._run(er, ec, dr, dc) == 5
            self.board[er][ec] = EMPTY
            if not exact_five:
                return False
        return True

    def _is_live_three(self, r, c, dr, dc, depth=0):
        """(r,c) 已為黑。該方向是否活三：存在空點 e，黑補 e 後成活四，
        且 e 不同時形成五（任何方向）或禁手（遞迴，深度上限防爆）。"""
        if self._fours(r, c, dr, dc):
            return False  # 該方向已是「四」（次一手成五）→ 是四不是三；否則四三會被誤判三三
        for off in range(-4, 5):
            er, ec = r + dr * off, c + dc * off
            if not (0 <= er < SIZE and 0 <= ec < SIZE) or self.board[er][ec] != EMPTY:
                continue
            self.board[er][ec] = BLACK
            try:
                if not self._has_live_four(r, c, dr, dc):
                    continue
                if any(self._run(er, ec, d[0], d[1]) == 5 for d in DIRS):
                    continue           # 活四點同時成五 → 該三不算活三
            finally:
                self.board[er][ec] = EMPTY
            if depth >= 3:
                return True            # 遞迴保護：深層視為活三（偏嚴，寧禁勿漏）
            if self.forbidden(er, ec, _depth=depth + 1) is None:
                return True            # 活四點本身非禁手 → 真活三
        return False

    # ── 悔棋 ────────────────────────────────────────────────
    def undo(self, n=1):
        """悔 n 手，回實際撤銷數。人機模式由前端呼叫 undo(1) 後視 current 決定是否再 undo(1)，
        保證悔棋後回到人類（黑）行棋——見 index.html 悔棋 handler 與 test_undo_after_human_win_*。"""
        self.reject_reason = None
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
        avoid_forbidden = self.renju and me == BLACK
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] != EMPTY or not self._near_stone(r, c):
                    continue
                if avoid_forbidden and self.forbidden(r, c) is not None:
                    continue
                score = self._score(r, c, me) * 1.1 + self._score(r, c, opp)
                if score > best_score:
                    best_score, best = score, (r, c)
        if best is None:  # 幾乎不可達（候選格全為禁手時），後備：任一非禁空格
            best = next(((r, c) for r in range(SIZE) for c in range(SIZE)
                         if self.board[r][c] == EMPTY
                         and not (avoid_forbidden and self.forbidden(r, c))), None)
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
