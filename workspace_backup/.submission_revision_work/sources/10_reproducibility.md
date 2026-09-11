---
filename: 底稿04_MLB复现与交付核查说明.docx
kind: draft_short
title: 底稿04　复现与交付核查说明
subtitle: 环境、冻结复现、证据分层与提交验收
meta_line: 杨炎新（3230102355）　｜　数据截止：2026年8月12日　｜　最终版本：9c8033d
---

## 一、说明范围

本说明只回答两件事：冻结项目怎样运行，以及交付物怎样验收。数据来源、指标口径和四项对账的具体数值见底稿02；研究判断如何经过证据检验和反证而改变见底稿03。本稿不重复分析结论和推断限制，以免同一事实分散在多份材料中后出现版本差异。

本轮对应仓库commit为`9c8033d181b5077e29aa67c8606e49f8db4ac842`。核查时本地`main`、`origin/main`与该commit一致，工作区无未提交改动；GitHub Actions run `31870800186`已在同一commit上运行成功。远程CI证明的是仓库冻结流程和测试在规定环境中通过，不代替最终提交Word的内容、页数和签章检查。

## 二、环境建立与冻结复现

参考验收环境为Windows、Python 3.12.13。`requirements.txt`已固定numpy 2.3.5、pandas 3.0.1、Pillow 12.3.0、python-docx 1.2.0、lxml 6.1.1和pypdf 6.10.0。进入`MLB-Analytics`目录后，先建立独立环境：

[[EQUATION:py -3.12 -m venv .venv]]

[[EQUATION:.\.venv\Scripts\python.exe -m pip install --upgrade pip]]

[[EQUATION:.\.venv\Scripts\python.exe -m pip install -r requirements.txt]]

冻结复现不访问网络，也不覆盖`data/raw`。执行：

[[EQUATION:.\.venv\Scripts\python.exe scripts\run_pipeline.py]]

[[EQUATION:.\.venv\Scripts\python.exe -m unittest discover -s tests -v]]

第一条命令依次运行`analyze.py`、`build_reports.py`和`verify_project.py`；第二条命令运行测试。当前冻结版本中，流水线返回0，12项测试通过，`qa/integrity_report.json`中的`overall_pass`为`true`。

这里需要区分“来源档案”和“本次计算输入”。`data/raw/source_manifest.csv`与`.json`登记17份原始来源快照；校验程序会逐项核对文件字节数和精确SHA-256，并检查两份manifest记录一致。这17份文件共同构成来源留档，但不等于`analyze.py`会逐一读取它们。

当前分析脚本直接读取4份raw文件：

- `mlb_statsapi_game_log_2026.json`；
- `statcast_imai_2026.csv`；
- `savant_pitch_arsenal_stats_2026.csv`；
- `savant_expected_stats_pitchers_2026.csv`。

脚本还直接依赖两份已经冻结的NPB处理表：

- `data/processed/npb_basement_imai_advanced_pitching_2023_2025.csv`；
- `data/processed/npb_basement_imai_pitch_values_2023_2025.csv`。

因此，现有离线流程能够从上述输入重算MLB分析表、图和报告，但不是把17份raw全部重新加工成所有processed文件的完整链条。复现时应保留仓库中的冻结processed目录；17份raw的作用是来源追溯、哈希核查以及今后刷新时的留档。

## 三、刷新数据时的分段检查

`python scripts/run_pipeline.py --refresh-data`会依次联网抓取、分析、构建报告并校验，但它不能单独作为“新版本已经完成”的凭据。原因是`build_reports.py`读取的是`reports/sources/formal_manuscript.md`和`reports/sources/full_analysis_draft.md`两份静态文字源；数据更新后，正文中的数字不会自动改写。为了避免“表已更新、文字仍是旧值”，建立新冻结点时按下列顺序执行：

1. 新建分支或工作副本，先在`config/analysis.json`写明新的截止日期与球员标识。
2. 运行`python scripts/fetch_data.py --refresh-data`，保存新raw和来源manifest。
3. 检查来源URL、抓取时间、球员ID、文件字节数、行数和SHA-256，确认下载窗口没有混入旧文件。
4. 运行`python scripts/analyze.py`，再逐项查看`data/processed`和`outputs/figures`的差异。
5. 根据新结果人工更新两份报告Markdown，逐一核对标题、摘要、正文、表格和图注中的核心数字。
6. 运行`python scripts/build_reports.py`生成仓库公开Word。
7. 运行`python scripts/verify_project.py`和全部单元测试；任何一项失败都停止发布。
8. 另行渲染Word，逐页检查截断、重叠、表图清晰度、页码和孤立标题。
9. 只有上述检查全部完成，才更新截止日、清单和版本号并提交新的冻结commit。

这样把“抓取—计算—文字更新—自动校验—视觉验收”分开留痕，能够明确错误发生在哪一段，也避免把一次能运行的命令误当成完整交付。

## 四、自动校验能证明什么

自动校验的范围需要按脚本实际能力解释。

第一，公开范围隐私扫描本轮共读取24份可扫描文件，只匹配邮箱、中国大陆手机号、10位数字学号和`C:\Users\...`本机路径四类模式。对于DOCX，程序只读取`word/document.xml`和`docProps/core.xml`，不覆盖页眉、批注、嵌入媒体等全部部件，也不识别人名。因此准确结论是“在规定的24份文件和四类规则中未发现匹配项”；姓名、单位、学号与签章位置仍需人工核对。

第二，`qa/artifact_manifest.csv`当前登记45项受控产物，并不是全仓库文件清单。其范围包括配置、研究记录、processed数据、最终图、报告文本与公开Word、脚本、测试、工作流以及指定根文件；`data/raw`、本地渲染目录、缓存和若干临时QA文件不在其中。清单也采用三种摘要口径：文本先统一换行为LF后计算`text-lf-sha256-v1`，DOCX按压缩包成员名称和内容计算`zip-content-sha256-v1`并忽略ZIP时间戳，其余二进制才使用精确文件字节的`file-sha256-v1`。所以45项中的`sha256`字段不能一概解释为原文件逐字节哈希。raw的精确哈希以来源manifest为准，最终提交Word的精确文件SHA-256以提交目录中的`提交文件清单_SHA256.txt`为准。

第三，仓库默认不保存`qa/rendered`和`qa/local_visual_report.json`等本地渲染缓存。clean clone可通过冻结流水线，但直接运行`python scripts/verify_project.py --require-visual`时没有这些PDF，不能得到可提交状态。仓库中的`qa/visual_review_receipt.json`记录过一次LibreOffice 26.2.5.2、150 dpi的人工逐页检查：两页决策稿2页，仓库版完整分析底稿10页。该收据虽然写有DOCX和PDF哈希，但当前校验脚本只检查PDF能否读取、页数是否满足规则，以及收据状态是否为`reviewed`，不会把收据哈希与当前文件重新比对。因此它是一份当次本地人工检查记录，不是与当前文件自动绑定的密码学门禁。

## 五、三类证据与验收责任

[[COLWEIGHTS:1.2,1.7,2.3,1.6,2.2]]
| 证据类别 | 核查对象 | 核查方式 | 当前结果 | 适用边界 |
| --- | --- | --- | --- | --- |
| 仓库自动证据 | 17份raw来源档案 | 字节数、精确SHA-256及CSV/JSON manifest一致性 | 通过 | 证明档案未变，不表示17份均被分析脚本读取 |
| 仓库自动证据 | 数据、核心指标与公开Word结构 | 四项数据对账、冻结数字断言、A4/字体/图片等结构检查 | 通过；详细对账见底稿02 | 结构通过不等于已逐页看过版面 |
| 仓库自动证据 | 流程与测试 | 离线流水线、12项测试、Windows远程CI | 通过 | 只对应commit `9c8033d` |
| 仓库自动证据 | 公开范围隐私与45项产物 | 四类正则扫描；按`digest_kind`生成确定顺序清单 | 通过 | 不扫描人名，不是全仓库逐字节清单 |
| 本地人工视觉证据 | 仓库两份公开Word | LibreOffice渲染为PDF/PNG后逐页查看并留收据 | 2页和10页已检查 | clean clone无缓存；脚本不校验收据哈希绑定 |
| 最终提交证据 | 本次五份MLB提交Word | Microsoft Word原生打开、渲染并逐页检查；另记页数和文件SHA-256 | 由提交包清单记录 | 与仓库公开Word的LibreOffice收据分开管理 |

默认运行`verify_project.py`后，`overall_pass=true`而`submission_ready=false`是预期状态：前者表示离线数据、代码和文档结构门禁通过，后者还要求本机已具备渲染文件和明确的人工审阅记录。不能为了得到`submission_ready=true`而复制旧缓存或只补写一条“已审阅”状态。

## 六、最终交付检查

正式提交前按以下顺序收口：先确认冻结commit和数据截止日；再运行离线流水线与12项测试；随后在Microsoft Word中打开五份提交材料，逐页检查截断、重叠、异常空白、表图可读性、页码和孤立标题；最后人工核对姓名、学号、单位、日期、需签字盖章的位置。学校表单或单位签章属于人工责任，不由代码自动填写或推断。

按“蒋总两页、底稿01—04”顺序，页数为2、8、4、3、3页；精确SHA-256见同目录清单，任何改动后须重新逐页检查并重算清单。
