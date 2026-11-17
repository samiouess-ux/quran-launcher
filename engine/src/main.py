"""Project entry point: delegates to the safe daily orchestrator."""
from __future__ import annotations

from orchestrator import main as orchestrator_main


def main() -> int:
    return orchestrator_main()


if __name__ == "__main__":
    raise SystemExit(main())
