import argparse
import json
from datetime import datetime
from pathlib import Path

import cv2
import mss
import numpy as np


WINDOW_NAME = "Capture Tool"


def grab_primary_monitor() -> np.ndarray:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        frame = np.array(sct.grab(monitor))
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)


def build_output_path(output_dir: Path, name: str | None) -> Path:
    if name:
        filename = f"{name}.png"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"template_{timestamp}.png"
    return output_dir / filename


def main() -> None:
    parser = argparse.ArgumentParser(description="擷取畫面並框選模板圖片")
    parser.add_argument(
        "--name",
        help="輸出的模板名稱，不含副檔名。若未提供會自動用時間命名。",
    )
    parser.add_argument(
        "--output-dir",
        default="templates",
        help="模板輸出資料夾，預設為 templates",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    output_dir = (base_dir / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("3 秒後擷取主螢幕，請先把遊戲畫面切到前景...")
    for count in (3, 2, 1):
        print(count)
        cv2.waitKey(1000)

    screenshot = grab_primary_monitor()
    print("請用滑鼠框選要存成模板的區域，按 Enter 確認，按 C 取消。")

    roi = cv2.selectROI(WINDOW_NAME, screenshot, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    x, y, w, h = map(int, roi)
    if w <= 0 or h <= 0:
        print("未選取任何區域，已取消。")
        return

    crop = screenshot[y : y + h, x : x + w]
    output_path = build_output_path(output_dir, args.name)
    if not cv2.imwrite(str(output_path), crop):
        raise RuntimeError(f"無法寫入模板圖片: {output_path}")

    region_json = {
        "left": x,
        "top": y,
        "width": w,
        "height": h,
    }

    print(f"模板已儲存: {output_path}")
    print(f"區域座標: left={x}, top={y}, width={w}, height={h}")
    print("可直接貼到 config.json 的 capture_region:")
    print(json.dumps(region_json, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
