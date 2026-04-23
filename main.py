import ctypes
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import mss
import numpy as np
import pydirectinput


VK_CODE_MAP = {
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F12": 0x7B,
}


@dataclass
class SceneRule:
    name: str
    template_path: Path
    threshold: float
    cooldown_ms: int
    actions: list[dict[str, Any]]


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(
            f"找不到 {config_path.name}，請先從 config.example.json 複製成 config.json"
        )

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_scenes(config: dict[str, Any], base_dir: Path) -> list[SceneRule]:
    scenes: list[SceneRule] = []
    for raw_scene in config.get("scenes", []):
        scenes.append(
            SceneRule(
                name=raw_scene["name"],
                template_path=base_dir / raw_scene["template"],
                threshold=float(raw_scene["threshold"]),
                cooldown_ms=int(raw_scene.get("cooldown_ms", 1000)),
                actions=list(raw_scene.get("actions", [])),
            )
        )
    return scenes


def load_template(template_path: Path) -> np.ndarray:
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"讀不到模板圖片: {template_path}")
    return template


def is_stop_key_pressed(key_name: str) -> bool:
    vk_code = VK_CODE_MAP.get(key_name.upper())
    if vk_code is None:
        raise ValueError(f"目前只支援這些停止鍵: {', '.join(sorted(VK_CODE_MAP))}")
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)


def grab_gray_frame(sct: mss.mss, region: dict[str, int]) -> np.ndarray:
    frame = np.array(sct.grab(region))
    bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def match_template(frame_gray: np.ndarray, template_gray: np.ndarray) -> float:
    result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return float(max_val)


def execute_actions(actions: list[dict[str, Any]]) -> None:
    for action in actions:
        action_type = action["type"]
        if action_type == "press":
            pydirectinput.press(action["key"])
        elif action_type == "keyDown":
            pydirectinput.keyDown(action["key"])
        elif action_type == "keyUp":
            pydirectinput.keyUp(action["key"])
        elif action_type == "sleep":
            time.sleep(int(action["ms"]) / 1000)
        else:
            raise ValueError(f"不支援的 action type: {action_type}")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir / "config.json")
    scenes = load_scenes(config, base_dir)
    templates = {scene.name: load_template(scene.template_path) for scene in scenes}
    last_trigger_times: dict[str, float] = {}

    region = config["capture_region"]
    loop_interval = int(config.get("loop_interval_ms", 250)) / 1000
    stop_key = str(config.get("stop_key", "F8"))
    debug = bool(config.get("debug", False))

    print("半自動掛機啟動中...")
    print(f"偵測區域: {region}")
    print(f"停止熱鍵: {stop_key}")

    with mss.mss() as sct:
        while True:
            if is_stop_key_pressed(stop_key):
                print("收到停止指令，程式結束。")
                break

            frame_gray = grab_gray_frame(sct, region)
            now = time.time()

            for scene in scenes:
                score = match_template(frame_gray, templates[scene.name])
                if debug:
                    print(f"[DEBUG] {scene.name}: {score:.4f}")

                if score < scene.threshold:
                    continue

                cooldown_sec = scene.cooldown_ms / 1000
                last_trigger = last_trigger_times.get(scene.name, 0.0)
                if now - last_trigger < cooldown_sec:
                    continue

                print(f"[HIT] {scene.name} score={score:.4f}")
                execute_actions(scene.actions)
                last_trigger_times[scene.name] = time.time()

            time.sleep(loop_interval)


if __name__ == "__main__":
    main()
