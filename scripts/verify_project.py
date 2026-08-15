"""Automatic integrity checks for the frozen MLB analytics project.

The automatic checks deliberately stop at properties that code can verify:
source bytes, reconciled totals, frozen headline metrics, public-file privacy,
and DOCX structure.  Rendering and human visual review are reported as
separate evidence states; their absence never masquerades as a successful
visual inspection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Iterable
from zipfile import BadZipFile, ZipFile

from lxml import etree
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa"
FORMAL = ROOT / "reports" / "public" / "今井达也_MLB调整决策_正式文稿.docx"
FULL = ROOT / "reports" / "public" / "今井达也_MLB调整决策_完整分析底稿.docx"
FORMAL_PDF = QA / "rendered" / "formal" / "今井达也_MLB调整决策_正式文稿.pdf"
FULL_PDF = QA / "rendered" / "full" / "今井达也_MLB调整决策_完整分析底稿.pdf"
VISUAL_RECEIPT = QA / "visual_review_receipt.json"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
EXPECTED_TITLE = "今井达也应如何重返MLB先发轮值"
EXPECTED_SOURCE_COUNT = 17
EXPECTED_RECONCILIATION = {
    "Statcast pitch rows": 1240,
    "Strikeouts": 80,
    "Walks": 42,
    "Games": 17,
}
EXPECTED_CORE_METRICS = {
    "games": 17,
    "starts": 15,
    "relief_appearances": 2,
    "innings": 64.66666666666667,
    "k_pct": 27.77777777777778,
    "bb_pct": 14.583333333333334,
    "npb_2025_changeup_usage_pct": 12.67,
    "mlb_changeup_usage_pct": 2.338709677419355,
    "four_seam_lhb_rv100": -1.2720257234726688,
    "four_seam_rhb_rv100": 1.465065502183406,
    "relief_plate_appearances": 23,
}

ARTIFACT_DIRS = (
    "config",
    "docs",
    "data/processed",
    "outputs/figures",
    "reports/sources",
    "reports/public",
    "scripts",
    "tests",
    ".github/workflows",
)
ARTIFACT_FILES = (
    "README.md",
    "data/README.md",
    "requirements.txt",
    "pyproject.toml",
    ".python-version",
    ".gitignore",
    ".gitattributes",
    "qa/data_reconciliation.csv",
)
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "rendered"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
CANONICAL_TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".txt", ".toml", ".yml", ".yaml"}
CANONICAL_TEXT_NAMES = {".gitattributes", ".gitignore", ".python-version"}

PUBLIC_SCAN_DIRS = ("config", "docs", "reports/sources", "reports/public", "scripts", "tests", ".github")
PUBLIC_SCAN_FILES = ("README.md", "data/README.md", "pyproject.toml")
TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yml", ".yaml", ".toml"}
PII_PATTERNS = {
    "email": re.compile(r"(?i)(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])"),
    "mainland_phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "ten_digit_student_id": re.compile(r"(?<![\dA-Fa-f])\d{10}(?![\dA-Fa-f])"),
    "windows_user_path": re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+"),
}


def sha256(path: Path) -> str:
    """Return the SHA-256 of exact file bytes."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_zip_sha256(path: Path) -> str:
    """Hash ZIP member names and contents while ignoring container timestamps."""

    digest = hashlib.sha256(b"zip-content-sha256-v1\0")
    with ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            payload = archive.read(name)
            encoded_name = name.encode("utf-8")
            digest.update(len(encoded_name).to_bytes(8, "big"))
            digest.update(encoded_name)
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
    return digest.hexdigest()


def artifact_digest(path: Path) -> tuple[str, str, int]:
    if path.suffix.lower() == ".docx":
        return "zip-content-sha256-v1", stable_zip_sha256(path), path.stat().st_size
    if path.suffix.lower() in CANONICAL_TEXT_SUFFIXES or path.name in CANONICAL_TEXT_NAMES:
        payload = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return "text-lf-sha256-v1", hashlib.sha256(payload).hexdigest(), len(payload)
    return "file-sha256-v1", sha256(path), path.stat().st_size


def _safe_manifest_path(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def check_source_manifest(root: Path = ROOT) -> dict:
    """Validate the CSV/JSON source manifest and every frozen source byte."""

    csv_path = root / "data" / "raw" / "source_manifest.csv"
    json_path = root / "data" / "raw" / "source_manifest.json"
    errors: list[str] = []
    if not csv_path.exists():
        return {"status": "failed", "entries": 0, "errors": ["missing:source_manifest.csv"]}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    seen: set[str] = set()
    csv_receipts: set[tuple[str, str, int]] = set()
    for row in rows:
        relative = str(row.get("file", "")).replace("\\", "/")
        expected_hash = str(row.get("sha256", "")).lower()
        try:
            expected_bytes = int(row.get("bytes", ""))
        except (TypeError, ValueError):
            expected_bytes = -1
        if not relative or relative in seen:
            errors.append(f"duplicate_or_empty:{relative or '<empty>'}")
            continue
        seen.add(relative)
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            errors.append(f"invalid_sha256:{relative}")
            continue
        path = _safe_manifest_path(root, relative)
        if path is None:
            errors.append(f"unsafe_path:{relative}")
        elif not path.is_file():
            errors.append(f"missing:{relative}")
        else:
            if path.stat().st_size != expected_bytes:
                errors.append(f"bytes:{relative}")
            if sha256(path) != expected_hash:
                errors.append(f"hash:{relative}")
        csv_receipts.add((relative, expected_hash, expected_bytes))

    if len(rows) != EXPECTED_SOURCE_COUNT:
        errors.append(f"entry_count:{len(rows)}!=expected:{EXPECTED_SOURCE_COUNT}")

    if not json_path.exists():
        errors.append("missing:source_manifest.json")
    else:
        try:
            json_rows = json.loads(json_path.read_text(encoding="utf-8"))
            json_receipts = {
                (str(row["file"]).replace("\\", "/"), str(row["sha256"]).lower(), int(row["bytes"]))
                for row in json_rows
            }
            if json_receipts != csv_receipts:
                errors.append("csv_json_manifest_mismatch")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid:source_manifest.json:{type(exc).__name__}")

    return {
        "status": "passed" if not errors else "failed",
        "entries": len(rows),
        "errors": errors,
    }


def check_source_hashes(root: Path = ROOT) -> tuple[int, list[str]]:
    """Backward-compatible summary used by tests and earlier notebooks."""

    result = check_source_manifest(root)
    return int(result["entries"]), list(result["errors"])


def check_data_reconciliation(root: Path = ROOT) -> dict:
    path = root / "qa" / "data_reconciliation.csv"
    if not path.exists():
        return {"status": "failed", "rows": [], "errors": ["missing:qa/data_reconciliation.csv"]}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    errors: list[str] = []
    observed: dict[str, float] = {}
    normalized_rows: list[dict[str, int | float | str]] = []
    for row in rows:
        name = str(row.get("check", ""))
        try:
            computed = float(row["computed"])
            reference = float(row["reference"])
            difference = float(row["difference"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"invalid_row:{name or '<empty>'}")
            continue
        observed[name] = computed
        if not math.isclose(computed, reference, abs_tol=1e-12) or not math.isclose(difference, 0.0, abs_tol=1e-12):
            errors.append(f"not_reconciled:{name}")
        normalized_rows.append(
            {
                "check": name,
                "computed": int(computed) if computed.is_integer() else computed,
                "reference": int(reference) if reference.is_integer() else reference,
                "difference": int(difference) if difference.is_integer() else difference,
            }
        )

    for name, expected in EXPECTED_RECONCILIATION.items():
        if name not in observed:
            errors.append(f"missing_check:{name}")
        elif not math.isclose(observed[name], float(expected), abs_tol=1e-12):
            errors.append(f"unexpected_value:{name}")

    return {
        "status": "passed" if not errors else "failed",
        "rows": normalized_rows,
        "errors": errors,
    }


def check_core_metrics(root: Path = ROOT) -> dict:
    path = root / "data" / "processed" / "analysis_summary.json"
    if not path.exists():
        return {"status": "failed", "errors": ["missing:data/processed/analysis_summary.json"]}
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "failed", "errors": [f"invalid:analysis_summary.json:{exc.msg}"]}

    errors: list[str] = []
    observed: dict[str, int | float | None] = {}
    for key, expected in EXPECTED_CORE_METRICS.items():
        value = summary.get(key)
        observed[key] = value
        if not isinstance(value, (int, float)) or not math.isclose(
            float(value), float(expected), rel_tol=1e-9, abs_tol=1e-9
        ):
            errors.append(f"unexpected_value:{key}")
    return {
        "status": "passed" if not errors else "failed",
        "observed": observed,
        "errors": errors,
    }


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", "", value).replace("？", "").replace("?", "")


def inspect_docx(
    path: Path,
    expected_images: int = 0,
    *,
    expected_normal_font: str | None = None,
    expected_normal_size_half_points: int | None = None,
    enforce_formal_course_format: bool = False,
) -> dict:
    """Inspect geometry, typography, figures, and a restrained style policy."""

    base = {
        "path": path.relative_to(ROOT).as_posix() if path.is_absolute() and ROOT in path.parents else path.as_posix(),
        "present": path.is_file(),
    }
    if not path.is_file():
        return {**base, "status": "failed", "errors": ["missing_docx"]}

    try:
        with ZipFile(path) as archive:
            document_xml = etree.fromstring(archive.read("word/document.xml"))
            styles_xml = etree.fromstring(archive.read("word/styles.xml"))
            media_files = [name for name in archive.namelist() if name.startswith("word/media/")]
    except (BadZipFile, KeyError, etree.XMLSyntaxError) as exc:
        return {**base, "status": "failed", "errors": [f"invalid_docx:{type(exc).__name__}"]}

    page_sizes = document_xml.xpath("//w:sectPr/w:pgSz", namespaces=NS)
    geometry = [
        (
            int(node.get(f"{{{NS['w']}}}w", "0")),
            int(node.get(f"{{{NS['w']}}}h", "0")),
        )
        for node in page_sizes
    ]
    a4_geometry = bool(geometry) and all(abs(width - 11906) <= 3 and abs(height - 16838) <= 3 for width, height in geometry)
    text = "".join(document_xml.xpath("//w:t/text()", namespaces=NS))
    contains_title = EXPECTED_TITLE in _compact_text(text)

    normal_fonts = styles_xml.xpath(
        "//w:style[@w:styleId='Normal']/w:rPr/w:rFonts/@w:eastAsia",
        namespaces=NS,
    )
    if not normal_fonts:
        normal_fonts = styles_xml.xpath("//w:docDefaults//w:rFonts/@w:eastAsia", namespaces=NS)
    normal_sizes = styles_xml.xpath(
        "//w:style[@w:styleId='Normal']/w:rPr/w:sz/@w:val",
        namespaces=NS,
    )
    caption_fonts = styles_xml.xpath(
        "//w:style[@w:styleId='Caption']/w:rPr/w:rFonts/@w:eastAsia",
        namespaces=NS,
    )
    caption_sizes = styles_xml.xpath(
        "//w:style[@w:styleId='Caption']/w:rPr/w:sz/@w:val",
        namespaces=NS,
    )

    direct_colors = {
        value.upper()
        for value in document_xml.xpath("//w:color/@w:val", namespaces=NS)
        if str(value).lower() not in {"auto", "000000"}
    }
    shading_fills = {
        value.upper()
        for value in document_xml.xpath("//w:shd/@w:fill", namespaces=NS)
        if str(value).lower() not in {"auto", "clear", "nil", "ffffff"}
    }
    page_backgrounds = len(document_xml.xpath("//*[local-name()='background']"))
    page_borders = len(document_xml.xpath("//w:sectPr/w:pgBorders", namespaces=NS))
    legacy_shapes = len(document_xml.xpath("//*[local-name()='pict' or local-name()='shape']"))
    plain_style = (
        page_backgrounds == 0
        and page_borders == 0
        and legacy_shapes == 0
        and len(direct_colors) <= 3
        and len(shading_fills) <= 2
    )

    thesis_nodes = document_xml.xpath("//w:p[.//w:t[contains(., '结论先行')]]", namespaces=NS)
    thesis_bold = bool(thesis_nodes) and all(
        run.xpath("boolean(w:rPr/w:b)", namespaces=NS)
        for run in thesis_nodes[0].xpath(".//w:r", namespaces=NS)
        if run.xpath(".//w:t", namespaces=NS)
    )

    formal_body_runs = document_xml.xpath(
        "//w:body/w:p[(not(w:pPr/w:pStyle) or w:pPr/w:pStyle/@w:val='Normal')]"
        "/w:r[.//w:t]",
        namespaces=NS,
    )
    formal_table_runs = document_xml.xpath("//w:tbl//w:r[.//w:t]", namespaces=NS)

    def run_matches_course_format(run) -> bool:
        fonts = run.xpath("w:rPr/w:rFonts/@w:eastAsia", namespaces=NS)
        sizes = run.xpath("w:rPr/w:sz/@w:val", namespaces=NS)
        return fonts == ["Microsoft YaHei"] and sizes == ["18"]

    formal_body_format_ok = bool(formal_body_runs) and all(
        run_matches_course_format(run) for run in formal_body_runs
    )
    formal_table_format_ok = bool(formal_table_runs) and all(
        run_matches_course_format(run) for run in formal_table_runs
    )
    formal_caption_format_ok = caption_fonts == ["Microsoft YaHei"] and caption_sizes == ["18"]
    errors: list[str] = []
    if not a4_geometry:
        errors.append("not_a4_portrait")
    if not contains_title:
        errors.append("missing_expected_title")
    if not normal_fonts:
        errors.append("missing_normal_style_chinese_font")
    if expected_normal_font and normal_fonts != [expected_normal_font]:
        errors.append(f"normal_font:{normal_fonts!r}!=expected:{expected_normal_font}")
    if expected_normal_size_half_points is not None and normal_sizes != [str(expected_normal_size_half_points)]:
        errors.append(
            f"normal_size:{normal_sizes!r}!=expected_half_points:{expected_normal_size_half_points}"
        )
    if not plain_style:
        errors.append("plain_style_policy_failed")
    if len(media_files) < expected_images:
        errors.append(f"embedded_images:{len(media_files)}<expected:{expected_images}")
    if enforce_formal_course_format:
        if not thesis_bold:
            errors.append("conclusion_first_paragraph_not_bold")
        if not formal_body_format_ok:
            errors.append("formal_body_runs_not_9pt_microsoft_yahei")
        if not formal_table_format_ok:
            errors.append("formal_table_runs_not_9pt_microsoft_yahei_or_missing_table")
        if not formal_caption_format_ok:
            errors.append("formal_caption_style_not_9pt_microsoft_yahei")

    return {
        **base,
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "a4_geometry": a4_geometry,
        "page_sizes_twips": [{"width": width, "height": height} for width, height in geometry],
        "contains_title": contains_title,
        "normal_style_chinese_fonts": sorted(set(normal_fonts)),
        "normal_style_sizes_half_points": sorted(set(normal_sizes)),
        "plain_style": plain_style,
        "plain_style_evidence": {
            "direct_nonblack_text_colors": sorted(direct_colors),
            "nonwhite_shading_fills": sorted(shading_fills),
            "page_backgrounds": page_backgrounds,
            "page_borders": page_borders,
            "legacy_shapes": legacy_shapes,
        },
        "embedded_images": len(media_files),
        "expected_images_at_least": expected_images,
        "thesis_paragraph_bold": thesis_bold,
        "course_format": {
            "required": enforce_formal_course_format,
            "body_runs_checked": len(formal_body_runs),
            "body_runs_9pt_microsoft_yahei": formal_body_format_ok,
            "table_runs_checked": len(formal_table_runs),
            "table_runs_9pt_microsoft_yahei": formal_table_format_ok,
            "caption_style_9pt_microsoft_yahei": formal_caption_format_ok,
        },
    }


def _iter_public_files(root: Path) -> Iterable[Path]:
    for relative in PUBLIC_SCAN_DIRS:
        directory = root / relative
        if directory.exists():
            yield from (path for path in directory.rglob("*") if path.is_file())
    for relative in PUBLIC_SCAN_FILES:
        path = root / relative
        if path.is_file():
            yield path


def _extract_scannable_text(path: Path) -> str | None:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".docx":
        try:
            with ZipFile(path) as archive:
                members = [
                    name
                    for name in archive.namelist()
                    if name == "word/document.xml" or name == "docProps/core.xml"
                ]
                return "\n".join(archive.read(name).decode("utf-8", errors="replace") for name in members)
        except (BadZipFile, KeyError):
            return None
    return None


def scan_public_pii(root: Path = ROOT) -> dict:
    findings: list[dict[str, str | int]] = []
    scanned = 0
    for path in sorted(set(_iter_public_files(root)), key=lambda item: item.as_posix()):
        if any(part in EXCLUDED_PARTS for part in path.parts) or path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        text = _extract_scannable_text(path)
        if text is None:
            continue
        scanned += 1
        for kind, pattern in PII_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                findings.append(
                    {
                        "file": path.relative_to(root).as_posix(),
                        "kind": kind,
                        "occurrences": len(matches),
                    }
                )
    return {
        "status": "passed" if not findings else "failed",
        "files_scanned": scanned,
        "findings": findings,
    }


def _artifact_is_excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if path.name == ".gitkeep" or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return any(part in EXCLUDED_PARTS for part in relative.parts)


def collect_artifacts(root: Path = ROOT) -> list[Path]:
    files: set[Path] = set()
    for relative in ARTIFACT_DIRS:
        directory = root / relative
        if directory.exists():
            files.update(
                path
                for path in directory.rglob("*")
                if path.is_file() and not _artifact_is_excluded(path, root)
            )
    for relative in ARTIFACT_FILES:
        path = root / relative
        if path.is_file() and not _artifact_is_excluded(path, root):
            files.add(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_artifact_manifest_bytes(root: Path = ROOT) -> tuple[bytes, list[dict[str, str | int]]]:
    rows: list[dict[str, str | int]] = []
    for path in collect_artifacts(root):
        digest_kind, digest, canonical_bytes = artifact_digest(path)
        rows.append(
            {
                "file": path.relative_to(root).as_posix(),
                "bytes": canonical_bytes,
                "digest_kind": digest_kind,
                "sha256": digest,
            }
        )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=["file", "bytes", "digest_kind", "sha256"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8"), rows


def write_artifact_manifest(root: Path = ROOT, output: Path | None = None) -> dict:
    output = output or (root / "qa" / "artifact_manifest.csv")
    payload, rows = build_artifact_manifest_bytes(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists() or output.read_bytes() != payload:
        output.write_bytes(payload)
    excluded_leaks = [
        row["file"]
        for row in rows
        if "__pycache__" in Path(str(row["file"])).parts
        or str(row["file"]).startswith("qa/rendered/")
        or str(row["file"]).endswith((".pyc", ".pyo"))
    ]
    return {
        "status": "passed" if not excluded_leaks else "failed",
        "entries": len(rows),
        "manifest_sha256": hashlib.sha256(payload).hexdigest(),
        "excluded_path_leaks": excluded_leaks,
        "deterministic_order": [row["file"] for row in rows] == sorted(str(row["file"]) for row in rows),
    }


def inspect_rendered_pdfs(root: Path = ROOT) -> dict:
    specs = (
        (root / "qa" / "rendered" / "formal" / FORMAL_PDF.name, 1, 2, "formal"),
        (root / "qa" / "rendered" / "full" / FULL_PDF.name, 1, None, "full_draft"),
    )
    documents: dict[str, dict[str, int | str | bool | None]] = {}
    present = 0
    failed = False
    for path, minimum_pages, maximum_pages, label in specs:
        page_rule = (
            f"{minimum_pages}-{maximum_pages}"
            if maximum_pages is not None
            else f">={minimum_pages}"
        )
        if not path.exists():
            documents[label] = {
                "status": "not_run",
                "rendered_pages": None,
                "page_rule": page_rule,
                "page_count_ok": None,
            }
            continue
        present += 1
        try:
            pages = len(PdfReader(str(path)).pages)
            ok = pages >= minimum_pages and (maximum_pages is None or pages <= maximum_pages)
            failed = failed or not ok
            documents[label] = {
                "status": "passed" if ok else "failed",
                "rendered_pages": pages,
                "page_rule": page_rule,
                "page_count_ok": ok,
            }
        except Exception as exc:  # corrupt or unreadable optional render evidence
            failed = True
            documents[label] = {
                "status": "failed",
                "rendered_pages": None,
                "page_rule": page_rule,
                "page_count_ok": False,
                "error": type(exc).__name__,
            }
    if present == 0:
        status = "not_run"
    elif present < len(specs):
        status = "partial"
    else:
        status = "failed" if failed else "passed"
    return {"status": status, "documents": documents}


def read_manual_visual_receipt(root: Path = ROOT) -> dict:
    path = root / "qa" / VISUAL_RECEIPT.name
    if not path.exists():
        return {
            "status": "not_run",
            "note": "No human visual-review receipt is present in this checkout.",
        }
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "invalid", "error": f"JSONDecodeError:{exc.msg}"}
    if receipt.get("status") != "reviewed":
        return {"status": "invalid", "error": "receipt status must be 'reviewed'"}
    return {
        "status": "reviewed",
        "reviewed_at": receipt.get("reviewed_at"),
        "reviewer": receipt.get("reviewer"),
        "documents": receipt.get("documents", []),
        "note": "Explicit reviewer receipt; not inferred by verify_project.py.",
    }


def run_checks(root: Path = ROOT, *, include_visual: bool = False) -> dict:
    analysis_config = json.loads((root / "config" / "analysis.json").read_text(encoding="utf-8"))
    source_manifest = check_source_manifest(root)
    reconciliation = check_data_reconciliation(root)
    core_metrics = check_core_metrics(root)
    formal_path = root / "reports" / "public" / FORMAL.name
    full_path = root / "reports" / "public" / FULL.name
    formal = inspect_docx(
        formal_path,
        expected_images=1,
        expected_normal_font="Microsoft YaHei",
        expected_normal_size_half_points=18,
        enforce_formal_course_format=True,
    )
    full = inspect_docx(
        full_path,
        expected_images=2,
        expected_normal_font="宋体",
        expected_normal_size_half_points=24,
    )
    pii = scan_public_pii(root)
    artifacts = write_artifact_manifest(root)

    automatic = {
        "source_manifest": source_manifest,
        "data_reconciliation": reconciliation,
        "core_metrics": core_metrics,
        "formal_docx": formal,
        "full_draft_docx": full,
        "public_pii_scan": pii,
        "artifact_manifest": artifacts,
    }
    automatic_pass = all(check.get("status") == "passed" for check in automatic.values())
    if include_visual:
        rendered = inspect_rendered_pdfs(root)
        manual = read_manual_visual_receipt(root)
    else:
        rendered = {
            "status": "not_run",
            "documents": {},
            "note": "Default automatic verification does not inspect local render caches.",
        }
        manual = {
            "status": "not_run",
            "note": "Run with --require-visual to evaluate local render evidence and a human receipt.",
        }
    submission_ready = automatic_pass and rendered["status"] == "passed" and manual["status"] == "reviewed"
    return {
        "report_schema_version": 2,
        "verification_scope": {
            "mode": "offline_frozen",
            "data_cutoff": analysis_config["analysis_window"]["mlb_end_date"],
        },
        "automatic_verification": {**automatic, "overall_pass": automatic_pass},
        "render_verification": rendered,
        "manual_visual_qa": manual,
        "overall_pass": automatic_pass,
        "submission_ready": submission_ready,
        "evidence_policy": {
            "clean_clone_can_pass_without_rendering": True,
            "rendering_is_automatic_page_count_evidence_only": True,
            "manual_visual_claims_are_never_inferred": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-visual",
        action="store_true",
        help="also require rendered page counts and a human visual-review receipt",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    QA.mkdir(parents=True, exist_ok=True)
    checks = run_checks(ROOT, include_visual=args.require_visual)
    output = QA / ("local_visual_report.json" if args.require_visual else "integrity_report.json")
    output.write_text(
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(checks, ensure_ascii=True, indent=2))
    success = bool(checks["overall_pass"])
    if args.require_visual:
        success = success and bool(checks["submission_ready"])
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
