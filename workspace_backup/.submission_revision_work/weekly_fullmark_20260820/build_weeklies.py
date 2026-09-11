from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

from docx import Document
from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
NS = {"w": W, "w14": W14}
XML = "http://www.w3.org/XML/1998/namespace"
REFERENCE_HASH = "07B267887710B0EF542D43EA1D6556CD4DA4D4BE6A83C9DFA967367F44BE0254"


def qn(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def parse_source(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    if not raw.startswith("---\n"):
        raise ValueError(f"Missing front matter: {path}")
    _, front, body = raw.split("---\n", 2)
    meta = {}
    for line in front.splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()

    items: list[dict] = []
    if meta.get("note"):
        items.append({"role": "note", "text": f"说明：{meta['note']}"})
    for block in re.split(r"\n\s*\n", body.strip()):
        line = " ".join(part.strip() for part in block.splitlines()).strip()
        if not line:
            continue
        if line.startswith("## "):
            items.append({"role": "heading", "text": line[3:].strip()})
        elif line.startswith("- "):
            # Blank-line-separated source bullets normally arrive one at a time.
            for bullet in line.split(" - "):
                bullet = bullet.removeprefix("- ").strip()
                if bullet:
                    items.append({"role": "bullet", "text": bullet})
        else:
            items.append({"role": "body", "text": line})

    headings = sum(item["role"] == "heading" for item in items)
    if headings != 5:
        raise ValueError(f"{path.name}: expected five headings, found {headings}")
    if not re.fullmatch(r"第[1-4]周实习记录\.docx", meta["filename"]):
        raise ValueError(f"Unexpected output filename: {meta['filename']}")
    return {"meta": meta, "items": items, "source": str(path)}


def clear_run_content(run: etree._Element) -> etree._Element:
    result = copy.deepcopy(run)
    for child in list(result):
        if child.tag != qn(W, "rPr"):
            result.remove(child)
    return result


def set_run_bold(run: etree._Element, bold: bool) -> None:
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        rpr = etree.Element(qn(W, "rPr"))
        run.insert(0, rpr)
    for child in list(rpr):
        if child.tag == qn(W, "b"):
            rpr.remove(child)
    if bold:
        etree.SubElement(rpr, qn(W, "b")).set(qn(W, "val"), "1")


def append_text_run(paragraph: etree._Element, run_template: etree._Element, text: str, bold: bool) -> None:
    if not text:
        return
    run = clear_run_content(run_template)
    set_run_bold(run, bold)
    text_node = etree.SubElement(run, qn(W, "t"))
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set(qn(XML, "space"), "preserve")
    text_node.text = text
    paragraph.append(run)


def set_paragraph_markup(paragraph: etree._Element, markdown: str) -> None:
    source_runs = paragraph.xpath("./w:r", namespaces=NS)
    run_template = source_runs[0] if source_runs else etree.Element(qn(W, "r"))
    for child in list(paragraph):
        if child.tag != qn(W, "pPr"):
            paragraph.remove(child)
    parts = re.split(r"(\*\*[^*]+\*\*)", markdown)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            append_text_run(paragraph, run_template, part[2:-2], True)
        else:
            append_text_run(paragraph, run_template, part, False)


def make_note_template(body_template: etree._Element) -> etree._Element:
    note = copy.deepcopy(body_template)
    ppr = note.find("w:pPr", NS)
    if ppr is not None:
        ind = ppr.find("w:ind", NS)
        if ind is not None:
            for attr in ("firstLine", "firstLineChars"):
                ind.attrib.pop(qn(W, attr), None)
        spacing = ppr.find("w:spacing", NS)
        if spacing is not None:
            spacing.set(qn(W, "after"), "80")
    for run in note.xpath("./w:r", namespaces=NS):
        rpr = run.find("w:rPr", NS)
        if rpr is None:
            rpr = etree.Element(qn(W, "rPr"))
            run.insert(0, rpr)
        for size_tag in ("sz", "szCs"):
            size = rpr.find(f"w:{size_tag}", NS)
            if size is None:
                size = etree.SubElement(rpr, qn(W, size_tag))
            size.set(qn(W, "val"), "21")
        if rpr.find("w:i", NS) is None:
            etree.SubElement(rpr, qn(W, "i")).set(qn(W, "val"), "1")
    return note


def update_core_properties(payload: bytes, title: str) -> bytes:
    root = etree.fromstring(payload)
    values = {
        qn(DC, "creator"): "杨炎新",
        qn(CP, "lastModifiedBy"): "杨炎新",
        qn(DC, "title"): title,
        qn(DC, "subject"): "本科生短学期实习记录",
        qn(DC, "description"): "",
        qn(CP, "keywords"): "",
        qn(DCTERMS, "created"): "2026-08-20T05:00:00Z",
        qn(DCTERMS, "modified"): "2026-08-20T05:00:00Z",
    }
    # cp:comments is not part of the OOXML core-properties schema.  Some
    # templates contain it, and Microsoft Word will then report the package as
    # damaged even though LibreOffice opens it.  Remove it instead of writing
    # an empty value.
    stale_comments = root.find(qn(CP, "comments"))
    if stale_comments is not None:
        root.remove(stale_comments)
    for tag, value in values.items():
        node = root.find(tag)
        if node is None:
            node = etree.SubElement(root, tag)
        node.text = value
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def build_one(reference: Path, source: Path, output: Path) -> dict:
    parsed = parse_source(source)
    meta = parsed["meta"]
    reference_document = Document(reference)
    heading_style_id = reference_document.styles["Heading 1"].style_id
    bullet_style_id = reference_document.styles["List Bullet"].style_id

    with zipfile.ZipFile(reference, "r") as source_zip:
        root = etree.fromstring(source_zip.read("word/document.xml"))
        # The supplied weekly template contains w14 paragraph identifiers on a
        # table-row element. LibreOffice tolerates them, but Microsoft Word
        # reports the package as damaged. Paragraph identifiers are valid on
        # w:p only, so remove inherited copies from every other element.
        for element in root.xpath("//*[@w14:paraId or @w14:textId]", namespaces=NS):
            if element.tag != qn(W, "p"):
                element.attrib.pop(qn(W14, "paraId"), None)
                element.attrib.pop(qn(W14, "textId"), None)
        body = root.find("w:body", NS)
        if body is None:
            raise ValueError("Reference document has no body")
        children = list(body)
        title_template = next(child for child in children if child.tag == qn(W, "p"))
        table_template = next(child for child in children if child.tag == qn(W, "tbl"))
        table_index = children.index(table_template)
        spacer_template = next(
            child
            for child in children[table_index + 1 :]
            if child.tag == qn(W, "p") and not child.xpath(".//w:t", namespaces=NS)
        )
        heading_template = next(
            child
            for child in children
            if child.tag == qn(W, "p")
            and child.xpath(f"./w:pPr/w:pStyle[@w:val='{heading_style_id}']", namespaces=NS)
        )
        body_template = next(
            child
            for child in children[children.index(heading_template) + 1 :]
            if child.tag == qn(W, "p")
            and not child.xpath(f"./w:pPr/w:pStyle[@w:val='{heading_style_id}']", namespaces=NS)
            and not child.xpath(f"./w:pPr/w:pStyle[@w:val='{bullet_style_id}']", namespaces=NS)
            and child.xpath(".//w:t", namespaces=NS)
        )
        bullet_template = next(
            child
            for child in children
            if child.tag == qn(W, "p")
            and child.xpath(f"./w:pPr/w:pStyle[@w:val='{bullet_style_id}']", namespaces=NS)
        )
        note_template = make_note_template(body_template)
        sect_pr = next(child for child in children if child.tag == qn(W, "sectPr"))

        title = copy.deepcopy(title_template)
        set_paragraph_markup(title, meta["title"])
        table = copy.deepcopy(table_template)
        topic_cell = table.xpath("./w:tr[2]/w:tc[4]", namespaces=NS)[0]
        set_paragraph_markup(topic_cell.xpath("./w:p[1]", namespaces=NS)[0], meta["period"])
        spacer = copy.deepcopy(spacer_template)
        rebuilt = [title, table, spacer]
        templates = {
            "heading": heading_template,
            "body": body_template,
            "bullet": bullet_template,
            "note": note_template,
        }
        for item in parsed["items"]:
            paragraph = copy.deepcopy(templates[item["role"]])
            set_paragraph_markup(paragraph, item["text"])
            rebuilt.append(paragraph)
        rebuilt.append(copy.deepcopy(sect_pr))

        for child in list(body):
            body.remove(child)
        for child in rebuilt:
            body.append(child)

        document_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")
        core_xml = update_core_properties(source_zip.read("docProps/core.xml"), meta["title"])
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w") as destination_zip:
            for info in source_zip.infolist():
                if info.filename == "word/document.xml":
                    payload = document_xml
                elif info.filename == "docProps/core.xml":
                    payload = core_xml
                else:
                    payload = source_zip.read(info.filename)
                destination_zip.writestr(info, payload)

    document = Document(output)
    visible = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    expected = [meta["title"]] + [re.sub(r"\*\*", "", item["text"]) for item in parsed["items"]]
    if visible != expected:
        raise AssertionError(f"Visible text mismatch in {output.name}")
    if document.tables[0].cell(1, 3).text.strip() != meta["period"]:
        raise AssertionError(f"Topic mismatch in {output.name}")
    if len(document.sections) != 1:
        raise AssertionError(f"Unexpected section count in {output.name}")
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise AssertionError(f"CRC failure in {output.name}")
        names = archive.namelist()
        forbidden = [
            name
            for name in names
            if name.startswith("word/comments")
            or name.startswith("word/vbaProject")
            or name.startswith("word/embeddings/")
            or name.startswith("word/activeX/")
        ]
        if forbidden:
            raise AssertionError(f"Forbidden package parts in {output.name}: {forbidden}")
    return {
        "source": str(source),
        "output": str(output),
        "sha256": sha256(output),
        "visible_paragraphs": len(visible),
        "characters": sum(len(text) for text in visible),
    }


def main() -> None:
    task_root = Path(os.environ["TASK_ROOT"])
    reference = Path(os.environ["REFERENCE_DOCX"])
    sources = Path(os.environ["SOURCES_DIR"])
    if sha256(reference) != REFERENCE_HASH:
        raise AssertionError("Reference changed; redistill before authoring")
    results = []
    for week in range(1, 5):
        source = sources / f"0{week}_week{week}.md"
        parsed = parse_source(source)
        output = task_root / "output" / parsed["meta"]["filename"]
        results.append(build_one(reference, source, output))
    if sha256(reference) != REFERENCE_HASH:
        raise AssertionError("Reference was modified")
    report = {
        "reference": str(reference),
        "reference_sha256": sha256(reference),
        "outputs": results,
    }
    report_path = task_root / "build_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
