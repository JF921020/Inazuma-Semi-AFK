from dataclasses import dataclass
from pathlib import Path
from typing import Any


Region = dict[str, int]
Action = dict[str, Any]


@dataclass
class SceneRule:
    name: str
    template_path: Path
    threshold: float
    cooldown_ms: int
    actions: list[Action]
    search_region: Region | None
    match_mode: str
    pixel_tolerance: int


@dataclass
class AppConfig:
    capture_region: Region | None
    loop_interval_ms: int
    stop_key: str
    debug: bool
    scenes: list[SceneRule]
