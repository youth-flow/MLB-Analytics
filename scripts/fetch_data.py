from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

START_DATE = "2026-03-29"
END_DATE = "2026-08-12"
PITCHER_ID = 837227
USER_AGENT = "Mozilla/5.0 (compatible; academic-course-project/1.0)"


def fetch(url: str, retries: int = 3, timeout: int = 90) -> tuple[bytes, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                return response.read(), dict(response.headers.items())
        except Exception as exc:  # network failures are preserved in the run log
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_error


def save_snapshot(name: str, url: str, payload: bytes, headers: dict[str, str], manifest: list[dict]) -> Path:
    path = RAW / name
    path.write_bytes(payload)
    manifest.append(
        {
            "file": path.relative_to(ROOT).as_posix(),
            "url": url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "content_type": headers.get("Content-Type", ""),
        }
    )
    return path


def statcast_pitcher_url() -> str:
    return (
        "https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfPT=&hfAB=&hfBBT=&hfPR=&hfZ="
        "&stadium=&hfBBL=&hfNewZones=&hfGT=R%7CPO%7CS%7C=&hfSea=&hfSit=&player_type=pitcher"
        "&hfOuts=&opponent=&pitcher_throws=&batter_stands=&hfSA="
        f"&game_date_gt={START_DATE}&game_date_lt={END_DATE}&pitchers_lookup%5B%5D={PITCHER_ID}"
        "&team=&position=&hfRO=&home_road=&hfFlag=&metric_1=&hfInn=&min_pitches=0&min_results=0"
        "&group_by=name&sort_col=pitches&player_event_sort=h_launch_speed&sort_order=desc&min_abs=0&type=details&"
    )


def normalize_npb_pitching(html_bytes: bytes) -> pd.DataFrame:
    text = html_bytes.decode("utf-8", errors="replace")
    tables = pd.read_html(StringIO(text))
    candidates = [table for table in tables if "年度" in table.columns and "防御率" in table.columns]
    if len(candidates) != 1:
        raise ValueError(f"Expected one NPB pitching table, found {len(candidates)}")
    frame = candidates[0].copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    year = pd.to_numeric(frame["年度"], errors="coerce")
    frame = frame[year.between(2000, 2100) & frame["登板"].notna()].copy()
    frame["年度"] = pd.to_numeric(frame["年度"], errors="raise").astype(int)

    def innings_to_outs(value: object) -> int:
        compact = str(value).replace(" ", "")
        if "." in compact:
            whole, fraction = compact.split(".", maxsplit=1)
        else:
            whole, fraction = compact, "0"
        fraction_outs = int(fraction or 0)
        if fraction_outs not in (0, 1, 2):
            raise ValueError(f"Invalid baseball innings value: {value}")
        return int(float(whole)) * 3 + fraction_outs

    frame["投球回_原始"] = frame["投球回"].astype(str).str.replace(" ", "", regex=False)
    frame["投球局数_出局数"] = frame["投球回"].map(innings_to_outs)
    frame["投球局数_十进制"] = frame["投球局数_出局数"] / 3
    for column in ["登板", "勝利", "敗北", "打者", "安打", "本塁打", "四球", "死球", "三振", "失点", "自責点", "防御率"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["K_per_9"] = frame["三振"] * 9 / frame["投球局数_十进制"]
    frame["BB_per_9"] = frame["四球"] * 9 / frame["投球局数_十进制"]
    frame["HR_per_9"] = frame["本塁打"] * 9 / frame["投球局数_十进制"]
    frame["K_BB_ratio"] = frame["三振"] / frame["四球"]
    return frame


def fetch_npb_basement(manifest: list[dict]) -> dict[int, dict]:
    home_url = "https://npbbasement.com/"
    home_payload, home_headers = fetch(home_url)
    save_snapshot("npb_basement_home.html", home_url, home_payload, home_headers, manifest)
    home_text = home_payload.decode("utf-8", errors="replace")
    asset_match = re.search(r'src="/assets/(index-[^"]+\.js)"', home_text)
    if not asset_match:
        raise ValueError("Could not discover the NPB Basement application asset")

    index_name = asset_match.group(1)
    index_url = f"https://npbbasement.com/assets/{index_name}"
    index_payload, index_headers = fetch(index_url)
    save_snapshot("npb_basement_app.js", index_url, index_payload, index_headers, manifest)
    index_text = index_payload.decode("utf-8", errors="replace")

    players: dict[int, dict] = {}
    for year in (2023, 2024, 2025):
        module_match = re.search(rf"\./({year}_1g-[A-Za-z0-9_-]+\.js)", index_text)
        if not module_match:
            raise ValueError(f"Could not discover NPB Basement {year} top-league module")
        module_name = module_match.group(1)
        module_url = f"https://npbbasement.com/assets/{module_name}"
        module_payload, module_headers = fetch(module_url)
        save_snapshot(f"npb_basement_{year}_1g.js", module_url, module_payload, module_headers, manifest)
        module_text = module_payload.decode("utf-8", errors="strict")
        payload_match = re.search(r"JSON\.parse\(`(.*)`\);export", module_text, flags=re.DOTALL)
        if not payload_match:
            raise ValueError(f"Could not extract JSON payload from NPB Basement {year} module")
        records = json.loads(payload_match.group(1))
        matches = [record for record in records if record.get("nameE") == "Tatsuya Imai"]
        if len(matches) != 1:
            raise ValueError(f"Expected one Tatsuya Imai record for {year}, found {len(matches)}")
        players[year] = matches[0]

    (PROCESSED / "npb_basement_imai_2023_2025.json").write_text(
        json.dumps(players, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    pitching_rows = []
    pitch_value_rows = []
    plate_discipline_rows = []
    for year, record in players.items():
        stats = record.get("Stats", {})
        total = stats.get("pit", {}).get("total", {})
        pitching_rows.append({"year": year, **total})
        for row in stats.get("pv", []):
            pitch_value_rows.append({"year": year, **row})
        for area, row in stats.get("pd", {}).items():
            plate_discipline_rows.append({"year": year, "area": area, **row})

    pd.DataFrame(pitching_rows).to_csv(
        PROCESSED / "npb_basement_imai_advanced_pitching_2023_2025.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(pitch_value_rows).to_csv(
        PROCESSED / "npb_basement_imai_pitch_values_2023_2025.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(plate_discipline_rows).to_csv(
        PROCESSED / "npb_basement_imai_plate_discipline_2023_2025.csv", index=False, encoding="utf-8-sig"
    )
    return players


def main() -> None:
    manifest: list[dict] = []
    sources = {
        "statcast_imai_2026.csv": statcast_pitcher_url(),
        "mlb_statsapi_game_log_2026.json": (
            f"https://statsapi.mlb.com/api/v1/people/{PITCHER_ID}/stats?stats=gameLog&group=pitching&season=2026"
        ),
        "npb_imai_player_page.html": "https://npb.jp/bis/players/31335134.html",
        "savant_imai_player_page.html": "https://baseballsavant.mlb.com/savant-player/tatsuya-imai-837227",
        "mlb_imai_player_page.html": "https://www.mlb.com/player/tatsuya-imai-837227",
        "mlb_imai_adjustment_article_2026-05-31.html": (
            "https://www.mlb.com/astros/news/tatsuya-imai-adjusting-to-pitching-in-major-leagues"
        ),
        "mlb_imai_bullpen_article_2026-07-31.html": (
            "https://www.mlb.com/astros/news/tatsuya-imai-moved-to-astros-bullpen"
        ),
        "savant_expected_stats_pitchers_2026.csv": (
            "https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year=2026"
            "&position=&team=&filterType=pa&min=25&csv=true"
        ),
        "savant_pitch_arsenal_stats_2026.csv": (
            "https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats?type=pitcher&pitchType="
            "&year=2026&team=&min=1&csv=true"
        ),
        "savant_percentile_rankings_2026.csv": (
            "https://baseballsavant.mlb.com/leaderboard/percentile-rankings?type=pitcher&year=2026"
            "&position=&team=&csv=true"
        ),
        "savant_pitch_movement_ff_2026.csv": (
            "https://baseballsavant.mlb.com/leaderboard/pitch-movement?year=2026&team=&min=50"
            "&pitch_type=FF&hand=&x=pitcher_break_x_hidden&z=pitcher_break_z_hidden&csv=true"
        ),
        "savant_pitch_movement_sl_2026.csv": (
            "https://baseballsavant.mlb.com/leaderboard/pitch-movement?year=2026&team=&min=50"
            "&pitch_type=SL&hand=&x=pitcher_break_x_hidden&z=pitcher_break_z_hidden&csv=true"
        ),
    }

    downloaded: dict[str, Path] = {}
    for name, url in sources.items():
        payload, headers = fetch(url)
        downloaded[name] = save_snapshot(name, url, payload, headers, manifest)
        print(f"downloaded {name}: {len(payload):,} bytes")

    basement_players = fetch_npb_basement(manifest)
    print(f"downloaded NPB Basement snapshots for: {sorted(basement_players)}")

    statcast = pd.read_csv(downloaded["statcast_imai_2026.csv"], low_memory=False)
    if len(statcast) < 1000 or set(statcast["pitcher"].dropna().astype(int)) != {PITCHER_ID}:
        raise ValueError("Statcast integrity check failed: unexpected row count or pitcher id")
    if statcast["game_date"].min() < START_DATE or statcast["game_date"].max() > END_DATE:
        raise ValueError("Statcast date range exceeded frozen analysis window")

    npb = normalize_npb_pitching(downloaded["npb_imai_player_page.html"].read_bytes())
    npb.to_csv(PROCESSED / "npb_imai_pitching_2018_2025.csv", index=False, encoding="utf-8-sig")

    for entry in manifest:
        path = ROOT / entry["file"]
        if path.suffix.lower() == ".csv":
            try:
                entry["rows_excluding_header"] = max(sum(1 for _ in path.open("r", encoding="utf-8-sig", errors="replace")) - 1, 0)
            except Exception:
                entry["rows_excluding_header"] = None

    manifest_path = RAW / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with (RAW / "source_manifest.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in manifest for key in row}))
        writer.writeheader()
        writer.writerows(manifest)

    print(f"Statcast rows: {len(statcast):,}")
    print(f"Statcast dates: {statcast['game_date'].min()} to {statcast['game_date'].max()}")
    print(f"NPB seasons: {npb['年度'].min()} to {npb['年度'].max()}")


if __name__ == "__main__":
    main()
