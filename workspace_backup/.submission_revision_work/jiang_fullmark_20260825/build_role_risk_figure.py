from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("figure_role_risk_intervals.png")
W, H = 1800, 860
BG = "#FFFFFF"
TEXT = "#222222"
MUTED = "#666666"
GRID = "#D0D0D0"
BLUE = "#2F5D7C"
BLUE_LIGHT = "#AFC3D1"
RISK = "#9A4A45"
RISK_LIGHT = "#D6B3B0"
GRAY = "#7A7A7A"


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def text(draw, xy, value, size=24, color=TEXT, bold=False, anchor=None):
    draw.text(xy, value, font=font(size, bold), fill=color, anchor=anchor)


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)
text(draw, (55, 35), "角色与侧别：只保留风险信号，不写成因果", 43, TEXT, True)
text(draw, (55, 94), "点为样本比例，线为 Wilson 95% 区间｜冻结窗口截至2026年8月12日", 23, MUTED)

# Left panel: role intervals
lx0, lx1 = 55, 1110
top, bottom = 155, 710
draw.rounded_rectangle((lx0, top, lx1, bottom), radius=12, outline=GRID, width=2)
text(draw, (lx0 + 30, top + 24), "牛棚窗口指标较高，但四项区间均与先发重叠", 29, TEXT, True)

axis_x0, axis_x1 = lx0 + 225, lx1 - 55
axis_y = bottom - 58
for pct in (20, 40, 60, 80, 100):
    x = axis_x0 + (axis_x1 - axis_x0) * pct / 100
    draw.line((x, top + 105, x, axis_y), fill="#E6E6E6", width=2)
    text(draw, (x, axis_y + 14), f"{pct}%", 19, MUTED, anchor="ma")

metrics = [
    ("Zone%", 43.4, 40.6, 46.3, 46.1, 36.1, 56.4),
    ("首球好球率", 49.8, 43.8, 55.8, 73.9, 53.5, 87.5),
    ("Whiff%", 31.6, 27.7, 35.8, 40.0, 27.0, 54.5),
    ("Chase%", 26.4, 23.2, 29.9, 37.5, 25.2, 51.6),
]


def px(value):
    return axis_x0 + (axis_x1 - axis_x0) * value / 100


for i, (name, sp, slo, shi, rp, rlo, rhi) in enumerate(metrics):
    y = top + 135 + i * 92
    text(draw, (lx0 + 30, y + 14), name, 23, TEXT, True, anchor="lm")
    # starter, top row of pair
    draw.line((px(slo), y, px(shi), y), fill=GRAY, width=6)
    draw.ellipse((px(sp) - 8, y - 8, px(sp) + 8, y + 8), fill=GRAY)
    text(draw, (axis_x1 + 10, y), f"先发 {sp:.1f}%", 19, GRAY, anchor="lm")
    # relief, lower row of pair
    ry = y + 32
    draw.line((px(rlo), ry, px(rhi), ry), fill=BLUE_LIGHT, width=8)
    draw.ellipse((px(rp) - 9, ry - 9, px(rp) + 9, ry + 9), fill=BLUE)
    text(draw, (axis_x1 + 10, ry), f"牛棚 {rp:.1f}%", 19, BLUE, True, anchor="lm")

# Right panel: platoon signal
rx0, rx1 = 1150, 1745
draw.rounded_rectangle((rx0, top, rx1, bottom), radius=12, outline=GRID, width=2)
text(draw, (rx0 + 30, top + 24), "四缝线侧别风险信号", 29, TEXT, True)
text(draw, (rx0 + 30, top + 70), "挥空率区间重叠，先核查而非定性", 22, MUTED)

rx_axis0, rx_axis1 = rx0 + 90, rx1 - 70
for pct in (0, 10, 20, 30, 40, 50):
    x = rx_axis0 + (rx_axis1 - rx_axis0) * pct / 50
    draw.line((x, top + 150, x, top + 405), fill="#E6E6E6", width=2)
    text(draw, (x, top + 420), f"{pct}%", 19, MUTED, anchor="ma")


def rpx(value):
    return rx_axis0 + (rx_axis1 - rx_axis0) * value / 50


platoons = [
    ("对左打", 15.4, 10.2, 22.6, "20/130次挥棒｜RV/100 −1.27", RISK, RISK_LIGHT),
    ("对右打", 27.0, 18.2, 38.1, "20/74次挥棒｜RV/100 +1.47", BLUE, BLUE_LIGHT),
]
for i, (name, point, lo, hi, detail, color, light) in enumerate(platoons):
    y = top + 200 + i * 150
    text(draw, (rx0 + 30, y), name, 24, TEXT, True, anchor="lm")
    line_y = y + 45
    draw.line((rpx(lo), line_y, rpx(hi), line_y), fill=light, width=10)
    draw.ellipse((rpx(point) - 10, line_y - 10, rpx(point) + 10, line_y + 10), fill=color)
    text(draw, (rpx(point), line_y - 22), f"{point:.1f}%", 20, color, True, anchor="ms")
    text(draw, (rx0 + 30, line_y + 38), detail, 20, color)

text(draw, (55, 755), "解读：角色变化与日期、健康、对手和比赛情境同时发生；侧别比较也未控制球数、落点和打者质量。", 22, MUTED)
text(draw, (55, 795), "因此，两组结果只用于确定下一步校准和采样重点，不能证明牛棚身份或打者侧别造成差异。", 22, MUTED, True)

img.save(OUT, quality=95, dpi=(180, 180))
print(OUT)
