from pathlib import Path
import sys

from afkbot.engine import run_from_file
from afkbot.gui import run_gui
from afkbot.profiles import get_default_profile


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    if "--cli" in sys.argv:
        profile = get_default_profile(base_dir)
        if profile is None:
            raise SystemExit("No game config found under games/.")
        run_from_file(profile.config_path)
        return
    run_gui(base_dir)


if __name__ == "__main__":
    main()
