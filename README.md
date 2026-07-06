# 五子棋 Gomoku — Python in the Browser

15×15 五子棋。遊戲邏輯與 AI 全部在 `gomoku.py`（純 Python），由 [Pyodide](https://pyodide.org)（WebAssembly）直接在瀏覽器執行；`index.html` 的 JS 只負責畫棋盤與接滑鼠。可直接部署 GitHub Pages。

## 功能

- 人機對戰（啟發式 AI：能贏就贏、否則優先阻擋對手活四/沖四）
- 雙人 PK
- 悔棋（人機模式一次撤兩手：AI 一手 + 你一手）
- 勝負判定：橫、直、雙斜五連

## 本機試玩

```bash
python3 -m http.server 8000
# 開 http://localhost:8000（不能直接雙擊 index.html，fetch 會被 file:// 擋）
```

## 跑測試

```bash
python3 -m pytest tests/ -q   # 11 個案例
```

## 發佈到 GitHub Pages

```bash
git init && git add -A && git commit -m "gomoku: python-in-browser via pyodide"
gh repo create gomoku --public --source=. --push
gh api repos/{owner}/gomoku/pages -X POST -f 'source[branch]=main' -f 'source[path]=/'
# 約 1 分鐘後： https://<你的帳號>.github.io/gomoku/
```

沒裝 `gh` 的話：GitHub 網頁建 repo → push → Settings → Pages → Branch 選 `main` / root。

## 檔案

| 檔案 | 說明 |
|---|---|
| `gomoku.py` | 規則 + 悔棋 + AI（測試與瀏覽器共用同一份） |
| `index.html` | Pyodide 載入器 + Canvas 畫面 |
| `tests/test_gomoku.py` | pytest 測試 |
