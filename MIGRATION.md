# 换电脑恢复项目

在新电脑安装 Git 后执行：

```powershell
git clone https://github.com/youth-flow/MLB-Analytics.git
cd MLB-Analytics
```

不使用 Git 时，可在 GitHub 仓库页面选择 **Code → Download ZIP** 下载。

原始数据、处理后的数据、代码、图表、研究记录和公开 Word 报告均随仓库保存。离线分析使用的数据截至 2026-08-12，无需重新下载数据。

本次迁移额外保存 `qa/rendered/` 和 `qa/local_visual_report.json`，保留旧电脑上的 PDF、逐页预览与检查记录。`full`、`full_final`、`full_final2` 是历史排版轮次；这些记录保留原貌，不代表新电脑已经完成版面检查。需要修改报告时，按 `docs/reproducibility.md` 重新检查。

运行分析需要 Python 3.12：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/run_pipeline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

只查看 Word、PDF 和数据文件时不需要安装 Python。Python 缓存和本机虚拟环境可重新生成，不随迁移上传。

## 全部课程与提交材料备份

经本人确认，包含姓名、学号及港科暑研内容的提交材料也已收入 `workspace_backup/`：

- `workspace_backup/提交材料/`：四周实习记录、实习报告、蒋总两页汇总、四份底稿及提交文件哈希清单。正式提交请取此目录中的文件。
- `workspace_backup/` 根目录：课程 PDF、实习要求及四份学校表格原文件。
- `workspace_backup/.submission_revision_work/`：文稿源文件、自编生成与核查脚本、历史版本、图表、PDF 和逐页排版预览。此处保留了工作过程，可能有过期候选稿；正式版本以上一项目录为准。
- `workspace_backup/BACKUP_MANIFEST.json`：每个备份文件的相对路径、字节数和 SHA-256，以及未上传的软件运行库与缓存清单。

备份保留文件原始字节，不转换 Word、不重排版。约 1.9 GB 的 LibreOffice 安装包及第三方软件运行库、安装日志和 Python 缓存未上传；自编渲染脚本和已有渲染结果均已保存。新电脑可重新安装 Microsoft Word 或 LibreOffice。

若继续运行旧文稿脚本，可把 `workspace_backup/` 中的内容复制到新电脑的课程文件夹，再把本仓库放在该文件夹的 `MLB-Analytics/` 子目录，恢复原先的相邻目录结构。部分旧脚本保留旧电脑绝对路径，运行前应改为新电脑对应路径；归档文件保留原貌。直接查看和提交现有 Word 不受这些路径影响。
