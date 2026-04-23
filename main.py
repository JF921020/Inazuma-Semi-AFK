from pathlib import Path

from afkbot.engine import run_from_file


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    run_from_file(base_dir / "config.json")


if __name__ == "__main__":
    main()
