# Weekly internship record template contract

- Reference: `C:\Users\yyx\Desktop\大三暑期短学期\提交材料\01_每周实习记录\第1周实习记录.docx`
- Reference SHA-256: `2B0F58826C9FC2972A38E3AAF71EE0737386B8C45DE36140D666AC1BCF9639D8`
- Reference structure: one section, two rendered pages, one 2 x 4 information table, no images.
- Visual evidence: the first-week package is readable by python-docx but its legacy OOXML is rejected by Word COM; the structurally matching third-week document was resaved without changing the visual system and rendered to `.submission_revision_work/week3_before_render/` for the baseline visual check.

## Page system

- A4 portrait: 8.27 x 11.69 in.
- Margins: left/right 1.00 in, top 0.93 in, bottom 0.89 in.
- Footer distance: 0.47 in; centered Arabic page number.
- One section; no first-page or odd/even-page variants.

## Typography and paragraph roles

- Document title: centered, 16 pt `方正小标宋简体`, black, 4 pt after.
- Information table: 12 pt `仿宋_GB2312`, black; compact labels and values centered except the longer organization name.
- Explanatory note after the table: 10.5 pt `仿宋_GB2312`, italic, black.
- Heading 1: 12 pt `仿宋_GB2312`, bold, black; Chinese numbered headings `一、` through `五、`.
- Body: 12 pt `仿宋_GB2312`, black, approximately 1.15 line spacing, first-line indent inherited from the source.
- Final output list: real `List Bullet` paragraphs, 12 pt `仿宋_GB2312`, hanging indent preserved from the source.

## Table and content flow

- Four table columns use the source widths 1669 / 2670 / 1669 / 3006 twips.
- Row 1: student / name / student number / value.
- Row 2: internship unit / organization / record topic / value.
- Flow: title, information table, italic note, five numbered sections, and a short four-item completion/next-step list in the final section.
- Target length: two pages, with data-analysis work about two thirds and HKUST research about one third.

## Editable slots

- Week title and record-topic value.
- The explanatory note, which must match the first-week wording exactly.
- Five section headings and their body paragraphs.
- The four final list items.
- Student name, number, and internship unit must remain unchanged.

## Preservation and fidelity gates

- Preserve A4 geometry, margins, footer/page number, information-table geometry, title hierarchy, fonts, paragraph rhythm, and black-only plain styling.
- Preserve all package parts not needed for text edits; however, save the final third- and fourth-week files through python-docx so Microsoft Word can open them cleanly.
- Final files must open in Microsoft Word, remain two pages, pass Open XML validation except any validator-version-only compatibility warning inherited from Office, and have no clipping, overlap, broken table, missing glyph, or awkward page break.
