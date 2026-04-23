# Inazuma Semi AFK

一個以畫面辨識為基礎的半自動按鍵工具雛形。

它的核心流程是：

1. 擷取指定螢幕區域
2. 用模板圖片比對目前畫面
3. 命中規則後執行按鍵操作
4. 依冷卻時間避免重複觸發

## 適合的用途

- 根據固定 UI 圖示自動補血
- 偵測「可互動」提示後自動按鍵
- 偵測戰鬥結束或確認視窗後自動處理

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

預設停止熱鍵是 `F8`。

如果你想直接雙擊啟動，也可以使用：

- `start_bot.bat`: 啟動主程式
- `capture_template.bat`: 啟動截圖取樣工具

## 截圖取樣工具

你可以先用工具把遊戲 UI 裁成模板圖：

```powershell
python capture_tool.py --name battle_ready
```

流程如下：

1. 先把遊戲畫面切到前景
2. 執行工具後等待 3 秒倒數
3. 工具會截取主螢幕並跳出框選視窗
4. 用滑鼠框選要辨識的 UI 小區塊
5. 按 Enter 存檔，按 `C` 取消

若不指定 `--name`，工具會自動用時間命名。輸出位置預設在 `templates/`。
存檔後，工具也會同步印出一段可直接貼進 `config.json` 的 `capture_region` JSON。

## 設定方式

主要設定在 `config.json`：

- `capture_region`: 要截圖辨識的畫面範圍
- `loop_interval_ms`: 每輪偵測間隔
- `stop_key`: 停止程式的熱鍵
- `debug`: 是否輸出偵測分數
- `scenes`: 規則列表

每個 `scene` 包含：

- `name`: 規則名稱
- `template`: 模板圖片路徑
- `threshold`: 命中門檻，通常 `0.85 ~ 0.97`
- `cooldown_ms`: 觸發後冷卻
- `actions`: 命中後要做的事情

支援的 `actions`：

- `press`: 按一下按鍵
- `keyDown`: 按住
- `keyUp`: 放開
- `sleep`: 暫停幾毫秒

## 模板圖片怎麼做

把遊戲中你想辨識的 UI 截一小塊圖，放到 `templates/` 目錄。

建議：

- 只截穩定不變的 UI 區塊
- 不要截太大
- 盡量避開會閃爍、會動態變化的元素
- 若誤判高，改小截圖範圍或提高 `threshold`

## 實務建議

- 先只做 1 到 2 個規則，確認辨識穩定後再擴充
- 若遊戲是 DirectX 全螢幕，建議改成無邊框視窗或視窗模式
- 某些遊戲對輸入方式比較敏感，這份範例用的是 `pydirectinput`

## 下一步可以擴充

- 指定每個模板只在局部區域搜尋，提升速度與準確率
- 加入顏色檢測或 OCR
- 加入「狀態機」避免不同場景互相搶按鍵
- 加入錄圖工具，直接框選螢幕生成模板
