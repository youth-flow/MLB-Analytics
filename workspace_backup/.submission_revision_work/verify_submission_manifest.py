import hashlib
import re
from pathlib import Path


ROOT = Path(r"C:\Users\yyx\Desktop\大三暑期短学期")
MANIFEST = ROOT / "提交材料" / "提交文件清单_SHA256.txt"

lines = MANIFEST.read_text(encoding="utf-8").splitlines()
records = []
current = None
for line in lines:
    match = re.match(r"^\d+\.\s+(.+)$", line)
    if match:
        current = match.group(1).strip()
        continue
    match = re.match(r"^\s*SHA-256：([0-9A-F]{64})$", line)
    if match and current:
        records.append((current, match.group(1)))
        current = None

assert len(records) == 10, f"expected 10 manifest records, got {len(records)}"
for relative, expected in records:
    path = ROOT / "提交材料" / Path(relative)
    assert path.is_file(), f"missing: {path}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    assert actual == expected, f"hash mismatch: {relative}\nexpected={expected}\nactual={actual}"
    print(f"PASS|{actual}|{relative}")
