from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


WORKSPACE = Path(r"C:\Users\yyx\Desktop\大三暑期短学期")
REVISION_ROOT = WORKSPACE / ".submission_revision_work"
TASK_ROOT = REVISION_ROOT / "fullmark_20260821"
STAGING_ROOT = TASK_ROOT / "staging"
SOURCE_ROOT = REVISION_ROOT / "sources"
WEEKLY_REFERENCE = (
    REVISION_ROOT
    / "archive"
    / "weekly_before_fullmark_polish_20260820"
    / "第1周实习记录_润色前.docx"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    weekly = load_module(
        "weekly_fullmark_builder",
        REVISION_ROOT / "weekly_fullmark_20260820" / "build_weeklies.py",
    )
    submission = load_module(
        "submission_builder",
        REVISION_ROOT / "build_submission.py",
    )

    results: list[dict[str, str]] = []
    for week in (3, 4):
        source = SOURCE_ROOT / f"0{week}_week{week}.md"
        output = STAGING_ROOT / f"第{week}周实习记录.docx"
        weekly.build_one(WEEKLY_REFERENCE, source, output)
        results.append({"file": output.name, "sha256": sha256(output)})

    submission.OUTPUT_ROOT = STAGING_ROOT
    for source_name in (
        "05_internship_report.md",
        "06_jiang_summary.md",
        "07_full_analysis.md",
        "08_sources_metrics.md",
        "09_analysis_iterations.md",
        "10_reproducibility.md",
    ):
        output = submission.build_document(SOURCE_ROOT / source_name)
        results.append({"file": output.name, "sha256": sha256(output)})

    if len(results) != 8 or len(list(STAGING_ROOT.glob("*.docx"))) != 8:
        raise AssertionError("Expected exactly eight staged DOCX outputs")
    (TASK_ROOT / "build_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
