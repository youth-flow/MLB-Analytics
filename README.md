# MLB Analytics：今井达也调整决策研究

本项目回答课程题目二：**今井达也在 MLB 应该如何调整和发展？**

研究问题：今井达也 2026 年在 MLB 的困难主要来自球威、控球、配球结构还是先发负荷？休斯顿太空人应如何安排他的短期角色、球种组合和重返先发门槛？

## 冻结范围

- MLB 主分析窗口：2026-03-29 至 2026-08-12（含首尾日期）
- NPB 基准：2018-2025，重点解释 2023-2025 成熟期
- MLBAM pitcher id：837227
- 原始数据只读留存；清洗和衍生数据写入 `data/processed/`
- 所有主张必须能回溯到来源、代码或明确标注的推断

## 目录

- `01_research/`：研究方案、假设迭代、来源与 AI 协作记录
- `data/raw/`：原始下载快照及哈希清单
- `data/processed/`：分析用表
- `scripts/`：数据获取、分析、作图和报告生成代码
- `outputs/figures/`：最终图表
- `reports/`：两页正式文稿及完整底稿
- `qa/`：复现、完整性和文档渲染检查结果

## 复现

使用 Codex 工作区附带的 Python 运行：

```powershell
python scripts/fetch_data.py
python scripts/analyze.py
python scripts/build_reports.py
python scripts/verify_project.py
```

具体运行命令、环境和文件哈希见 `qa/reproducibility_report.md`。

## 最终提交物

- `reports/今井达也_MLB调整决策_正式文稿.docx`：按课程要求制作的 A4 两页正式文稿，第一段为加粗结论。
- `reports/今井达也_MLB调整决策_完整分析底稿.docx`：7 页完整底稿，含来源、方法、计算、四轮分析循环、反证、限制和 AI 使用说明。
- `reports/formal_manuscript.md`、`reports/full_analysis_draft.md`：可审查的纯文本版本。
- `qa/integrity_report.json`、`qa/reproducibility_report.md`：数据闭合、哈希、文档结构和逐页渲染检查。

## 核心结论

今井的三振与挥空能力仍在，主要瓶颈是 BB%翻倍、首球和好球区控制下降，以及 NPB 2025 已成熟变速球在 MLB 的使用率与速度分层消失。两次牛棚登板只提供积极的小样本过程信号；建议把多局牛棚作为短期校准环境，以预先声明的控球、球种和负荷门槛决定何时重返先发。
