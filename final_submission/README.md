# 最终提交两份

更新于 2026-09-11。本次提交只使用本目录的两个 Word 文件：

- `实习报告_杨炎新_15页.docx`：正常 A4、12pt 宋体正文，共 15 页。以 MLB 课程项目为主，结合已完整完成的港科大 IEDA 暑研；含两张新图、四张手稿及适量数据图表。
- `蒋总汇总_今井达也MLB调整建议_2页.docx`：两页 MLB 判断与调整建议，不含港科暑研、不附底稿。

两份文件已在 Microsoft Word 中重新分页，并检查全部 17 页。它们替代本次任务中的历史报告和蒋总候选稿；已提交的第一、二周周记未改动。

`_source/` 是迁移备份，不需要提交给老师或蒋总。它保存正文、构建与检查脚本、原图、最终渲染以及绑定文件哈希的视觉检查记录。个人姓名、学号和照片按此前本人明确要求随项目备份；不要将其误认为匿名公开报告。

## 修改与重建

只查看 Word 无需安装开发环境。若需重建，安装 Python、python-docx、Pillow、pypdf、lxml，并在 Windows 中保留宋体、黑体和微软雅黑。从仓库根目录执行：

```powershell
python final_submission/_source/build_final_two.py
```

该命令会重写本目录两个 Word 文件。修改前请先保留旧版。Word 页数受字体及渲染环境影响，重建后需重新检查，不能沿用旧记录。

如有 Microsoft Word 与 Poppler，可导出最终检查页：

```powershell
powershell -File final_submission/_source/render_word.ps1 -Round final -PdftoppmPath C:/path/to/pdftoppm.exe
python final_submission/_source/verify_final.py
```

检查脚本仅验证页数、结构、图片和哈希；视觉合格须逐页查看并重新记录。文稿使用 2026-08-12 冻结数据，重建文稿不等于刷新 MLB 赛季数据。
