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


def test_state_json_roundtrip():
    g = Game()
    g.place(7, 7)
    s = json.loads(g.state())
    assert s["last"] == [7, 7] and s["current"] == WHITE and s["moves"] == 1
    assert s["winner"] is None and s["board"][7][7] == BLACK
