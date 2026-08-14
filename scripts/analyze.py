from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
RESEARCH = ROOT / "01_research"
QA = ROOT / "qa"
for directory in (PROCESSED, FIGURES, RESEARCH, QA):
    directory.mkdir(parents=True, exist_ok=True)

SWING_DESCRIPTIONS = {
    "swinging_strike",
    "swinging_strike_blocked",
    "foul",
    "foul_tip",
    "hit_into_play",
    "foul_bunt",
    "missed_bunt",
}
WHIFF_DESCRIPTIONS = {"swinging_strike", "swinging_strike_blocked", "foul_tip", "missed_bunt"}
BALL_DESCRIPTIONS = {"ball", "blocked_ball", "hit_by_pitch", "automatic_ball", "pitchout"}
PITCH_NAMES = {"FF": "四缝线", "SL": "滑球", "CH": "变速球", "FS": "指叉球", "SI": "伸卡球", "CU": "曲球"}
ORDER = ["FF", "SL", "CH", "FS", "SI", "CU"]


def innings_to_outs(value: object) -> int:
    text = str(value)
    if "." in text:
        whole, fraction = text.split(".", maxsplit=1)
    else:
        whole, fraction = text, "0"
    return int(whole) * 3 + int(fraction)


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return math.nan, math.nan
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return 100 * (center - half), 100 * (center + half)


def classify_count(frame: pd.DataFrame) -> pd.Series:
    pairs = pd.Series(list(zip(frame["balls"].astype(int), frame["strikes"].astype(int))), index=frame.index)
    return pd.Series(
        np.select(
            [
                pairs.isin([(0, 1), (0, 2), (1, 2)]),
                pairs.isin([(1, 0), (2, 0), (2, 1), (3, 0), (3, 1)]),
                pairs.isin([(3, 2)]),
            ],
            ["投手领先", "打者领先", "满球数"],
            default="均势",
        ),
        index=frame.index,
    )


def parse_game_log() -> pd.DataFrame:
    payload = json.loads((RAW / "mlb_statsapi_game_log_2026.json").read_text(encoding="utf-8"))
    rows = []
    for split in payload["stats"][0]["splits"]:
        stat = split["stat"]
        rows.append(
            {
                "game_date": split["date"],
                "game_pk": split["game"]["gamePk"],
                "opponent": split["opponent"]["name"],
                "role": "先发" if stat["gamesStarted"] == 1 else "牛棚",
                "outs": int(stat["outs"]),
                "innings_pitched": int(stat["outs"]) / 3,
                "pitches": int(stat["numberOfPitches"]),
                "strikes": int(stat["strikes"]),
                "batters_faced": int(stat["battersFaced"]),
                "strikeouts": int(stat["strikeOuts"]),
                "walks": int(stat["baseOnBalls"]),
                "hits": int(stat["hits"]),
                "home_runs": int(stat["homeRuns"]),
                "earned_runs": int(stat["earnedRuns"]),
                "era_after_game": float(stat["era"]),
                "whip_after_game": float(stat["whip"]),
            }
        )
    frame = pd.DataFrame(rows).sort_values("game_date")
    frame.to_csv(PROCESSED / "mlb_game_log_2026.csv", index=False, encoding="utf-8-sig")
    return frame


def rate_record(group: pd.DataFrame, games: int) -> dict[str, float]:
    first = group[group["pitch_number"] == 1]
    zone_n = int(group["zone"].notna().sum())
    zone_success = int(group["zone_in"].sum())
    first_success = int(group.loc[group["pitch_number"] == 1, "first_pitch_strike"].sum())
    swing_n = int(group["swing"].sum())
    whiff_success = int(group["whiff"].sum())
    outside_n = int((~group["zone_in"] & group["zone"].notna()).sum())
    chase_success = int((group["swing"] & ~group["zone_in"] & group["zone"].notna()).sum())
    zone_ci = wilson(zone_success, zone_n)
    fps_ci = wilson(first_success, len(first))
    whiff_ci = wilson(whiff_success, swing_n)
    chase_ci = wilson(chase_success, outside_n)
    return {
        "games": games,
        "pitches": len(group),
        "plate_appearances": len(first),
        "zone_pct": 100 * zone_success / zone_n,
        "zone_ci_low": zone_ci[0],
        "zone_ci_high": zone_ci[1],
        "first_pitch_strike_pct": 100 * first_success / len(first),
        "first_pitch_strike_ci_low": fps_ci[0],
        "first_pitch_strike_ci_high": fps_ci[1],
        "whiff_pct": 100 * whiff_success / swing_n,
        "whiff_ci_low": whiff_ci[0],
        "whiff_ci_high": whiff_ci[1],
        "chase_pct": 100 * chase_success / outside_n,
        "chase_ci_low": chase_ci[0],
        "chase_ci_high": chase_ci[1],
        "pitcher_run_value": group["delta_pitcher_run_exp"].sum(),
        "four_seam_velocity": group.loc[group["pitch_type"] == "FF", "release_speed"].mean(),
        "slider_velocity": group.loc[group["pitch_type"] == "SL", "release_speed"].mean(),
    }


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, font: ImageFont.FreeTypeFont) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=24, fill="#F7F9FC", outline="#D9E2EC", width=2)
    draw.text((x0 + 28, y0 + 22), title, font=font, fill="#17324D")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def grouped_bars(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    categories: list[str],
    series: list[tuple[str, list[float], str]],
    maximum: float,
    value_suffix: str = "%",
) -> None:
    x0, y0, x1, y1 = box
    chart_top, chart_bottom = y0 + 70, y1 - 80
    chart_left, chart_right = x0 + 50, x1 - 25
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#9FB3C8", width=2)
    group_width = (chart_right - chart_left) / len(categories)
    bar_width = min(42, group_width / (len(series) + 1))
    for index, category in enumerate(categories):
        center = chart_left + group_width * (index + 0.5)
        draw.text((center - 42, chart_bottom + 14), category, font=font(24), fill="#334E68")
        for s_index, (_, values, color) in enumerate(series):
            value = float(values[index])
            height = (chart_bottom - chart_top) * value / maximum
            left = center + (s_index - (len(series) - 1) / 2) * (bar_width + 8) - bar_width / 2
            draw.rounded_rectangle((left, chart_bottom - height, left + bar_width, chart_bottom), radius=5, fill=color)
            draw.text((left - 3, chart_bottom - height - 30), f"{value:.1f}{value_suffix}", font=font(18), fill="#243B53")
    legend_x = chart_left
    for name, _, color in series:
        draw.rounded_rectangle((legend_x, y0 + 22, legend_x + 22, y0 + 44), radius=4, fill=color)
        draw.text((legend_x + 30, y0 + 15), name, font=font(20), fill="#334E68")
        legend_x += 170


def make_core_figure(outcomes: pd.DataFrame, pitch_change: pd.DataFrame, pitch_summary: pd.DataFrame) -> None:
    image = Image.new("RGB", (1800, 1040), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 36), "诊断：三振能力保留，控球与球种结构发生退化", font=font(42, True), fill="#102A43")
    draw.text((72, 92), "NPB 2025 与 MLB 2026（截止 8 月 12 日）", font=font(24), fill="#627D98")

    left = (60, 145, 865, 655)
    right = (895, 145, 1740, 655)
    bottom = (60, 690, 1740, 990)
    draw_panel(draw, left, "能力结果：K%未降，BB%翻倍", font(29, True))
    draw_panel(draw, right, "球种结构：变速球消失，滑球负荷上升", font(29, True))
    draw_panel(draw, bottom, "MLB球种质量：滑球仍是核心武器，四缝线对左打风险突出", font(29, True))

    grouped_bars(
        draw,
        (85, 190, 840, 635),
        ["K%", "BB%", "K-BB%"],
        [
            ("NPB 2025", outcomes.loc[outcomes["level"] == "NPB 2025", ["K_pct", "BB_pct", "K_minus_BB_pct"]].iloc[0].tolist(), "#2A9D8F"),
            ("MLB 2026", outcomes.loc[outcomes["level"] == "MLB 2026", ["K_pct", "BB_pct", "K_minus_BB_pct"]].iloc[0].tolist(), "#E76F51"),
        ],
        maximum=32,
    )

    change = pitch_change.set_index("pitch_type")
    grouped_bars(
        draw,
        (920, 190, 1715, 635),
        [PITCH_NAMES[code] for code in ["FF", "SL", "CH", "FS"]],
        [
            ("NPB 2025", [change.loc[code, "npb_usage_pct"] for code in ["FF", "SL", "CH", "FS"]], "#2A9D8F"),
            ("MLB 2026", [change.loc[code, "mlb_usage_pct"] for code in ["FF", "SL", "CH", "FS"]], "#E76F51"),
        ],
        maximum=55,
    )

    arsenal = pitch_summary.set_index("pitch_type")
    cards = [
        ("滑球", "SL", "#2A9D8F", "跨左右打者均维持正价值"),
        ("四缝线", "FF", "#E76F51", "对左打：Whiff 15.4%，RV/100 -1.27"),
        ("变速球", "CH", "#E9C46A", "29球小样本；应重建设计而非直接弃用"),
    ]
    for index, (label, code, color, note) in enumerate(cards):
        x0 = 105 + index * 545
        draw.rounded_rectangle((x0, 755, x0 + 500, 950), radius=20, fill="white", outline=color, width=4)
        draw.text((x0 + 24, 775), label, font=font(30, True), fill=color)
        row = arsenal.loc[code]
        draw.text((x0 + 24, 825), f"使用 {row['usage_pct']:.1f}%   Whiff {row['whiff_pct']:.1f}%", font=font(23), fill="#243B53")
        if not math.isnan(float(row["official_xwoba"])):
            draw.text((x0 + 24, 864), f"xwOBA {row['official_xwoba']:.3f}   RV {row['official_run_value']:+.0f}", font=font(23), fill="#243B53")
        draw.text((x0 + 24, 910), note, font=font(19), fill="#627D98")

    image.save(FIGURES / "figure_1_core_diagnosis.png", quality=95, dpi=(180, 180))


def make_role_figure(role_summary: pd.DataFrame, platoon: pd.DataFrame) -> None:
    image = Image.new("RGB", (1800, 930), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 36), "角色与侧别：牛棚改善是积极信号，但样本不足以证明永久转型", font=font(40, True), fill="#102A43")
    draw.text((72, 91), "先发15场、1,151球；牛棚2场、89球", font=font(24), fill="#627D98")
    left = (60, 145, 1040, 835)
    right = (1070, 145, 1740, 835)
    draw_panel(draw, left, "过程指标：牛棚阶段更主动进入好球区", font(28, True))
    draw_panel(draw, right, "球种-打者侧别：四缝线问题集中在左打", font(28, True))

    role = role_summary.set_index("role")
    grouped_bars(
        draw,
        (90, 210, 1010, 710),
        ["Zone%", "首球好球%", "Whiff%", "Chase%"],
        [
            ("先发", [role.loc["先发", "zone_pct"], role.loc["先发", "first_pitch_strike_pct"], role.loc["先发", "whiff_pct"], role.loc["先发", "chase_pct"]], "#457B9D"),
            ("牛棚", [role.loc["牛棚", "zone_pct"], role.loc["牛棚", "first_pitch_strike_pct"], role.loc["牛棚", "whiff_pct"], role.loc["牛棚", "chase_pct"]], "#F4A261"),
        ],
        maximum=85,
    )
    draw.text((105, 755), "注意：牛棚只有23个打席，置信区间较宽；该结果用于设定观察门槛，不作因果结论。", font=font(21), fill="#7B2D26")

    subset = platoon[platoon["pitch_type"].isin(["FF", "SL"])].copy()
    values = {(row.pitch_type, row.stand): row.rv100 for row in subset.itertuples()}
    chart_left, chart_right, zero_x = 1120, 1690, 1405
    chart_top, row_gap = 265, 125
    scale = 95
    draw.line((zero_x, chart_top - 35, zero_x, chart_top + row_gap * 4 - 25), fill="#9FB3C8", width=3)
    rows = [("四缝线-左打", values[("FF", "L")]), ("四缝线-右打", values[("FF", "R")]), ("滑球-左打", values[("SL", "L")]), ("滑球-右打", values[("SL", "R")])]
    for idx, (label, value) in enumerate(rows):
        y = chart_top + idx * row_gap
        draw.text((1120, y - 2), label, font=font(24), fill="#334E68")
        end = zero_x + value * scale
        color = "#2A9D8F" if value >= 0 else "#E76F51"
        draw.rounded_rectangle((min(zero_x, end), y + 42, max(zero_x, end), y + 77), radius=8, fill=color)
        draw.text((end + (10 if value >= 0 else -100), y + 37), f"{value:+.2f}", font=font(21, True), fill=color)
    draw.text((1120, 748), "RV/100：正值对投手有利", font=font(21), fill="#627D98")
    draw.text((1120, 786), "四缝线对左打Whiff仅15.4%", font=font(21), fill="#7B2D26")

    image.save(FIGURES / "figure_2_role_platoon.png", quality=95, dpi=(180, 180))


def main() -> None:
    game_log = parse_game_log()
    statcast_all = pd.read_csv(RAW / "statcast_imai_2026.csv", low_memory=False)
    pitches = statcast_all[statcast_all["pitch_type"].notna()].copy()
    role_by_game = game_log.set_index("game_pk")["role"].to_dict()
    pitches["role"] = pitches["game_pk"].map(role_by_game)
    if pitches["role"].isna().any():
        raise ValueError("Some Statcast rows could not be mapped to an official MLB game log role")
    pitches["swing"] = pitches["description"].isin(SWING_DESCRIPTIONS)
    pitches["whiff"] = pitches["description"].isin(WHIFF_DESCRIPTIONS)
    pitches["zone_in"] = pitches["zone"].between(1, 9)
    pitches["first_pitch_strike"] = (pitches["pitch_number"] == 1) & ~pitches["description"].isin(BALL_DESCRIPTIONS)
    pitches["count_group"] = classify_count(pitches)

    role_rows = []
    for role, group in pitches.groupby("role"):
        role_rows.append({"role": role, **rate_record(group, int((game_log["role"] == role).sum()))})
    role_summary = pd.DataFrame(role_rows)
    role_summary.to_csv(PROCESSED / "mlb_process_metrics_by_role.csv", index=False, encoding="utf-8-sig")

    arsenal = pd.read_csv(RAW / "savant_pitch_arsenal_stats_2026.csv")
    arsenal = arsenal[arsenal["player_id"] == 837227].set_index("pitch_type")
    pitch_rows = []
    for pitch_type, group in pitches.groupby("pitch_type"):
        swing_n = int(group["swing"].sum())
        official = arsenal.loc[pitch_type]
        pitch_rows.append(
            {
                "pitch_type": pitch_type,
                "pitch_name_cn": PITCH_NAMES[pitch_type],
                "pitches": len(group),
                "usage_pct": 100 * len(group) / len(pitches),
                "velocity_mph": group["release_speed"].mean(),
                "zone_pct": 100 * group["zone_in"].mean(),
                "whiff_pct": 100 * group["whiff"].sum() / swing_n if swing_n else math.nan,
                "pitcher_run_value": group["delta_pitcher_run_exp"].sum(),
                "rv100_recomputed": 100 * group["delta_pitcher_run_exp"].sum() / len(group),
                "official_run_value": official["run_value"],
                "official_rv100": official["run_value_per_100"],
                "official_xwoba": official["est_woba"],
                "official_woba": official["woba"],
                "official_hard_hit_pct": official["hard_hit_percent"],
            }
        )
    pitch_summary = pd.DataFrame(pitch_rows).sort_values("pitches", ascending=False)
    pitch_summary.to_csv(PROCESSED / "mlb_pitch_type_summary.csv", index=False, encoding="utf-8-sig")

    platoon_rows = []
    for (pitch_type, stand), group in pitches.groupby(["pitch_type", "stand"]):
        swing_n = int(group["swing"].sum())
        outside_n = int((~group["zone_in"] & group["zone"].notna()).sum())
        platoon_rows.append(
            {
                "pitch_type": pitch_type,
                "stand": stand,
                "pitches": len(group),
                "zone_pct": 100 * group["zone_in"].mean(),
                "whiff_pct": 100 * group["whiff"].sum() / swing_n if swing_n else math.nan,
                "chase_pct": 100 * (group["swing"] & ~group["zone_in"] & group["zone"].notna()).sum() / outside_n if outside_n else math.nan,
                "rv100": 100 * group["delta_pitcher_run_exp"].sum() / len(group),
            }
        )
    platoon = pd.DataFrame(platoon_rows)
    platoon.to_csv(PROCESSED / "mlb_pitch_metrics_by_batter_hand.csv", index=False, encoding="utf-8-sig")

    count_rows = []
    for (count_group, pitch_type), group in pitches.groupby(["count_group", "pitch_type"]):
        count_rows.append(
            {
                "count_group": count_group,
                "pitch_type": pitch_type,
                "pitches": len(group),
                "usage_within_count_pct": 100 * len(group) / len(pitches[pitches["count_group"] == count_group]),
                "zone_pct": 100 * group["zone_in"].mean(),
                "rv100": 100 * group["delta_pitcher_run_exp"].sum() / len(group),
            }
        )
    pd.DataFrame(count_rows).to_csv(PROCESSED / "mlb_pitch_metrics_by_count.csv", index=False, encoding="utf-8-sig")

    tto_rows = []
    starters = pitches[pitches["role"] == "先发"]
    for tto, group in starters.groupby("n_thruorder_pitcher"):
        tto_rows.append(
            {
                "times_through_order": int(tto),
                "pitches": len(group),
                "zone_pct": 100 * group["zone_in"].mean(),
                "pitcher_run_value": group["delta_pitcher_run_exp"].sum(),
                "four_seam_velocity": group.loc[group["pitch_type"] == "FF", "release_speed"].mean(),
            }
        )
    pd.DataFrame(tto_rows).to_csv(PROCESSED / "mlb_times_through_order.csv", index=False, encoding="utf-8-sig")

    npb_advanced = pd.read_csv(PROCESSED / "npb_basement_imai_advanced_pitching_2023_2025.csv")
    npb_2025 = npb_advanced[npb_advanced["year"] == 2025].iloc[0]
    season_outs = int(game_log["outs"].sum())
    mlb_bf = int(game_log["batters_faced"].sum())
    mlb_k = int(game_log["strikeouts"].sum())
    mlb_bb = int(game_log["walks"].sum())
    expected = pd.read_csv(RAW / "savant_expected_stats_pitchers_2026.csv")
    expected_row = expected[expected["player_id"] == 837227].iloc[0]
    outcomes = pd.DataFrame(
        [
            {
                "level": "NPB 2025",
                "BF": npb_2025["TBF"],
                "K_pct": npb_2025["K%"],
                "BB_pct": npb_2025["BB%"],
                "K_minus_BB_pct": npb_2025["K-BB%"],
                "ERA": 1.92,
                "xERA": math.nan,
            },
            {
                "level": "MLB 2026",
                "BF": mlb_bf,
                "K_pct": 100 * mlb_k / mlb_bf,
                "BB_pct": 100 * mlb_bb / mlb_bf,
                "K_minus_BB_pct": 100 * (mlb_k - mlb_bb) / mlb_bf,
                "ERA": 27 * game_log["earned_runs"].sum() / season_outs,
                "xERA": expected_row["xera"],
            },
        ]
    )
    outcomes.to_csv(PROCESSED / "npb_2025_vs_mlb_2026_outcomes.csv", index=False, encoding="utf-8-sig")

    npb_pitch = pd.read_csv(PROCESSED / "npb_basement_imai_pitch_values_2023_2025.csv")
    npb_pitch = npb_pitch[npb_pitch["year"] == 2025].set_index("Type")
    mlb_pitch = pitch_summary.set_index("pitch_type")
    change_rows = []
    for code in ORDER:
        change_rows.append(
            {
                "pitch_type": code,
                "pitch_name_cn": PITCH_NAMES[code],
                "npb_usage_pct": npb_pitch.loc[code, "Pitch%"] if code in npb_pitch.index else 0.0,
                "mlb_usage_pct": mlb_pitch.loc[code, "usage_pct"] if code in mlb_pitch.index else 0.0,
                "usage_change_pp": (mlb_pitch.loc[code, "usage_pct"] if code in mlb_pitch.index else 0.0) - (npb_pitch.loc[code, "Pitch%"] if code in npb_pitch.index else 0.0),
                "npb_velocity_mph": npb_pitch.loc[code, "Velo."] / 1.609344 if code in npb_pitch.index else math.nan,
                "mlb_velocity_mph": mlb_pitch.loc[code, "velocity_mph"] if code in mlb_pitch.index else math.nan,
                "npb_whiff_pct": npb_pitch.loc[code, "Whiff%"] if code in npb_pitch.index else math.nan,
                "mlb_whiff_pct": mlb_pitch.loc[code, "whiff_pct"] if code in mlb_pitch.index else math.nan,
                "npb_xpv100": npb_pitch.loc[code, "xPV/100"] if code in npb_pitch.index else math.nan,
                "mlb_rv100": mlb_pitch.loc[code, "official_rv100"] if code in mlb_pitch.index else math.nan,
            }
        )
    pitch_change = pd.DataFrame(change_rows)
    pitch_change.to_csv(PROCESSED / "npb_2025_vs_mlb_2026_pitch_mix.csv", index=False, encoding="utf-8-sig")

    terminal = statcast_all[statcast_all["events"].notna()]
    reconciliation = pd.DataFrame(
        [
            {"check": "Statcast pitch rows", "computed": len(pitches), "reference": int(arsenal["pitches"].sum()), "difference": len(pitches) - int(arsenal["pitches"].sum())},
            {
                "check": "Strikeouts",
                "computed": int(terminal["events"].isin(["strikeout", "strikeout_double_play"]).sum()),
                "reference": mlb_k,
                "difference": int(terminal["events"].isin(["strikeout", "strikeout_double_play"]).sum()) - mlb_k,
            },
            {"check": "Walks", "computed": int(terminal["events"].isin(["walk", "intent_walk"]).sum()), "reference": mlb_bb, "difference": int(terminal["events"].isin(["walk", "intent_walk"]).sum()) - mlb_bb},
            {"check": "Games", "computed": int(pitches["game_pk"].nunique()), "reference": len(game_log), "difference": int(pitches["game_pk"].nunique()) - len(game_log)},
        ]
    )
    reconciliation.to_csv(QA / "data_reconciliation.csv", index=False, encoding="utf-8-sig")
    if not (reconciliation["difference"] == 0).all():
        raise ValueError("Data reconciliation failed")

    role_index = role_summary.set_index("role")
    pitch_index = pitch_summary.set_index("pitch_type")
    hand_index = platoon.set_index(["pitch_type", "stand"])
    summary = {
        "cutoff": "2026-08-12",
        "games": len(game_log),
        "starts": int((game_log["role"] == "先发").sum()),
        "relief_appearances": int((game_log["role"] == "牛棚").sum()),
        "innings": season_outs / 3,
        "era": float(outcomes.loc[outcomes["level"] == "MLB 2026", "ERA"].iloc[0]),
        "xera": float(expected_row["xera"]),
        "k_pct": 100 * mlb_k / mlb_bf,
        "bb_pct": 100 * mlb_bb / mlb_bf,
        "zone_pct": 100 * pitches["zone_in"].mean(),
        "first_pitch_strike_pct": 100 * pitches.loc[pitches["pitch_number"] == 1, "first_pitch_strike"].mean(),
        "whiff_pct": 100 * pitches["whiff"].sum() / pitches["swing"].sum(),
        "chase_pct": 100 * (pitches["swing"] & ~pitches["zone_in"] & pitches["zone"].notna()).sum() / (~pitches["zone_in"] & pitches["zone"].notna()).sum(),
        "two_pitch_usage_pct": float(pitch_index.loc[["FF", "SL"], "usage_pct"].sum()),
        "npb_2025_changeup_usage_pct": float(npb_pitch.loc["CH", "Pitch%"]),
        "mlb_changeup_usage_pct": float(pitch_index.loc["CH", "usage_pct"]),
        "npb_2025_changeup_velocity_mph": float(npb_pitch.loc["CH", "Velo."] / 1.609344),
        "mlb_changeup_velocity_mph": float(pitch_index.loc["CH", "velocity_mph"]),
        "four_seam_lhb_rv100": float(hand_index.loc[("FF", "L"), "rv100"]),
        "four_seam_rhb_rv100": float(hand_index.loc[("FF", "R"), "rv100"]),
        "four_seam_lhb_whiff_pct": float(hand_index.loc[("FF", "L"), "whiff_pct"]),
        "relief_zone_pct": float(role_index.loc["牛棚", "zone_pct"]),
        "relief_first_pitch_strike_pct": float(role_index.loc["牛棚", "first_pitch_strike_pct"]),
        "relief_whiff_pct": float(role_index.loc["牛棚", "whiff_pct"]),
        "relief_plate_appearances": int(role_index.loc["牛棚", "plate_appearances"]),
    }
    (PROCESSED / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    analysis_cycles = f"""# 分析循环结果

## 循环 1：球威还是控球？

- 结果：MLB K% 为 {summary['k_pct']:.1f}%，与 NPB 2025 的 27.8%基本一致；BB% 从 NPB 2025 的 7.0%升至 {summary['bb_pct']:.1f}%。
- 判断：H1“球威保留”和 H2“控球瓶颈”得到支持。不能把高ERA解释为单纯球威不足。

## 循环 2：是否只是二球种过度依赖？

- 结果：MLB 四缝线+滑球占 {summary['two_pitch_usage_pct']:.1f}%；NPB 2025 变速球占 {summary['npb_2025_changeup_usage_pct']:.1f}%，MLB降至 {summary['mlb_changeup_usage_pct']:.1f}%。
- 新发现：今井不是“没有第三球种”，而是迁移到MLB后基本失去了原本有效的变速球。NPB 2025 变速球 Whiff 41.6%、xPV/100 +1.03。
- 修正：建议从“开发任意第三球种”改为“优先重建2025年已有证据的变速球”，并对小样本保持克制。

## 循环 3：问题是否集中在特定对手？

- 结果：四缝线对左打 RV/100 为 {summary['four_seam_lhb_rv100']:+.2f}、Whiff仅 {summary['four_seam_lhb_whiff_pct']:.1f}%；对右打 RV/100 为 {summary['four_seam_rhb_rv100']:+.2f}。
- 判断：不应笼统减少四缝线；调整应集中在对左打的配球，并让变速球承担横向速度差角色。

## 循环 4：牛棚是否解决问题？

- 结果：两次牛棚登板的 Zone% 为 {summary['relief_zone_pct']:.1f}%、首球好球率 {summary['relief_first_pitch_strike_pct']:.1f}%、Whiff {summary['relief_whiff_pct']:.1f}%。
- 反证检查：样本只有 {summary['relief_plate_appearances']} 个打席；四缝线平均球速并未明显提升，因此不能宣称牛棚角色产生了确定因果改善。
- 决策：牛棚适合作为短期校准环境，但长期是否转为后援仍无充分证据。

## 最终研究判断

主要问题不是球速或三振能力，而是控球回退、对左打四缝线效果不佳，以及NPB时期有效变速球的使用与速度差消失。短期保留多局牛棚以恢复首球好球和好球区率；中期重建对左打变速球；达到预设门槛后再重返先发。
"""
    (RESEARCH / "analysis_cycle_results.md").write_text(analysis_cycles, encoding="utf-8")

    make_core_figure(outcomes, pitch_change, pitch_summary)
    make_role_figure(role_summary, platoon)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
