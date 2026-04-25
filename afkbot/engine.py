import time
from collections.abc import Callable
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


LogCallback = Callable[[str], None]
StateCallback = Callable[[bool], None]


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
    def __init__(
        self,
        config: AppConfig,
        log: LogCallback | None = None,
        on_monitoring_changed: StateCallback | None = None,
    ) -> None:
        self.config = config
        self.templates = TemplateCache()
        self.last_trigger_times: dict[str, float] = {}
        self.start_hotkey = HotkeyLatch("ALT", "1")
        self.pause_hotkey = HotkeyLatch("ALT", "0")
        self.is_monitoring = False
        self._stop_requested = False
        self._log_callback = log or print
        self._on_monitoring_changed = on_monitoring_changed

    def run(self) -> None:
        self._stop_requested = False
        try:
            with mss.mss() as sct:
                base_region = resolve_capture_region(sct, self.config.capture_region)
                self._print_startup(base_region)

                while not self._stop_requested:
                    if is_key_pressed(self.config.stop_key):
                        self.log(f"{self.config.stop_key} pressed. Stopping bot.")
                        break

                    self._update_monitor_state()
                    if not self.is_monitoring:
                        time.sleep(self.config.loop_interval_ms / 1000)
                        continue

                    self._process_scenes(sct, base_region)
                    time.sleep(self.config.loop_interval_ms / 1000)
        finally:
            self.set_monitoring(False)
            self.log("Bot engine stopped.")

    def start_monitoring(self) -> None:
        self.set_monitoring(True)

    def pause_monitoring(self) -> None:
        self.set_monitoring(False)

    def request_stop(self) -> None:
        self._stop_requested = True
        self.set_monitoring(False)

    def set_monitoring(self, enabled: bool) -> None:
        if self.is_monitoring == enabled:
            return
        self.is_monitoring = enabled
        self.log("Monitoring started." if enabled else "Monitoring paused.")
        if self._on_monitoring_changed is not None:
            self._on_monitoring_changed(enabled)

    def log(self, message: str) -> None:
        self._log_callback(message)

    def _print_startup(self, base_region: dict[str, int]) -> None:
        self.log("Bot engine ready.")
        self.log(f"Capture region: {base_region}")
        self.log("Start hotkey: ALT+1")
        self.log("Pause hotkey: ALT+0")
        self.log(f"Stop hotkey: {self.config.stop_key}")
        self.log("Waiting for start command.")

        if not self.config.scenes:
            self.log("No scenes configured. Check config.json.")

    def _update_monitor_state(self) -> None:
        if self.start_hotkey.consume_press() and not self.is_monitoring:
            self.set_monitoring(True)

        if self.pause_hotkey.consume_press() and self.is_monitoring:
            self.set_monitoring(False)

    def _process_scenes(self, sct: mss.mss, base_region: dict[str, int]) -> None:
        now = time.time()

        for scene in self.config.scenes:
            if self._stop_requested or not self.is_monitoring:
                return

            template = self.templates.get(scene)
            if template is None:
                if self.config.debug:
                    self.log(f"[SKIP] {scene.name}: missing template {scene.template_path}")
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
                self.log(
                    f"[DEBUG] {scene.name}: {score:.4f} "
                    f"mode={scene.match_mode} region={current_region}"
                )

            if score < scene.threshold:
                continue

            if self._is_in_cooldown(scene, now):
                continue

            self.log(f"[HIT] {scene.name} score={score:.4f}")
            execute_actions(scene.actions)
            self.last_trigger_times[scene.name] = time.time()

    def _is_in_cooldown(self, scene: SceneRule, now: float) -> bool:
        cooldown_sec = scene.cooldown_ms / 1000
        last_trigger = self.last_trigger_times.get(scene.name, 0.0)
        return now - last_trigger < cooldown_sec


def run_from_file(config_path: Path) -> None:
    config = load_config(config_path)
    BotEngine(config).run()
