# Weekly record template contract

## Reference

- Retained reference: `C:\Users\yyx\Desktop\大三暑期短学期\提交材料\01_每周实习记录\第1周实习记录.docx`
- SHA-256: `07B267887710B0EF542D43EA1D6556CD4DA4D4BE6A83C9DFA967367F44BE0254`
- Rendered page count: 2; section count: 1.
- Render evidence: `template-reference-render/page-1.png`, `template-reference-render/page-2.png`.
- Structure evidence: `template-style-evidence.json` and the packaged `section_audit.py` output captured during this task.
- The retained reference is read-only and must remain byte-for-byte unchanged.

## Page system

- A4 portrait: 11906 x 16838 twips.
- Margins: left 1446, right 1446, top 1332, bottom 1276 twips.
- Header/footer distances: 680/680 twips. No visible header. No different-first-page treatment.
- One section only; continuous content flow. Footer contains a centered dynamic `PAGE` field in black 9 pt type.

## Typography and paragraph roles

- Title: first body paragraph, style `Normal`, centered; 方正小标宋简体 16 pt, bold, black; 4 pt after.
- Section headings: style `Heading 1`; visible text explicitly carries Chinese ordinal markers `一、` through `五、`; 仿宋_GB2312 12 pt, black and bold through the retained style. Heading rhythm and keep behavior are copied from the reference paragraph XML.
- Body: style `Normal`; 仿宋_GB2312 12 pt, black, justified by retained style; first-line indent and line spacing come from the retained `Normal` definition. No extra paragraph-after spacing.
- Bullet rows: style `List Bullet`; 仿宋_GB2312 12 pt, real Word bullets using the retained numbering part; left indent 21.25 pt, hanging indent 9.9 pt, 1.279 line spacing and 1.5 pt after.
- Blank spacer immediately after the information table: retained `Normal` paragraph with 0.3 line spacing.

## Information table

- First body object after the title; two rows x four columns; style `Normal Table`, centered, fixed layout and no autofit.
- Grid and cell widths in DXA: 1669, 2670, 1669, 3006; every `tcW` matches `tblGrid`.
- No fill; thin black full-grid borders inherited from the reference. Cells vertically centered.
- Table text is 仿宋_GB2312 12 pt. Labels and short values are centered; the company name is left aligned; the record-topic value is centered.
- Editable cells: only row 2 column 4 (`记录主题`) changes per week. Student, ID, company and labels are preserved.

## Components and content flow

1. Centered weekly title.
2. Two-row identity/topic table.
3. One compact spacer paragraph.
4. Five numbered sections in their existing target order.
5. Each section retains every existing target body paragraph; the final section retains its existing bullets or prose.
6. Centered page-number footer on every page.

## Slot map

- `word/document.xml/body/p[1]`: title; replace with `第2/3/4周实习记录` only.
- `word/document.xml/body/tbl[1]/tr[2]/tc[4]`: record topic; copy the exact topic from the corresponding current target document.
- Body paragraphs following the table spacer: rebuild from the corresponding current target document's five `Heading 1` groups. Remove the target-only subtitle and `(阶段回顾)` suffix; preserve all substantive section headings and paragraph text.
- Heading paragraphs use a clone of the reference heading paragraph; normal prose uses a clone of the reference body paragraph; bullets use a clone of the reference bullet paragraph. Extra paragraphs are permitted only as clones of these documented patterns.
- No images, captions, text boxes, comments or content controls are present or may be added.

## Stable locators and coverage

- Stable locators are package part plus body order and semantic style: first paragraph (title), first table row/cell coordinates, the first post-table blank paragraph, and all subsequent paragraphs classified by `Heading 1`, `Normal`, or `List Bullet`.
- Text coverage includes body paragraphs, all four table cells in both rows, the footer PAGE field and the empty header. No body text boxes, footnotes with content, endnotes with content or content controls exist.

## Package preservation

- Preserve byte-for-byte from the retained reference: `[Content_Types].xml`, root relationships, document relationships, footnotes, endnotes, footer, theme, settings, customXml, numbering, styles, web settings, font table, package relationships and app properties.
- Editable part: `word/document.xml` only. `docProps/core.xml` remains reference-derived and is not rewritten.
- All relationship IDs, section properties, table geometry, numbering definitions, footer field and opaque package parts remain unchanged.

## Fidelity gates

- Reference SHA-256 remains unchanged before and after authoring.
- Each output is visually source-derived: same title block, table, fonts, margins, five-section hierarchy, bullet treatment and footer.
- One section with identical A4 geometry and footer relationship.
- Package inventory matches the reference and only `word/document.xml` may have a different hash.
- No substantive text from weeks 2-4 is dropped or rewritten; only the title suffix/subtitle packaging is removed to match week 1.
- Render every output at 150 dpi and inspect every page at 100% for clipping, unexpected page count, broken table geometry, orphan headings, font substitution and footer placement.
