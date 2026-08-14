# 复现与质量保证报告

生成日期：2026-08-14（Asia/Shanghai）  
冻结数据截止日：2026-08-12  
主分支：`main`

## 环境

- Windows，Python 3.12.13
- numpy 2.3.5；pandas 3.0.1；Pillow 12.3.0
- python-docx 1.2.0；lxml 6.1.1；pypdf 6.10.0
- Word 桌面版用于 DOCX→PDF 渲染；Poppler `pdftoppm` 用于 PDF→PNG 逐页检查

## 运行顺序

```powershell
python scripts/fetch_data.py
python scripts/analyze.py
python scripts/build_reports.py
python scripts/verify_project.py
```

若只需从冻结的原始快照复现结果，应跳过 `fetch_data.py`，避免动态网页与下载时间更新：

```powershell
python scripts/analyze.py
python scripts/build_reports.py
python scripts/verify_project.py
```

## 数据与计算校验

`qa/data_reconciliation.csv` 的四项差值均为 0：

| 校验 | 逐球/计算值 | 官方参考 | 差值 |
|---|---:|---:|---:|
| 有球种标签的 Statcast 投球 | 1,240 | 1,240 | 0 |
| 三振 | 80 | 80 | 0 |
| 保送 | 42 | 42 | 0 |
| 比赛 | 17 | 17 | 0 |

说明：Statcast 将一次事件编码为 `strikeout_double_play`；分析脚本按 MLB 官方口径将其计入三振。原始 Statcast 共 1,241 行，另 1 行是无球种标签的自动坏球，不进入球种分析。

原始来源清单含 17 个文件；`verify_project.py` 逐一重算 SHA-256，与 `data/raw/source_manifest.csv` 全部一致。最终研究文件的哈希见 `qa/artifact_manifest.csv`。

## 文档结构与视觉 QA

- 正式稿：A4（11906×16838 twips），2 页；样式中包含 Microsoft YaHei；“结论先行”首段全文加粗。
- 完整底稿：A4，7 页；样式中包含 Microsoft YaHei。
- 逐页检查范围：正式稿 2/2 页、完整底稿 7/7 页。
- 结果：未发现截断文字、重叠对象、破裂表格、异常分页或明显字体替换。
- 图表：两张 PNG 均已按原始分辨率检查，标签、图例、小样本警告和正负方向可读。

打包的 `render_docx.py` 在本机第一次运行因系统未安装 LibreOffice 而找不到 `soffice`。随后使用已安装的 Microsoft Word 隐藏 COM 会话导出 PDF，再用同一 Poppler 路径生成 PNG；该替代链路不修改 DOCX 内容。

## 推断边界审计

- 没有把牛棚前后观察性差异写成因果效应；23 个牛棚打席报告 Wilson 区间与小样本警告。
- 没有把 29 球的 MLB 变速球表面结果视作真实能力；建议来自 NPB 成熟证据、使用率下降和速度差变化的联合证据。
- 没有直接相减 NPB xPV/100 与 MLB Run Value/100；只比较各自在本联盟中的方向。
- 没有用 ERA 单独判断角色；返回先发规则绑定健康、控球、球种质量与负荷。
- 任何右臂疲劳复发均优先于表现门槛。

## Git 审计

- `67095f9 chore: initialize auditable Imai research project`
- `e2dcd1c feat: add reconciled Imai analysis and diagnostic figures`
- 远程：`https://github.com/youth-flow/MLB-Analytics.git`

最终报告与 QA 将作为第三个阶段性提交。前两次推送分别因无法连接 GitHub 443 端口和连接重置失败；这不影响本地历史和远程绑定，最终节点继续重试并保留结果。
