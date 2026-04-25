from dataclasses import dataclass
from pathlib import Path


GAMES_DIR_NAME = "games"
CONFIG_FILE_NAME = "config.json"


@dataclass(frozen=True)
class GameProfile:
    name: str
    path: Path
    config_path: Path


def games_dir(base_dir: Path) -> Path:
    return base_dir / GAMES_DIR_NAME


def list_game_profiles(base_dir: Path) -> list[GameProfile]:
    root = games_dir(base_dir)
    if not root.exists():
        return []

    profiles: list[GameProfile] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir():
            continue
        config_path = path / CONFIG_FILE_NAME
        if config_path.exists():
            profiles.append(
                GameProfile(
                    name=path.name,
                    path=path,
                    config_path=config_path,
                )
            )
    return profiles


def get_profile_by_name(base_dir: Path, name: str) -> GameProfile | None:
    for profile in list_game_profiles(base_dir):
        if profile.name == name:
            return profile
    return None


def get_default_profile(base_dir: Path) -> GameProfile | None:
    profiles = list_game_profiles(base_dir)
    if not profiles:
        return None
    return profiles[0]
