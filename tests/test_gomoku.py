# -*- coding: utf-8 -*-
"""五子棋核心邏輯測試（FABLE-PROTOCOL fail-then-pass：先紅後綠）。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from gomoku import Game, BLACK, WHITE, EMPTY, SIZE


def test_initial_state():
    g = Game()
    assert g.current == BLACK and g.winner is None
    assert all(cell == EMPTY for row in g.board for cell in row)


def test_place_alternates_turns():
    g = Game()
    assert g.place(7, 7) and g.current == WHITE
    assert g.place(7, 8) and g.current == BLACK


def test_occupied_and_out_of_bounds_rejected():
    g = Game()
    g.place(7, 7)
    assert not g.place(7, 7)          # 佔位
    assert not g.place(-1, 0)         # 出界
    assert not g.place(SIZE, 0)


def test_horizontal_win():
    g = Game()
    for c in range(4):
        g.place(7, c); g.place(8, c)  # 黑走 7 列，白走 8 列
    g.place(7, 4)                     # 黑第五子
    assert g.winner == BLACK


def test_vertical_and_both_diagonal_wins():
    for dr, dc in ((1, 0), (1, 1), (1, -1)):
        g = Game()
        for i in range(4):
            g.place(5 + dr * i, 7 + dc * i)
            g.place(0, i)             # 白亂走
        g.place(5 + dr * 4, 7 + dc * 4)
        assert g.winner == BLACK, f"方向 {(dr, dc)} 未判勝"


def test_no_moves_after_win():
    g = Game()
    for c in range(4):
        g.place(7, c); g.place(8, c)
    g.place(7, 4)
    assert not g.place(9, 9)


def test_undo_restores_board_turn_and_winner():
    g = Game()
    g.place(7, 7)                     # 黑
    g.place(7, 8)                     # 白
    assert g.undo() == 1              # 悔白棋
    assert g.board[7][8] == EMPTY and g.current == WHITE
    # 悔棋能撤銷勝局
    g2 = Game()
    for c in range(4):
        g2.place(7, c); g2.place(8, c)
    g2.place(7, 4)
    assert g2.winner == BLACK
    g2.undo()
    assert g2.winner is None and g2.current == BLACK


def test_undo_two_for_ai_mode():
    g = Game()
    g.place(7, 7); g.place(0, 0)
    assert g.undo(2) == 2
    assert g.current == BLACK and len(g.history) == 0
    assert g.undo() == 0              # 空棋盤悔棋安全


def test_ai_takes_winning_move():
    g = Game()
    # 黑（AI 方）已四連 (7,0)-(7,3)，白子墊場
    for c in range(4):
        g.place(7, c); g.place(10, c)
    r, c = g.ai_move()                # 輪到黑
    g.place(r, c)
    assert g.winner == BLACK, f"AI 放 {(r, c)} 未取勝"


def test_ai_blocks_opponent_four():
    g = Game()
    # 白（對手）四連 (7,1)-(7,4)，(7,0) 被黑堵住、(7,5) 開放 → AI(黑)必須堵 (7,5)
    g.place(7, 0)                     # 黑
    g.place(7, 1)                     # 白
    g.place(0, 0)                     # 黑
    g.place(7, 2)                     # 白
    g.place(0, 1)                     # 黑
    g.place(7, 3)                     # 白
    g.place(0, 2)                     # 黑
    g.place(7, 4)                     # 白，四連
    assert g.current == BLACK
    assert g.ai_move() == (7, 5), "AI 未阻擋對手四連"


def test_ai_first_move_center():
    g = Game()
    assert g.ai_move() == (SIZE // 2, SIZE // 2)


def test_undo_after_human_win_returns_black_turn():
    """抗辯 REFUTED 修正案：人機模式人類(黑)致勝後悔棋，須回到黑方行棋（不可換色）。
    鏡射 index.html 的 JS 邏輯：undo(1) 後若 current != BLACK 再 undo(1)。"""
    g = Game()
    for c in range(4):
        g.place(7, c); g.place(8, c)
    g.place(7, 4)                     # 黑勝（奇數手結尾）
    g.undo(1)
    if g.current != BLACK:
        g.undo(1)
    assert g.current == BLACK and g.winner is None
    # 對照組：AI(白)剛下完的偶數手情境，同一邏輯須撤兩手
    g2 = Game()
    g2.place(7, 7); g2.place(0, 0)    # 黑、白(AI)
    g2.undo(1)
    if g2.current != BLACK:
        g2.undo(1)
    assert g2.current == BLACK and len(g2.history) == 0


# ────────────────────────── 連珠禁手（renju=True 預設） ──────────────────────────
# 規範來源：https://587.renju.org.tw/teach/teach018.htm
# 黑禁：長連(≥6)、雙四、雙活三；五最大（成五同時成禁 → 黑勝）；白方無任何限制。

def _setup(black_cells, white_cells, renju=True):
    """直接鋪盤（繞過輪替），回傳輪到黑方的 Game。"""
    g = Game(renju=renju)
    for r, c in black_cells:
        g.board[r][c] = BLACK
        g.history.append((r, c))
    for r, c in white_cells:
        g.board[r][c] = WHITE
        g.history.append((r, c))
    g.current = BLACK
    return g


def test_forbidden_overline():
    # 黑 (7,1)(7,2)(7,3) + (7,5)(7,6)(7,7)，下 (7,4) 成七連 → 長連禁手
    g = _setup([(7, 1), (7, 2), (7, 3), (7, 5), (7, 6), (7, 7)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)])
    assert not g.place(7, 4)
    assert "長連" in g.reject_reason
    assert g.board[7][4] == EMPTY and g.current == BLACK  # 盤面不變、仍輪黑


def test_five_beats_forbidden():
    # (7,7) 同時成「橫五」與「縱雙活三之一」→ 五最大，判黑勝
    g = _setup([(7, 3), (7, 4), (7, 5), (7, 6), (5, 7), (6, 7)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)])
    assert g.place(7, 7)
    assert g.winner == BLACK


def test_forbidden_double_four():
    # (7,6)：橫 (7,3)(7,4)(7,5)+落點 成四；縱 (4,6)(5,6)(6,6)+落點 成四 → 四四禁手
    g = _setup([(7, 3), (7, 4), (7, 5), (4, 6), (5, 6), (6, 6)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)])
    assert not g.place(7, 6)
    assert "四四" in g.reject_reason


def test_forbidden_double_four_same_line():
    # 同一線雙四（教學頁：四四可形成在同一線上）：黑 BBB_?_BBB，下中點 ? 後
    # 左側填 (7,4) 成恰五、右側填 (7,6) 成恰五 → 一子成兩個四
    g = _setup([(7, 1), (7, 2), (7, 3), (7, 7), (7, 8), (7, 9)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)])
    assert not g.place(7, 5)
    assert "四四" in g.reject_reason


def test_forbidden_double_three():
    # (7,6)：橫 (7,4)(7,5)+落點 成活三；縱 (5,6)(6,6)+落點 成活三 → 三三禁手
    g = _setup([(7, 4), (7, 5), (5, 6), (6, 6)],
               [(0, 0), (0, 1), (0, 2), (0, 3)])
    assert not g.place(7, 6)
    assert "三三" in g.reject_reason


def test_blocked_three_not_forbidden():
    # 教學頁易誤判：其中一條三被白擋住端點、無法成活四 → 只算一個活三，不禁
    g = _setup([(7, 4), (7, 5), (5, 6), (6, 6)],
               [(7, 3), (0, 0), (0, 1), (0, 2)])   # 白擋 (7,3)
    assert g.place(7, 6)                            # 合法落子
    assert g.winner is None


def test_pseudo_three_shadowed_by_overline_not_forbidden():
    # 教學頁易誤判：橫向 (7,2)(7,3)(7,4) 因遠處 (7,0) 黑子——
    # 四點 (7,1) 會直接成五（跳到勝利、非活四）、四點 (7,5) 的活四左端會成六連
    # → 橫向不算活三（實為一個「四」），縱向 (5,3)(6,3)+落點 為真活三
    # 合計＝四三，合法（抗辯 skeptic 版易誤判重構案）
    g = _setup([(7, 0), (7, 2), (7, 4), (5, 3), (6, 3)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)])
    assert g.place(7, 3)
    assert g.winner is None


def test_four_three_is_legal():
    # 抗辯 REFUTED 反例 C1 固化：四三是連珠標準勝著，不得誤禁
    # (7,6)：橫 (7,4)(7,5)+落點+(7,7) 成活四；縱 (4,6)(5,6)+落點 成跳活三 → 四三合法
    g = _setup([(7, 4), (7, 5), (7, 7), (4, 6), (5, 6)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)])
    assert g.place(7, 6), f"四三被誤禁：{g.reject_reason}"
    assert g.winner is None


def test_double_jump_three_forbidden():
    # 抗辯 REFUTED 反例 C4 固化：兩個「跳活三」的交點是真三三，必須禁
    # (7,7)：橫 (7,4)(7,5)_落點 跳三（四點 (7,6) 為合法四三點）；
    #        縱 落點_(9,7)(10,7) 跳三（四點 (8,7) 合法）→ 雙活三
    g = _setup([(7, 4), (7, 5), (9, 7), (10, 7), (4, 6), (5, 6)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)])
    assert not g.place(7, 7)
    assert "三三" in g.reject_reason


def test_undo_clears_reject_reason():
    # 抗辯次要發現固化：禁手被拒後悔棋，reject_reason 不得殘留
    g = _setup([(7, 4), (7, 5), (5, 6), (6, 6)],
               [(0, 0), (0, 1), (0, 2), (0, 3)])
    assert not g.place(7, 6) and g.reject_reason
    g.undo(1)
    assert g.reject_reason is None


def test_white_has_no_restrictions():
    # 白方雙活三合法；白長連算勝
    g = _setup([(0, 10), (0, 11), (1, 10), (1, 11)],
               [(7, 4), (7, 5), (5, 6), (6, 6)])
    g.current = WHITE
    assert g.place(7, 6)                            # 白雙三合法
    assert g.winner is None
    g2 = _setup([(0, 10), (0, 11), (0, 12), (1, 10), (1, 11), (1, 12)],
                [(7, 1), (7, 2), (7, 3), (7, 5), (7, 6)])
    g2.current = WHITE
    assert g2.place(7, 4)                           # 白六連
    assert g2.winner == WHITE


def test_black_overline_wins_when_renju_off():
    g = _setup([(7, 1), (7, 2), (7, 3), (7, 5), (7, 6), (7, 7)],
               [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)], renju=False)
    assert g.place(7, 4)                            # 自由規則：七連照贏
    assert g.winner == BLACK


def test_ai_black_avoids_forbidden_point():
    # 雙三交點是全盤最高分，AI 執黑必須避開它
    g = _setup([(7, 4), (7, 5), (5, 6), (6, 6)],
               [(0, 0), (0, 1), (0, 2), (0, 3)])
    mv = g.ai_move()
    assert mv != (7, 6)
    assert g.forbidden(*mv) is None


def test_state_json_roundtrip():
    g = Game()
    g.place(7, 7)
    s = json.loads(g.state())
    assert s["last"] == [7, 7] and s["current"] == WHITE and s["moves"] == 1
    assert s["winner"] is None and s["board"][7][7] == BLACK
