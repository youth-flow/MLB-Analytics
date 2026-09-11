"""Verify the migration archive using only Python's standard library."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git-index', action='store_true', help='Also verify staged Git blob bytes')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent
    root = repo / 'workspace_backup'
    manifest = json.loads((root / 'BACKUP_MANIFEST.json').read_text(encoding='utf-8'))
    entries = manifest['files']
    assert len(entries) == manifest['file_count']
    assert len({entry['path'] for entry in entries}) == len(entries)
    assert sum(entry['bytes'] for entry in entries) == manifest['total_bytes']
    git = None
    if args.git_index:
        git = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=repo,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for entry in entries:
            rel = PurePosixPath(entry['path'])
            assert not rel.is_absolute() and '..' not in rel.parts
            target = root.joinpath(*rel.parts)
            raw = target.read_bytes()
            assert len(raw) == entry['bytes'], entry['path']
            assert hashlib.sha256(raw).hexdigest().upper() == entry['sha256'], entry['path']
            if git:
                git.stdin.write((':workspace_backup/' + entry['path'] + '\n').encode('utf-8'))
                git.stdin.flush()
                fields = git.stdout.readline().split()
                assert len(fields) == 3 and fields[1] == b'blob', entry['path']
                blob = git.stdout.read(int(fields[2]))
                assert git.stdout.read(1) == b'\n'
                assert hashlib.sha256(blob).hexdigest().upper() == entry['sha256'], entry['path']
        print(f'PASS: {len(entries)} archived files, {manifest["total_bytes"]} bytes')
        if git:
            print('PASS: staged Git blobs exactly match all source SHA-256 hashes')
    finally:
        if git:
            git.stdin.close()
            git.wait()
    submission = root / '提交材料'
    text = (submission / '提交文件清单_SHA256.txt').read_text(encoding='utf-8')
    current = None
    count = 0
    for line in text.splitlines():
        match = re.match(r'^\d+\.\s+(.+\.docx)$', line)
        if match:
            current = match.group(1).replace('\\', '/')
        match = re.match(r'^\s*SHA-256：([0-9A-F]{64})$', line)
        if match and current:
            assert hashlib.sha256((submission / current).read_bytes()).hexdigest().upper() == match.group(1), current
            count += 1
            current = None
    assert count == 10, count
    print('PASS: all 10 final submission documents match their original submission manifest')


if __name__ == '__main__':
    main()
