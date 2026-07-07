# 五子棋 Gomoku — Python in the Browser

**🎮 立即遊玩：<https://ychung1998.github.io/gomoku/>**

15×15 五子棋。遊戲邏輯與 AI 全部在 `gomoku.py`（純 Python），由 [Pyodide](https://pyodide.org)（WebAssembly）直接在瀏覽器執行；`index.html` 的 JS 只負責畫棋盤與接滑鼠。

## 怎麼玩

1. 開啟上方網址，等 2–5 秒讓 Pyodide 載入（狀態列會顯示「輪到 ⚫ 黑方」即就緒）。
2. 左上選單選模式：**人機對戰**（你執黑先手，AI 執白）或 **雙人 PK**（同一台輪流點）。
3. 點棋盤交叉點落子，紅框標示最後一手；先連五者勝。
4. **悔棋**：人機模式自動撤回「AI 一手＋你一手」，回到你行棋；雙人模式撤一手。
5. **重新開始** 或切換模式都會開新局。

## 功能

- 人機對戰（啟發式 AI：能贏就贏、否則優先阻擋對手活四/沖四；執黑時自動避禁手）
- 雙人 PK
- 悔棋（人機模式自動撤回 AI＋你各一手）
- 勝負判定：橫、直、雙斜五連
- **連珠禁手**（預設開啟，可關）：黑方長連/雙四/雙活三禁止落子並顯示原因；五最大；
  白方無限制。規則詳見 [rules.html](rules.html)，規範來源 [587.renju.org.tw](https://587.renju.org.tw/teach/teach018.htm)

## 本機試玩

```bash
python3 -m http.server 8000
# 開 http://localhost:8000（不能直接雙擊 index.html，fetch 會被 file:// 擋）
```

## 跑測試

```bash
python3 -m pytest tests/ -q   # 26 個案例（含連珠禁手與抗辯反例回歸）
```

## CI/CD

`.github/workflows/ci-deploy.yml`：push 到 `main` → 跑 13 個 pytest → **全綠才部署** Pages；PR 只跑測試不部署。
啟用方式：repo **Settings → Pages → Source 改選 "GitHub Actions"**（否則仍是分支直接部署，測試失敗也會上線）。

## 檔案

| 檔案 | 說明 |
|---|---|
| `gomoku.py` | 規則 + 悔棋 + AI（測試與瀏覽器共用同一份） |
| `index.html` | Pyodide 載入器 + Canvas 畫面 |
| `tests/test_gomoku.py` | pytest 測試 |
