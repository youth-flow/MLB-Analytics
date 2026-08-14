"""Run the reproducible MLB analytics pipeline.

Offline mode is the default and consumes the committed frozen raw snapshots.
Use ``--refresh-data`` only when intentionally replacing those snapshots with
new network responses and updating their provenance manifest.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def command(script_name: str, *extra_args: str) -> list[str]:
    return [sys.executable, str(ROOT / "scripts" / script_name), *extra_args]


def run_step(script_name: str, *extra_args: str) -> None:
    argv = command(script_name, *extra_args)
    print(f"[pipeline] {' '.join(argv)}", flush=True)
    subprocess.run(argv, cwd=ROOT, check=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-data",
        action="store_true",
        help="download live sources before analysis; omitted by default for frozen offline reproduction",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    steps: list[tuple[str, ...]] = [("analyze.py",), ("build_reports.py",), ("verify_project.py",)]
    if args.refresh_data:
        steps.insert(0, ("fetch_data.py", "--refresh-data"))
    mode = "refresh" if args.refresh_data else "offline"
    print(f"[pipeline] mode={mode}", flush=True)
    try:
        for script_name, *extra_args in steps:
            run_step(script_name, *extra_args)
    except subprocess.CalledProcessError as exc:
        print(f"[pipeline] failed at {Path(exc.cmd[-1]).name} with exit code {exc.returncode}", file=sys.stderr)
        return int(exc.returncode or 1)
    print("[pipeline] completed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
