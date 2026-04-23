import json
from pathlib import Path

from afkbot.models import AppConfig, SceneRule


def load_config(config_path: Path) -> AppConfig:
    if not config_path.exists():
        raise FileNotFoundError(
            f"找不到 {config_path.name}，請先從 config.example.json 複製成 config.json"
        )

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = json.load(file)

    base_dir = config_path.parent
    scenes = [
        SceneRule(
            name=raw_scene["name"],
            template_path=base_dir / raw_scene["template"],
            threshold=float(raw_scene["threshold"]),
            cooldown_ms=int(raw_scene.get("cooldown_ms", 1000)),
            actions=list(raw_scene.get("actions", [])),
            search_region=raw_scene.get("search_region"),
            match_mode=str(raw_scene.get("match_mode", "template")),
            pixel_tolerance=int(raw_scene.get("pixel_tolerance", 10)),
        )
        for raw_scene in raw_config.get("scenes", [])
    ]

    return AppConfig(
        capture_region=raw_config.get("capture_region"),
        loop_interval_ms=int(raw_config.get("loop_interval_ms", 250)),
        stop_key=str(raw_config.get("stop_key", "F8")),
        debug=bool(raw_config.get("debug", False)),
        scenes=scenes,
    )
