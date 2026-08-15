# 复现与质量保证

## 冻结研究合同

机器可读研究配置位于 `config/analysis.json`。当前合同冻结：

- MLB：2026-03-29 至 2026-08-12；
- NPB：2018—2025，主要比较基准为 2025；
- MLBAM pitcher id：837227；
- 默认运行模式：读取仓库内 raw 快照的离线复现；
- 联网更新：只能通过显式 `--refresh-data` 启动。

配置中的决策门槛是预先声明的行动规则，不是由很小的牛棚样本估出的能力真值。

## 参考环境

项目以 Windows、Python 3.12.13 完成最终复核，依赖锁定为：

| 包 | 版本 |
|---|---:|
| numpy | 2.3.5 |
| pandas | 3.0.1 |
| Pillow | 12.3.0 |
| python-docx | 1.2.0 |
| lxml | 6.1.1 |
| pypdf | 6.10.0 |

Python 版本约束也记录在 `.python-version` 与 `pyproject.toml`。

## 安装

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS / Linux：

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

后续命令中的 `python` 应替换为相应虚拟环境解释器，或先激活该环境。

## 路径一：冻结快照离线复现

此路径不调用下载脚本：

```powershell
python scripts/run_pipeline.py
python -m unittest discover -s tests -v
```

若需要定位某个阶段，也可依次直接运行 `scripts/analyze.py`、`scripts/build_reports.py` 和 `scripts/verify_project.py`。

预期核心闭合值：

| 校验 | 冻结值 |
|---|---:|
| 比赛 | 17 |
| 有球种标签的 Statcast 投球 | 1,240 |
| 三振 | 80 |
| 保送 | 42 |

`scripts/analyze.py` 会重新生成 processed 表、两张图、分析摘要、数据对账表和分析循环结果。

## 路径二：显式建立新冻结点

只有研究者明确决定刷新时才运行：

```powershell
python scripts/run_pipeline.py --refresh-data
```

刷新前应先修改 `config/analysis.json` 的截止日期。刷新会覆盖 raw 快照及 manifest，因此应检查来源状态、下载字节数、日期范围和球员 ID，再把新冻结点作为独立提交审阅。

## 自动完整性检查

```powershell
python scripts/verify_project.py
```

自动检查负责：

- raw 快照与 source manifest 的 SHA-256 一致性；
- Statcast 与官方比赛日志的数据闭合；
- DOCX 的 A4 结构、关键标题和所需样式；
- 研究交付物 manifest 的重建。

GitHub Actions 在 Windows/Python 3.12 上运行相同的冻结离线流水线与回归测试，不执行联网刷新。
CI 明确保留仓库中已经审阅的两张确定性图表，避免云端运行器缺少中文字体时产生字体替换；本地存在微软雅黑、黑体或 Noto CJK 时，分析脚本会正常重绘图表。

## 文档渲染与人工视觉 QA

DOCX 的分页由实际文字处理软件决定。最终交付前应在目标环境中把每份 DOCX 导出为 PDF，再把 PDF 渲染为逐页 PNG，检查：

- 截断、重叠或异常留白；
- 表格跨页和列宽；
- 图题、图例和小样本提示；
- 字体替换、乱码与异常分页；
- 正式稿是否保持课程要求的页数。

参考环境使用 Microsoft Word 导出 PDF、Poppler `pdftoppm` 生成逐页 PNG。LibreOffice 可作为跨平台替代，但分页结果可能不同，必须重新人工审阅。

人工视觉结论不是可以由布尔常量替代的自动检测；应记录审阅日期、软件版本、检查页数和审阅者，并与自动完整性结果分开保存。`qa/rendered/` 属于可再生本地中间物，默认不进入 Git。

默认 `verify_project.py` 有意不读取这些本地缓存，以保证 clean clone 的 `qa/integrity_report.json` 可确定性重建。准备好两份 PDF 和人工审阅收据 `qa/visual_review_receipt.json` 后，可运行：

```powershell
python scripts/verify_project.py --require-visual
```

该模式核对正式稿为 1—2 页（课程硬约束是不超过两页），并确认完整底稿 PDF 至少有一页且可读取；实际页数会写入被忽略的`qa/local_visual_report.json`。页数检查只证明分页数量，不能证明“无截断、无重叠”，这些结论必须来自真实逐页审阅。

## 推断边界

- 牛棚只有 2 场、23 个打席，角色前后差异不得解释为确定因果效应。
- MLB 变速球样本很小，建议依赖 NPB 成熟证据、使用下降和速度分层变化的联合证据。
- NPB xPV/100 与 MLB Run Value/100 不是同一量纲，只比较各自在联盟内部的方向。
- ERA 不能单独决定角色；返回先发须同时考虑健康、控球、球种质量和负荷。
- 任何右臂疲劳或伤情复发都优先于表现门槛。
