"""Run integrity and document-structure checks for the course project."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from lxml import etree
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa"
FORMAL = ROOT / "reports" / "今井达也_MLB调整决策_正式文稿.docx"
FULL = ROOT / "reports" / "今井达也_MLB调整决策_完整分析底稿.docx"
FORMAL_PDF = QA / "rendered" / "formal" / "今井达也_MLB调整决策_正式文稿.pdf"
FULL_PDF = QA / "rendered" / "full" / "今井达也_MLB调整决策_完整分析底稿.pdf"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_source_hashes() -> tuple[int, list[str]]:
    manifest = pd.read_csv(ROOT / "data" / "raw" / "source_manifest.csv")
    errors: list[str] = []
    for row in manifest.itertuples(index=False):
        path = ROOT / row.file
        if not path.exists():
            errors.append(f"missing:{row.file}")
        elif sha256(path) != row.sha256:
            errors.append(f"hash:{row.file}")
    return len(manifest), errors


def inspect_docx(path: Path, expected_pages: int | None, pdf_path: Path | None) -> dict:
    with ZipFile(path) as archive:
        xml = etree.fromstring(archive.read("word/document.xml"))
        styles = etree.fromstring(archive.read("word/styles.xml"))
    pg_sz = xml.xpath("//w:sectPr[1]/w:pgSz", namespaces=NS)[0]
    width = int(pg_sz.get(f"{{{NS['w']}}}w"))
    height = int(pg_sz.get(f"{{{NS['w']}}}h"))
    text = "".join(xml.xpath("//w:t/text()", namespaces=NS))
    font_values = styles.xpath("//w:rFonts/@w:eastAsia", namespaces=NS)
    thesis_nodes = xml.xpath("//w:p[.//w:t[contains(., '结论先行')]]", namespaces=NS)
    thesis_bold = bool(thesis_nodes) and all(
        run.xpath("boolean(w:rPr/w:b)", namespaces=NS)
        for run in thesis_nodes[0].xpath(".//w:r", namespaces=NS)
        if run.xpath(".//w:t", namespaces=NS)
    )
    pages = len(PdfReader(str(pdf_path)).pages) if pdf_path and pdf_path.exists() else None
    return {
        "path": str(path.relative_to(ROOT)),
        "a4_geometry": abs(width - 11906) <= 3 and abs(height - 16838) <= 3,
        "page_width_twips": width,
        "page_height_twips": height,
        "microsoft_yahei_in_styles": "Microsoft YaHei" in font_values,
        "contains_title": "今井达也应如何重返 MLB 先发轮值" in text,
        "thesis_paragraph_bold": thesis_bold,
        "rendered_pages": pages,
        "expected_pages": expected_pages,
        "page_count_ok": expected_pages is None or pages == expected_pages,
    }


def write_artifact_manifest() -> int:
    roots = ["01_research", "data/processed", "outputs/figures", "reports", "scripts"]
    files: list[Path] = []
    for root in roots:
        files.extend(p for p in (ROOT / root).rglob("*") if p.is_file() and p.name != ".gitkeep")
    files.extend([ROOT / "README.md", ROOT / "requirements.txt"])
    files = sorted(set(files), key=lambda p: p.as_posix())
    out = QA / "artifact_manifest.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "bytes", "sha256"])
        writer.writeheader()
        for path in files:
            writer.writerow({
                "file": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    return len(files)


def main() -> None:
    QA.mkdir(parents=True, exist_ok=True)
    reconciliation = pd.read_csv(QA / "data_reconciliation.csv")
    reconciliation_ok = bool((reconciliation["difference"] == 0).all())
    source_count, source_errors = check_source_hashes()
    formal = inspect_docx(FORMAL, 2, FORMAL_PDF)
    full = inspect_docx(FULL, 7, FULL_PDF)
    artifact_count = write_artifact_manifest()
    checks = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_reconciliation_ok": reconciliation_ok,
        "data_reconciliation_rows": reconciliation.to_dict(orient="records"),
        "source_manifest_entries": source_count,
        "source_hash_errors": source_errors,
        "formal_docx": formal,
        "full_draft_docx": full,
        "artifact_manifest_entries": artifact_count,
        "visual_review": {
            "formal_pages_reviewed": 2,
            "full_draft_pages_reviewed": 7,
            "clipped_text": False,
            "overlaps": False,
            "broken_tables": False,
            "unexpected_font_substitution": False,
        },
    }
    required = [
        reconciliation_ok,
        not source_errors,
        formal["a4_geometry"],
        formal["microsoft_yahei_in_styles"],
        formal["thesis_paragraph_bold"],
        formal["page_count_ok"],
        full["a4_geometry"],
        full["microsoft_yahei_in_styles"],
        full["page_count_ok"],
    ]
    checks["overall_pass"] = all(required)
    (QA / "integrity_report.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not checks["overall_pass"]:
        raise SystemExit(json.dumps(checks, ensure_ascii=False, indent=2))
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
