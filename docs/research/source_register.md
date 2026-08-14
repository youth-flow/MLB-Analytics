# 来源登记表

数据截止日：2026-08-12；下载时间统一记录于 `data/raw/source_manifest.csv`。

| 编号 | 来源 | 用途 | 本地快照/处理结果 |
|---|---|---|---|
| S1 | MLB StatsAPI, player 837227 game log | 17 场比赛、角色、局数、K、BB、ERA 的官方核对 | `data/raw/mlb_statsapi_game_log_2026.json`；`data/processed/mlb_game_log_2026.csv` |
| S2 | Baseball Savant Statcast Search | 逐球球种、球数、位置、结果、Run Value；主分析 1,240 球 | `data/raw/statcast_imai_2026.csv` |
| S3 | Baseball Savant Expected Statistics | ERA、xERA、K%、BB%及赛季级预期指标 | `data/raw/savant_expected_stats_pitchers_2026.csv` |
| S4 | Baseball Savant Pitch Arsenal Stats | 球种使用、Whiff、wOBA/xwOBA、官方 Run Value | `data/raw/savant_pitch_arsenal_stats_2026.csv` |
| S5 | NPB 官方球员页 | 2018—2025 年传统投球统计，核对 2025 年 163.2 局、178K、45BB、ERA 1.92 | `data/raw/npb_imai_player_page.html`；`data/processed/npb_imai_pitching_2018_2025.csv` |
| S6 | NPB Basement | 2023—2025 年高级投球与球种数据；2025 K%、BB%、FIP、球种使用和 xPV | `data/raw/npb_basement_*.js`；`data/processed/npb_basement_imai_*.csv` |
| S7 | MLB.com, 2026-05-31 | 赛季中适应过程、本人及教练语境 | `data/raw/mlb_imai_adjustment_article_2026-05-31.html` |
| S8 | MLB.com, 2026-07-31 | 球队将其转入牛棚及当时赛季状态 | `data/raw/mlb_imai_bullpen_article_2026-07-31.html` |

## 在线地址

1. https://statsapi.mlb.com/api/v1/people/837227/stats?stats=gameLog&group=pitching&season=2026
2. https://baseballsavant.mlb.com/savant-player/tatsuya-imai-837227
3. https://npb.jp/bis/players/31335134.html
4. https://npbbasement.com/
5. https://www.mlb.com/astros/news/tatsuya-imai-adjusting-to-pitching-in-major-leagues
6. https://www.mlb.com/astros/news/tatsuya-imai-moved-to-astros-bullpen

## 引用与解释规则

- MLB 赛季汇总以 S1/S3/S4 为准；逐球衍生以 S2 为准，并与 S1/S4 闭合。
- NPB 传统统计以 S5 为准；公开高级指标和球种级数据以 S6 为准。
- NPB 的 xPV/100 与 MLB 的 Run Value/100 定义和环境不同，只比较方向与球种在各自联盟中的相对有效性，不当作同尺度因果差值。
- 新闻来源只用于角色变更和适应背景，不用于替代可计算的数据证据。
