"""Build the two course DOCX deliverables from frozen analysis outputs.

Formal manuscript preset: decision_memo (standard_business_brief), with named
course overrides: A4, Microsoft YaHei, 9 pt body, single spacing, two pages.
Full draft preset: compact_reference_guide, with named Chinese-report overrides:
A4, Microsoft YaHei, 10.5 pt body and restrained blue headings.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = ROOT / "outputs" / "figures"
FORMAL = REPORTS / "今井达也_MLB调整决策_正式文稿.docx"
FULL = REPORTS / "今井达也_MLB调整决策_完整分析底稿.docx"

FONT = "Microsoft YaHei"
NAVY = "17324D"
BLUE = "2E74B5"
MUTED = "617A95"
LIGHT = "EEF3F8"
PALE_GOLD = "FFF4D6"
WHITE = "FFFFFF"
INK = "172B3A"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=70, start=90, bottom=70, end=90) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_table_fixed(table, widths_dxa: list[int], indent_dxa: int = 90) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths_dxa)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent_dxa))
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        gc = OxmlElement("w:gridCol")
        gc.set(qn("w:w"), str(width))
        grid.append(gc)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths_dxa[idx]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_run_font(run, size: float, *, bold=False, color=INK, italic=False) -> None:
    run.font.name = FONT
    r_fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for key in ("ascii", "hAnsi", "eastAsia"):
        r_fonts.set(qn(f"w:{key}"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def set_style_font(style, size: float, *, bold=False, color=INK) -> None:
    style.font.name = FONT
    style._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor.from_string(color)


def setup_page(doc: Document, *, margins_cm=(1.65, 1.7, 1.55, 1.7)) -> None:
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(margins_cm[0])
        section.right_margin = Cm(margins_cm[1])
        section.bottom_margin = Cm(margins_cm[2])
        section.left_margin = Cm(margins_cm[3])
        section.header_distance = Cm(0.75)
        section.footer_distance = Cm(0.75)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("第 ")
    set_run_font(run, 7.5, color=MUTED)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)
    run = paragraph.add_run(" 页")
    set_run_font(run, 7.5, color=MUTED)


def add_running_furniture(doc: Document, left_text: str) -> None:
    for section in doc.sections:
        hp = section.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        hp.paragraph_format.space_after = Pt(0)
        r = hp.add_run(left_text)
        set_run_font(r, 7.5, bold=True, color=MUTED)
        fp = section.footer.paragraphs[0]
        add_page_number(fp)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_with_next(paragraph) -> None:
    paragraph.paragraph_format.keep_with_next = True


def add_text(doc, text: str, *, size=9, bold=False, color=INK, align=None,
             before=0, after=3, line=1.0, indent=0, keep=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if indent:
        pf.first_line_indent = Cm(indent)
    if keep:
        pf.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, size, bold=bold, color=color)
    return p


def add_heading(doc, text: str, level: int, *, compact=False):
    sizes = {1: 15.5, 2: 12.5, 3: 10.5}
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5 if compact else (12 if level == 1 else 8))
    p.paragraph_format.space_after = Pt(3 if compact else 5)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, sizes[level], bold=True, color=NAVY if level == 1 else BLUE)
    return p


def add_inline_markup(paragraph, text: str, *, size: float, color=INK) -> None:
    parts = re.split(r"(\*\*.*?\*\*|`.*?`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = paragraph.add_run(part[2:-2])
            set_run_font(r, size, bold=True, color=color)
        elif part.startswith("`") and part.endswith("`"):
            r = paragraph.add_run(part[1:-1])
            set_run_font(r, size - 0.3, color="7A5A00")
        else:
            r = paragraph.add_run(part)
            set_run_font(r, size, color=color)


def add_bullet(doc, text: str, *, size=10.5, level=0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.75 + level * 0.45)
    pf.first_line_indent = Cm(-0.38)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.18
    r = p.add_run("• ")
    set_run_font(r, size, bold=True, color=BLUE)
    add_inline_markup(p, text, size=size)
    return p


def add_numbered(doc, number: str, text: str, *, size=10.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.85)
    pf.first_line_indent = Cm(-0.55)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.18
    r = p.add_run(f"{number}. ")
    set_run_font(r, size, bold=True, color=BLUE)
    add_inline_markup(p, text, size=size)
    return p


def add_source_caption(doc, text: str, *, size=7.2):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(text)
    set_run_font(r, size, color=MUTED)
    return p


def build_formal() -> None:
    doc = Document()
    setup_page(doc, margins_cm=(1.45, 1.55, 1.40, 1.55))
    normal = doc.styles["Normal"]
    set_style_font(normal, 9)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.line_spacing = 1.0
    add_running_furniture(doc, "MLB 数据分析课程｜正式文稿")

    add_text(doc, "今井达也应如何重返 MLB 先发轮值？", size=16, bold=True,
             color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, after=1)
    add_text(doc, "——基于控球、球种价值与角色转换的决策分析", size=10.5,
             bold=True, color=BLUE, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    add_text(doc, "杨炎新　3230102355　｜　数据截止：2026-08-12", size=8,
             color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER, after=5)

    thesis = (
        "结论先行：今井达也的 MLB 困境不是“球威不够”，而是控球回退、对左打四缝线效率不佳，"
        "以及 NPB 时期有效变速球的使用和速度分层消失。建议暂留多局牛棚作为校准环境，先恢复抢好球能力并重建对左打变速球，"
        "再以量化门槛逐级返回先发；当前两次牛棚登板只能视为积极信号，不能证明永久转型更优。"
    )
    p = add_text(doc, thesis, size=9.2, bold=True, color=INK, after=5, line=1.05)
    p.paragraph_format.left_indent = Cm(0.22)
    p.paragraph_format.right_indent = Cm(0.22)

    add_heading(doc, "一、诊断：上限仍在，失败来自控球与球种组织", 3, compact=True)
    add_text(doc,
        "截至 8 月 12 日，今井在 MLB 17 场（15 场先发）64.2 局，ERA 5.29、xERA 4.89。K%为27.8%，与NPB 2025完全相同；"
        "真正恶化的是BB%，由7.0%升至14.6%，K-BB%由20.7%降至13.2%。1,240球显示Zone% 43.6%、首球好球率51.7%，"
        "低于Savant同页MLB平均48.7%和61.2%；Whiff% 32.3%却高于平均25.0%。优先级因此是重新取得球数控制，而不是继续追求球速。",
        size=8.8, indent=0.6, after=3, line=1.0)
    add_text(doc,
        "MLB中四缝线+滑球占88.9%。滑球仍是核心武器（45.3%使用、40.6% Whiff、+4 RV、xwOBA .274）；"
        "四缝线整体接近中性，却对左打只有15.4% Whiff、RV/100 -1.27。NPB 2025变速球曾有12.7%使用、41.6% Whiff、xPV/100 +1.03，"
        "到MLB仅剩2.3%；均速还由84.7升至86.8 mph，使其与94.9 mph四缝线的速度差缩小约2.1 mph。应重建这颗已有证据的球，而非凭空发明第三球种。",
        size=8.8, indent=0.6, after=2, line=1.0)
    doc.add_picture(str(FIGURES / "figure_1_core_diagnosis.png"), width=Inches(6.55))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_after = Pt(0)
    add_source_caption(doc, "图1　NPB 2025与MLB 2026诊断。来源：NPB官方、NPB Basement、Baseball Savant；跨联盟球种价值只比较方向。")

    doc.add_page_break()
    add_heading(doc, "二、角色证据：牛棚是校准环境，不是永久答案", 3, compact=True)
    add_text(doc,
        "15次先发的Zone%、首球好球率、Whiff%分别为43.4%、49.8%、31.6%；两次牛棚提高到46.1%、73.9%、40.0%。但牛棚只有89球、23打席，"
        "95%区间较宽；四缝线均速还从94.87略降至94.72 mph。面对打线第三轮的161球也没有球速下降。因此只能说短任务可能改善进区意愿，"
        "不能说后援角色已经产生确定因果提升。", size=8.8, indent=0.6, after=4, line=1.0)

    add_heading(doc, "三、执行路线与重返先发门槛", 3, compact=True)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    set_table_fixed(table, [1100, 2580, 2800, 2600])
    headers = ["阶段", "安排", "验收指标", "不达标处理"]
    for i, text in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_shading(cell, NAVY)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        set_run_font(r, 7.5, bold=True, color=WHITE)
    set_repeat_table_header(table.rows[0])
    rows = [
        ("A 校准\n3—4周", "1—2局多局牛棚；固定节奏；四缝线进区、滑球chase区、变速球8—10 mph速度差。", "变速球逐步到8%—12%，优先对左打；健康无复发。", "维持低负荷，复查健康、动作与握法。"),
        ("B 过程\n≥60打席", "以过程而非短期ERA判断。", "Zone≥46%；首球好球≥60%；BB≤10%；变速球质量不同时恶化。", "任一核心指标持续未达，回A期。"),
        ("C 负荷\n45→60→75球", "每阶至少两次；比较前后半段执行。", "后半段Zone与球速无明显下降；控球门槛继续成立。", "BB>12%、疲劳或动作退化，退一阶。"),
        ("D 角色", "达标则回传统先发；扩大样本后再判断轮次效应。", "60—75球健康且稳定。", "若只在前两轮稳定，用一次打线+或短先发。"),
    ]
    for ridx, row_data in enumerate(rows):
        cells = table.add_row().cells
        for idx, text in enumerate(row_data):
            if ridx % 2 == 0:
                set_cell_shading(cells[idx], LIGHT)
            p = cells[idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 0.95
            r = p.add_run(text)
            set_run_font(r, 7.25, bold=(idx == 0), color=INK)
    add_source_caption(doc, "注：门槛是基于MLB平均、今井NPB基准和牛棚初始信号制定的决策规则，不是由23个牛棚打席估出的能力真值。")

    add_heading(doc, "四、结论、限制与证据边界", 3, compact=True)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.0
    add_inline_markup(p,
        "**最终判断：**今井的竞争优势仍在；球队要修复的不是上限，而是把高质量滑球、可用四缝线和曾经成熟的变速球重新组织成能稳定抢好球、尤其能处理左打者的先发方案。",
        size=8.8)
    add_text(doc,
        "限制：NPB与MLB的用球、球场、打者与追踪模型不同；2026右臂疲劳与角色变化混杂时间趋势；变速球MLB仅29球、牛棚仅23打席；"
        "所有分组均为观察性描述。任何伤情复发都应优先于表现门槛。", size=8.0, after=3, line=1.0)
    add_source_caption(doc,
        "数据来源：[1] MLB StatsAPI；[2] Baseball Savant Statcast/Expected Statistics/Pitch Arsenal；[3] NPB官方；[4] NPB Basement；"
        "[5] MLB.com 2026-05-31；[6] MLB.com 2026-07-31。完整URL、原始快照、SHA-256、计算与AI记录见配套底稿。",
        size=7.1)

    doc.core_properties.title = "今井达也应如何重返MLB先发轮值？"
    doc.core_properties.author = "杨炎新"
    doc.core_properties.subject = "MLB数据分析课程正式文稿"
    doc.save(FORMAL)


def parse_full_markdown(doc: Document, path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    title_seen = False
    inserted_fig1 = False
    inserted_fig2 = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# ") and not title_seen:
            add_text(doc, line[2:], size=23, bold=True, color=NAVY,
                     align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
            title_seen = True
        elif line.startswith("## 完整分析底稿"):
            add_text(doc, line[3:], size=13, bold=True, color=BLUE,
                     align=WD_ALIGN_PARAGRAPH.CENTER, after=18)
        elif line.startswith("## "):
            heading = line[3:]
            if heading == "1. 作业要求与研究问题":
                doc.add_page_break()
            add_heading(doc, heading, 1)
        elif line.startswith("### "):
            add_heading(doc, line[4:], 2)
        elif re.match(r"^- ", line):
            add_bullet(doc, line[2:])
        elif re.match(r"^\d+\. ", line):
            m = re.match(r"^(\d+)\. (.*)", line)
            add_numbered(doc, m.group(1), m.group(2))
        elif line.startswith("作者：") or line.startswith("研究冻结日：") or line.startswith("项目目录："):
            add_text(doc, line.rstrip("  "), size=9.5, color=MUTED,
                     align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf = p.paragraph_format
            pf.space_after = Pt(5)
            pf.line_spacing = 1.20
            pf.first_line_indent = Cm(0.74)
            add_inline_markup(p, line, size=10.5)
        if line.startswith("结论：保留 H1 与 H2") and not inserted_fig1:
            doc.add_picture(str(FIGURES / "figure_1_core_diagnosis.png"), width=Inches(6.3))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_source_caption(doc, "图1　核心诊断：三振能力保留，控球与球种结构退化。")
            inserted_fig1 = True
        if line.startswith("结论：牛棚是重新练习") and not inserted_fig2:
            doc.add_picture(str(FIGURES / "figure_2_role_platoon.png"), width=Inches(6.3))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_source_caption(doc, "图2　角色与侧别：牛棚改善方向积极，但样本不足；四缝线问题集中于左打。")
            inserted_fig2 = True


def build_full() -> None:
    doc = Document()
    setup_page(doc, margins_cm=(1.75, 1.85, 1.65, 1.85))
    normal = doc.styles["Normal"]
    set_style_font(normal, 10.5)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.20
    add_running_furniture(doc, "今井达也 MLB 调整研究｜完整分析底稿")
    parse_full_markdown(doc, REPORTS / "full_analysis_draft.md")
    doc.core_properties.title = "今井达也MLB调整决策完整分析底稿"
    doc.core_properties.author = "杨炎新"
    doc.core_properties.subject = "数据、计算、迭代、反证与决策门槛"
    doc.save(FULL)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    build_formal()
    build_full()
    print(FORMAL)
    print(FULL)


if __name__ == "__main__":
    main()
