# Inazuma Semi AFK

一個以畫面辨識為基礎的半自動按鍵工具。

現在的使用流程是：

1. 先自行準備好遊戲畫面的模板圖片
2. 把圖片放進 `templates/`
3. 在 `config.json` 設定每張圖對應的按鍵
4. 執行程式後持續監看螢幕
5. 畫面中出現指定模板時自動按下對應按鍵

如果你只是先測試程式能不能跑，`scenes` 可以先留空，這樣程式會正常啟動待機，但不會讀取任何圖片。

目前範例已經內建第一條規則：

- 讀取 `templates/find_level.png`
- 畫面命中後按下 `Enter`
- `find_level` 目前使用 `template` 模式，適合用裁切後的小圖做比對

你也可以像目前設定這樣，把多條規則串起來，例如：

- 讀到 `find_level` 後按 `Enter`
- 讀到 `choose_level` 後連按四次 `Down`

## 適合的用途

- 偵測「可互動」提示後自動按鍵
- 偵測確認按鈕或結算畫面後自動處理
- 偵測固定 UI 圖示後執行技能、補血或切換流程

## 先決條件

- Windows
- Python 3.10 以上

## 安裝

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.json config.json
```

## 執行

```powershell
python main.py
```

啟動後程式會先進入待機模式，不會立刻開始監控。

- `Alt+1`: 開始監控
- `Alt+0`: 停止監控，但不退出程式
- `F8`: 結束整個程式

如果你想直接雙擊啟動，也可以使用：

- `start_bot.bat`: 啟動主程式

## 設定方式

主要設定在 `config.json`：

- `capture_region`: 基礎偵測範圍，設成 `null` 代表監看整個主螢幕
- `loop_interval_ms`: 每輪偵測間隔
- `stop_key`: 停止程式的熱鍵
- `debug`: 是否輸出偵測分數
- `scenes`: 規則列表

每個 `scene` 包含：

- `name`: 規則名稱
- `template`: 模板圖片路徑
- `threshold`: 命中門檻，通常 `0.85 ~ 0.97`
- `cooldown_ms`: 觸發後冷卻
- `search_region`: 只在基礎偵測區域中的局部範圍搜尋，設成 `null` 代表整個基礎區域
- `match_mode`: `template` 或 `exact_frame`
- `pixel_tolerance`: `exact_frame` 模式下允許的單像素亮度誤差
- `actions`: 命中後要做的事情

支援的 `actions`：

- `press`: 按一下按鍵
- `keyDown`: 按住
- `keyUp`: 放開
- `sleep`: 暫停幾毫秒

`match_mode` 說明：

- `template`: 適合用小型 UI 圖片在大畫面中搜尋
- `exact_frame`: 適合整張畫面幾乎固定不變，而且你想排除相似畫面的情況

`actions` 也支援 `repeat`，適合重複按鍵流程，例如連按四次 `down`：

```json
{
  "type": "repeat",
  "times": 4,
  "delay_ms": 120,
  "actions": [
    {
      "type": "press",
      "key": "down"
    }
  ]
}
```

## 模板圖片準備方式

先用任何你習慣的截圖工具，把遊戲中你想辨識的 UI 小區塊截下來，放到 `templates/` 目錄。

建議：

- 只截穩定不變的 UI 區塊
- 不要截太大
- 盡量避開會閃爍、會動態變化的元素
- 若誤判高，改小截圖範圍或提高 `threshold`
- 若效能不夠，優先為該規則設定 `search_region`

## 實務建議

- 先只做 1 到 2 個規則，確認辨識穩定後再擴充
- 若遊戲是 DirectX 全螢幕，建議改成無邊框視窗或視窗模式
- 某些遊戲對輸入方式比較敏感，這份範例用的是 `pydirectinput`

## 下一步可以擴充

- 加入顏色檢測或 OCR
- 加入「狀態機」避免不同場景互相搶按鍵
- 加入前景視窗檢查，只在遊戲視窗位於前景時才動作

## 專案結構

- `main.py`: 程式入口，只負責載入設定並啟動引擎
- `afkbot/config.py`: 讀取與解析 `config.json`
- `afkbot/models.py`: 設定與規則資料模型
- `afkbot/hotkeys.py`: 熱鍵判斷與防重複觸發
- `afkbot/vision.py`: 截圖、區域換算與模板比對
- `afkbot/actions.py`: 按鍵與延遲動作執行
- `afkbot/engine.py`: 主循環、監控狀態與規則觸發
