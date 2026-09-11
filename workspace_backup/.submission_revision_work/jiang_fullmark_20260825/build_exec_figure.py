from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("figure_exec_decision_signals.png")
W, H = 1800, 760
BG = "#FFFFFF"
TEXT = "#222222"
MUTED = "#666666"
GRID = "#B8B8B8"
BLUE = "#2F5D7C"
RISK = "#9A4A45"
LIGHT = "#E7EDF1"
GRAY = "#A6A6A6"


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)
draw.text((55, 35), "为何先校准、后增负荷", font=font(46, True), fill=TEXT)
draw.text((55, 95), "冻结窗口：2026年3月29日至8月12日｜公开数据", font=font(24), fill=MUTED)

panel_y0, panel_y1 = 145, 675
panel_w, gap = 535, 40
panel_x = [55, 55 + panel_w + gap, 55 + 2 * (panel_w + gap)]
for x in panel_x:
    draw.rounded_rectangle((x, panel_y0, x + panel_w, panel_y1), radius=12, fill=BG, outline=GRID, width=2)


def label(x, y, text, size=27, color=TEXT, bold=False):
    draw.text((x, y), text, font=font(size, bold), fill=color)


# Panel 1
x = panel_x[0]
label(x + 28, 170, "1  控球优先", 32, TEXT, True)
label(x + 28, 220, "288 PA：80 K / 42 BB", 27, MUTED)
label(x + 28, 270, "NPB 2025  BB%", 23, MUTED)
draw.rounded_rectangle((x + 215, 274, x + 215 + 105, 298), radius=5, fill=GRAY)
label(x + 335, 267, "7.0%", 24, MUTED, True)
label(x + 28, 320, "MLB 2026  BB%", 23, TEXT)
draw.rounded_rectangle((x + 215, 324, x + 215 + 220, 348), radius=5, fill=RISK)
label(x + 448, 317, "14.6%", 24, RISK, True)
draw.line((x + 28, 382, x + panel_w - 28, 382), fill=GRID, width=2)
label(x + 28, 410, "Zone%", 23, MUTED)
label(x + 170, 402, "43.6%", 33, BLUE, True)
label(x + 28, 462, "首球好球率", 23, MUTED)
label(x + 170, 454, "51.7%", 33, BLUE, True)
draw.rounded_rectangle((x + 28, 532, x + panel_w - 28, 630), radius=10, fill=LIGHT)
label(x + 47, 550, "结论", 24, BLUE, True)
label(x + 47, 585, "先解决免费上垒与早期球数", 25, TEXT, True)

# Panel 2
x = panel_x[1]
label(x + 28, 170, "2  先核对左打", 32, TEXT, True)
label(x + 28, 222, "四缝线—左打", 25, TEXT, True)
label(x + 28, 260, "311球｜Whiff 15.4%｜RV/100 −1.27", 23, RISK)
label(x + 28, 315, "四缝线—右打", 25, TEXT, True)
label(x + 28, 353, "229球｜Whiff 27.0%｜RV/100 +1.47", 23, BLUE)
draw.line((x + 28, 403, x + panel_w - 28, 403), fill=GRID, width=2)
label(x + 28, 430, "滑球仍是当前证据最稳的核心球种", 24, TEXT, True)
label(x + 28, 475, "使用45.3%｜Whiff 40.6%｜官方RV +4", 23, BLUE)
draw.rounded_rectangle((x + 28, 532, x + panel_w - 28, 630), radius=10, fill=LIGHT)
label(x + 47, 550, "结论", 24, BLUE, True)
label(x + 47, 585, "保留滑球；四缝线不宜一刀切", 25, TEXT, True)

# Panel 3
x = panel_x[2]
label(x + 28, 170, "3  变速球待验证", 32, TEXT, True)
label(x + 28, 222, "使用率", 23, MUTED)
label(x + 150, 213, "12.7%  →  2.3%", 33, BLUE, True)
label(x + 28, 280, "与四缝线速度差", 23, MUTED)
label(x + 265, 271, "10.1  →  8.0 mph", 30, BLUE, True)
draw.line((x + 28, 335, x + panel_w - 28, 335), fill=GRID, width=2)
label(x + 28, 368, "MLB样本", 23, MUTED)
label(x + 155, 360, "仅29球", 32, RISK, True)
label(x + 28, 422, "Whiff为5/8次挥棒；不能外推长期质量", 23, TEXT)
draw.rounded_rectangle((x + 28, 532, x + panel_w - 28, 630), radius=10, fill=LIGHT)
label(x + 47, 550, "结论", 24, BLUE, True)
label(x + 47, 585, "有历史基础，不等于当前效果已确认", 25, TEXT, True)

draw.text(
    (55, 704),
    "注：跨联盟数值只作结构参照；侧别和角色分组均为观察结果。两次牛棚仅23个打席，不作因果结论。",
    font=font(22),
    fill=MUTED,
)
img.save(OUT, quality=95, dpi=(180, 180))
print(OUT)
