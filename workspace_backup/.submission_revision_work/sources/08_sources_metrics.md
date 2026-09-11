---
filename: 底稿02_MLB数据来源与指标口径.docx
kind: draft_short
title: 底稿02　数据来源与指标口径
subtitle: 今井达也MLB调整决策｜数据截止2026年8月12日
meta_line: 杨炎新（3230102355）　｜　MLBAM ID 837227　｜　17份原始快照　｜　版本9c8033d
---

## 一、这份底稿记录什么

本稿只记录数据来源、字段口径、处理血缘和更新条件，不重复结论或行动建议。分析窗口为2026年3月29日至8月12日；原始文件于8月14日下载，因此“下载时间”不等于“数据截止日”。每份文件的URL、下载时间、字节数和SHA-256均登记在两份来源清单，原始快照不经手工改写：

- `data/raw/source_manifest.csv`；
- `data/raw/source_manifest.json`。

主分析脚本`analyze.py`直接读取4份raw：StatsAPI比赛日志、Statcast逐球、Savant Expected Statistics和Savant Pitch Arsenal。跨联盟部分还读取两份已经冻结的NPB处理表：

- `npb_basement_imai_advanced_pitching_2023_2025.csv`；
- `npb_basement_imai_pitch_values_2023_2025.csv`。

其余raw并非都参加计算，有些只负责在联网刷新时重建处理表，有些只作为背景和审计留存。

比赛日志、打席和逐球是三个分析单位。比赛日志负责场次、角色、局数和官方结果；打席用于K%、BB%和首球指标；逐球用于球种、球数、挥棒、进区、打者侧别和面对打线轮次。64.2局是棒球记分法，表示64局加2个出局数。脚本先换算为194个出局数，再计算ERA，不能把64.2当成十进制数。

## 二、17份原始快照用途台账

下表的“计算使用”指`analyze.py`直接读取；“刷新依赖”指`fetch_data.py --refresh-data`用来生成NPB处理表或发现年度数据模块；“背景留存”指保留网页或榜单作语境、人工核查和后续扩展，当前主计算不读取。

[[COLWEIGHTS:0.35,2.25,0.8,2.6]]
| 序 | raw文件 | 分类 | 当前用途 |
| --- | --- | --- | --- |
| 1 | `statcast_imai_2026.csv` | 计算使用 | 1,241条原始记录；逐球指标、球种使用、分组和重算RV的基础 |
| 2 | `mlb_statsapi_game_log_2026.json` | 计算使用 | 17场日志；角色、出局数、打者数、K、BB、自责分和ERA |
| 3 | `npb_imai_player_page.html` | 刷新依赖 | 生成2018—2025年NPB官方传统统计表；当前主脚本不直接读取 |
| 4 | `savant_imai_player_page.html` | 背景留存 | Savant球员页快照，供球员身份和网页展示信息复核 |
| 5 | `mlb_imai_player_page.html` | 背景留存 | MLB球员页快照，供名单和基本资料复核 |
| 6 | `mlb_imai_adjustment_article_2026-05-31.html` | 背景留存 | 适应过程的时间语境，不替代统计证据 |
| 7 | `mlb_imai_bullpen_article_2026-07-31.html` | 背景留存 | 转入牛棚的时间语境，不用于估计角色效果 |
| 8 | `savant_expected_stats_pitchers_2026.csv` | 计算使用 | 按`player_id`筛选今井；当前只读取`xera`字段 |
| 9 | `savant_pitch_arsenal_stats_2026.csv` | 计算使用 | 球种级官方RV、RV/100、wOBA、xwOBA、Hard-hit%，并核对总球数 |
| 10 | `savant_percentile_rankings_2026.csv` | 背景留存 | 百分位榜单快照；当前主脚本未读取 |
| 11 | `savant_pitch_movement_ff_2026.csv` | 背景留存 | 四缝线位移榜单快照；当前主脚本未读取 |
| 12 | `savant_pitch_movement_sl_2026.csv` | 背景留存 | 滑球位移榜单快照；当前主脚本未读取 |
| 13 | `npb_basement_home.html` | 刷新依赖 | 发现NPB Basement应用脚本的实际文件名 |
| 14 | `npb_basement_app.js` | 刷新依赖 | 发现2023、2024、2025年度一军数据模块 |
| 15 | `npb_basement_2023_1g.js` | 刷新依赖 | 提取今井2023年高级、球种和挥棒纪律数据 |
| 16 | `npb_basement_2024_1g.js` | 刷新依赖 | 提取今井2024年高级、球种和挥棒纪律数据 |
| 17 | `npb_basement_2025_1g.js` | 刷新依赖 | 提取今井2025年高级、球种和挥棒纪律数据 |

第3项生成NPB官方传统统计表，第13—17项生成三类NPB Basement CSV和一份JSON。主分析只读取其中的高级投球表与球种价值表；官方传统统计表、挥棒纪律表和完整JSON留作核查，不写成“参加了主计算”。

## 三、清洗、事件集合与分母

Statcast快照共1,241行。其中1条是第7球的`automatic_ball`，没有`pitch_type`。该行保留在raw中，但球种和逐球主分析只使用其余1,240行；它不是首球，所以288个打席的首球仍全部保留。K、BB和面对打者数取自StatsAPI，不靠删除后的逐球表反推。

代码中的事件集合固定如下：

- `Swing`包括`swinging_strike`、`swinging_strike_blocked`、`foul`、`foul_tip`、`hit_into_play`、`foul_bunt`、`missed_bunt`。
- `Whiff`包括`swinging_strike`、`swinging_strike_blocked`、`foul_tip`、`missed_bunt`，是`Swing`的子集。
- `Ball`包括`ball`、`blocked_ball`、`hit_by_pitch`、`automatic_ball`、`pitchout`。
- 首球好球要求`pitch_number=1`，且`description`不属于`Ball`。本样本149次成功由78次`called_strike`、23次`swinging_strike`、31次`foul`、16次`hit_into_play`和1次`foul_bunt`组成；分母是288个打席的第一球。
- `Zone`指`zone`取1至9；区外球指`zone`非空且不在1至9。本冻结样本中541球进区、699球在区外，两者合计1,240球。
- `Chase`指区外球同时属于`Swing`。因此追打率分母是699个区外球，不是总投球数或总挥棒数。

[[COLWEIGHTS:1.0,1.65,1.6,2.3]]
| 指标 | 本样本计算 | 数值 | 主要落盘位置 |
| --- | --- | --- | --- |
| K% | 80 K / 288 BF | 27.8% | `analysis_summary.json`；跨联盟outcomes表 |
| BB% | 42 BB / 288 BF | 14.6% | `analysis_summary.json`；跨联盟outcomes表 |
| K-BB% | (80−42) / 288 BF | 13.2% | `npb_2025_vs_mlb_2026_outcomes.csv`；`analysis_summary.json`没有该字段 |
| Zone% | 541 / 1,240 | 43.6% | 总览、角色、球种、侧别、球数和轮次表 |
| 首球好球率 | 149 / 288 | 51.7% | 总览及角色表 |
| Whiff% | 175次Whiff / 542次Swing | 32.3% | 总览、角色、球种和侧别表 |
| Chase% | 190次Chase / 699个区外球 | 27.2% | 总览、角色和侧别表 |
| Usage% | 某球种球数 / 1,240 | 见球种表 | `mlb_pitch_type_summary.csv` |
| 重算RV/100 | Σ`delta_pitcher_run_exp` / 球数 × 100 | 分组计算 | 球种、侧别和球数表；正值对投手有利 |

角色由StatsAPI逐场记录确定：当场`gamesStarted=1`记为先发，其余出场记为牛棚。打者侧别使用`stand`；球数分组使用投球前的`balls`和`strikes`；面对打线轮次只在先发场次内按`n_thruorder_pitcher`分组。角色、侧别、球数和轮次比较都是观察性描述。角色表中的Zone、首球、Whiff和Chase另报Wilson 95%区间，小样本不会因给出区间而变成稳定估计。

`qa/data_reconciliation.csv`把1,240个带标签投球、80次三振、42次保送和17场比赛分别与Savant Arsenal或StatsAPI核对，四项差值均为0。差值为0只说明数据闭合，不表示研究结论已经得到因果验证。

[[PAGEBREAK]]

## 四、跨联盟字段边界

Expected Statistics文件在当前脚本中只提供MLB xERA（4.89）。MLB ERA由StatsAPI的自责分和194个出局数重算；K%和BB%也来自StatsAPI。不能把Expected文件笼统写成ERA、K%和BB%的共同来源。

NPB 2025年的K%、BB%和K-BB%来自冻结的NPB Basement高级投球表。NPB官方处理表中可核对到ERA 1.92，但`analyze.py`目前在跨联盟outcomes表内直接写入常数`1.92`，没有在运行时读取该CSV字段。当前冻结值彼此一致；若参考年份或数据窗口变化，NPB ERA必须单独人工核对，不能假定刷新后会自动改动。

### 4.1 球种标签与价值口径

NPB Basement与Statcast的球种标签、识别模型和比赛环境不同，CH与FS不能视为跨联盟一一对应。为检查结论是否只由标签迁移造成，另把CH和FS合并核对：NPB 2025为12.67%+4.37%=17.04%（17.0%），MLB 2026为2.34%+3.39%=5.73%（5.7%）。合并后该类球的使用占比仍下降，但这只是口径稳健性核对，不能证明两边每一球属于同一种球，也不能据此作因果解释。NPB的xPV/100与MLB的Run Value/100定义不同，只能在各自联盟内部解释，不作同尺度相减。

## 五、数据更新的分段门禁

联网刷新命令为：

[[EQUATION:python scripts/run_pipeline.py --refresh-data]]

该命令会替换raw快照和来源清单，随后重跑分析、仓库报告与完整性检查。它不会自动修改本文件等`.submission_revision_work/sources`下的静态Markdown，也不会自动改写已经生成的提交版Word。因此，更新不能止于命令成功。

[[COLWEIGHTS:0.9,2.7,2.4]]
| 阶段 | 必做检查 | 未通过时的处理 |
| --- | --- | --- |
| 1　确定窗口 | 修改配置中的截止日，说明为何更新，并保留旧版本哈希或Git提交 | 截止日和用途不清，不刷新 |
| 2　刷新raw | 显式运行`--refresh-data`；核对17项预期来源、URL、时间、哈希、Statcast球员ID和日期范围 | 来源缺失、网页结构变化或校验失败，停止发布 |
| 3　重算与对账 | 完成`analyze.py`、`build_reports.py`、`verify_project.py`和测试；检查四项对账差值、缺失球种、`zone`缺失及各指标新分母 | 任何差值或异常未解释，不进入文档阶段 |
| 4　人工更新静态材料 | 逐项修改本稿的截止日、样本数、149/288等分母、K-BB落盘位置、CH+FS核对、NPB ERA常数和版本号，再重新生成Word | 不允许只替换正文中的少数赛季数字 |
| 5　提交验收 | 比较新旧结果，检查表图与分页，确认Word、仓库输出和来源清单使用同一窗口 | 三处版本不一致，不替换提交包 |
