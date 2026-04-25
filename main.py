from pathlib import Path
import sys

from afkbot.engine import run_from_file
from afkbot.gui import run_gui


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    if "--cli" in sys.argv:
        run_from_file(base_dir / "config.json")
        return
    run_gui(base_dir)


if __name__ == "__main__":
    main()
