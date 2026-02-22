"""Entry point for the Python Point of Sale system."""

from pos.cli import run
from pos.store import create_demo_store


def main() -> None:
    store = create_demo_store()
    run(store)


if __name__ == "__main__":
    main()
