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
