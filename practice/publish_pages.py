#!/usr/bin/env python3
"""Copy the static practice site into a GitHub Pages docs/ folder."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "static"
DEFAULT_DEST = Path("/home/harik/Spectrum-generator/docs")
SKIP = {".DS_Store", "media", "ms_keys.json"}


def publish(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for p in SRC.iterdir():
        if p.name in SKIP:
            continue
        target = dest / p.name
        if p.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(p, target)
        else:
            shutil.copy2(p, target)
    (dest / ".nojekyll").write_text("", encoding="utf-8")
    print("published", SRC, "->", dest)


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DEST
    publish(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
