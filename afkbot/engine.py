import time
from pathlib import Path

import mss
import numpy as np

from afkbot.actions import execute_actions
from afkbot.config import load_config
from afkbot.hotkeys import HotkeyLatch, is_key_pressed
from afkbot.models import AppConfig, SceneRule
from afkbot.vision import (
    grab_gray_frame,
    load_template,
    match_template,
    resolve_capture_region,
    to_absolute_region,
)


class TemplateCache:
    def __init__(self) -> None:
        self._templates: dict[str, np.ndarray] = {}

    def get(self, scene: SceneRule) -> np.ndarray | None:
        if scene.name in self._templates:
            return self._templates[scene.name]
        if not scene.template_path.exists():
            return None
        template = load_template(scene.template_path)
        self._templates[scene.name] = template
        return template


class BotEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.templates = TemplateCache()
        self.last_trigger_times: dict[str, float] = {}
        self.start_hotkey = HotkeyLatch("ALT", "1")
        self.pause_hotkey = HotkeyLatch("ALT", "0")
        self.is_monitoring = False

    def run(self) -> None:
        with mss.mss() as sct:
            base_region = resolve_capture_region(sct, self.config.capture_region)
            self._print_startup(base_region)

            while True:
                if is_key_pressed(self.config.stop_key):
                    print("收到停止指令，程式結束。")
                    break

                self._update_monitor_state()
                if not self.is_monitoring:
                    time.sleep(self.config.loop_interval_ms / 1000)
                    continue

                self._process_scenes(sct, base_region)
                time.sleep(self.config.loop_interval_ms / 1000)

    def _print_startup(self, base_region: dict[str, int]) -> None:
        print("半自動掛機啟動中...")
        print(f"基礎偵測區域: {base_region}")
        print("開始監控熱鍵: ALT+1")
        print("停止監控熱鍵: ALT+0")
        print(f"停止熱鍵: {self.config.stop_key}")
        print("目前狀態: 待機中")

        if not self.config.scenes:
            print("目前沒有任何偵測規則，程式只會待機與接收熱鍵。")

    def _update_monitor_state(self) -> None:
        if self.start_hotkey.consume_press() and not self.is_monitoring:
            self.is_monitoring = True
            print("監控已開始。")

        if self.pause_hotkey.consume_press() and self.is_monitoring:
            self.is_monitoring = False
            print("監控已停止，程式維持待機。")

    def _process_scenes(self, sct: mss.mss, base_region: dict[str, int]) -> None:
        now = time.time()

        for scene in self.config.scenes:
            template = self.templates.get(scene)
            if template is None:
                if self.config.debug:
                    print(f"[SKIP] {scene.name}: 找不到模板 {scene.template_path}")
                continue

            current_region = to_absolute_region(base_region, scene.search_region)
            frame_gray = grab_gray_frame(sct, current_region)
            score = match_template(
                frame_gray,
                template,
                scene.match_mode,
                scene.pixel_tolerance,
            )

            if self.config.debug:
                print(
                    f"[DEBUG] {scene.name}: {score:.4f} "
                    f"mode={scene.match_mode} region={current_region}"
                )

            if score < scene.threshold:
                continue

            if self._is_in_cooldown(scene, now):
                continue

            print(f"[HIT] {scene.name} score={score:.4f}")
            execute_actions(scene.actions)
            self.last_trigger_times[scene.name] = time.time()

    def _is_in_cooldown(self, scene: SceneRule, now: float) -> bool:
        cooldown_sec = scene.cooldown_ms / 1000
        last_trigger = self.last_trigger_times.get(scene.name, 0.0)
        return now - last_trigger < cooldown_sec


def run_from_file(config_path: Path) -> None:
    config = load_config(config_path)
    BotEngine(config).run()
