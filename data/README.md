# 数据说明

本目录把来源快照与分析派生数据分开保存。默认复现只读取冻结快照，不访问网络。

## `raw/`：冻结来源快照

`raw/` 保存研究截止日之前下载的网页、接口响应和 CSV 快照。每个来源的 URL、UTC 抓取时间、字节数、内容类型和 SHA-256 记录在：

- `raw/source_manifest.csv`
- `raw/source_manifest.json`

这些文件是字节级证据，Git 不应对其换行进行自动转换。除显式建立新的冻结点外，不应手工编辑或覆盖。

主要来源：

| 来源 | 主要用途 |
|---|---|
| MLB StatsAPI | 官方逐场投球日志与角色信息 |
| Baseball Savant / Statcast | 逐球、预期结果、球种与移动数据 |
| NPB 官方 | NPB 赛季投球记录 |
| NPB Basement | 2023—2025 球种价值与纪律指标 |
| MLB.com | 角色调整、健康和球队语境的新闻材料 |

## `processed/`：分析派生数据

`processed/` 由脚本从冻结 raw 快照生成，包括：

- MLB 逐场日志与按角色、球种、左右打、球数和打线轮次的汇总；
- NPB 赛季与球种基准；
- NPB 2025 与 MLB 2026 的结果及球种结构对照；
- 供报告生成器读取的 `analysis_summary.json`。

派生文件允许通过脚本重建，不应直接手工修数。若发现错误，应修正代码或来源映射，并重新运行完整流程。

## 冻结与刷新规则

离线复现：

```powershell
python scripts/analyze.py
```

联网刷新必须显式执行：

```powershell
python scripts/fetch_data.py --refresh-data
```

刷新会覆盖 raw 快照和来源 manifest，并可能改变 processed 数据及研究结论。建立新冻结点时，应同步更新 `config/analysis.json`、重跑分析与质量校验，并在单独提交中记录差异。

## 数据权利与使用限制

raw 中的第三方网页、接口响应、统计数据、名称与标识并非本项目原创，其权利仍归 MLB、Baseball Savant、NPB、NPB Basement 及相应发布者。本仓库保存快照仅用于课程研究、核查与复现，不对第三方内容授予许可，也不保证这些材料可用于商业再分发。

根目录目前未附开源许可证；不得据此推定项目原创内容或第三方数据已经开放授权。使用者还应遵守各来源网站的条款、署名要求与适用法律。
