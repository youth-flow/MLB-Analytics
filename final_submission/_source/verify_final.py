import hashlib
import argparse
import json
import zipfile
from pathlib import Path
from lxml import etree
from pypdf import PdfReader

work = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--document-dir', type=Path)
args = parser.parse_args()
out = args.document_dir or (work.parent if work.name == '_source' else work.parent.parent/'提交材料'/'最终提交两份')
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
specs = [('实习报告_杨炎新_15页.docx', 'report', 15, 8, 8),
         ('蒋总汇总_今井达也MLB调整建议_2页.docx', 'executive', 2, 0, 2)]
results = []
for name, key, pages, images, tables in specs:
    path = out / name
    render = work / 'render_final' / key
    pdf = render / (key + '.pdf')
    reader = PdfReader(pdf)
    assert len(reader.pages) == pages
    assert all(len(p.extract_text().strip()) > 250 for p in reader.pages)
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
        styles = etree.fromstring(z.read('word/styles.xml'))
        assert len(root.findall('.//w:tbl', ns)) == tables
        assert len(root.findall('.//wp:inline', ns)) == images
        assert not root.findall('.//w:ins', ns)
        assert not root.findall('.//w:del', ns)
        assert not styles.findall('.//w:pBdr', ns)
        assert not any('comments' in n.lower() or n.endswith('.bin') for n in z.namelist())
        text = ''.join(root.itertext())
        assert '[[' not in text and 'PAGEBREAK' not in text
        embedded = {hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
        if images:
            for asset in ['答辩现场.jpg','阶段汇报总览.png','基础手写.jpg',
                          'theory-notes-01.jpg','theory-notes-02.jpg','theory-notes-03.jpg']:
                assert hashlib.sha256((work/'assets'/asset).read_bytes()).hexdigest() in embedded
    results.append({'file':name, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'bytes':path.stat().st_size,'word_pdf_pages':pages,
                    'tables':tables,'embedded_images':images,
                    'visual_review':'Not inferred by this script. See the separately recorded, hash-bound VISUAL_REVIEW.md.',
                    'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()})
receipt={'review_date':'2026-09-11','renderer':'Microsoft Word COM, exported PDF, pdftoppm at 120 dpi',
         'style':'A4; report 12 pt SimSun, 18.5 pt fixed line spacing; executive 9 pt Microsoft YaHei, 14 pt fixed line spacing',
         'scope':'Two DOCX deliverables only. MLB frozen through 2026-08-12. HKUST summer stage complete. No implemented team intervention or statistical significance claimed.',
         'results':results}
(work/'final_qa.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=True,indent=2))
