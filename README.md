# 招聘岗位 GUI 工具

[简体中文](README.md) | [English](README.en.md)

这是一个 GUI 优先的 Python 工具，用来采集、清洗、筛选和汇总公开招聘岗位数据，同时保留命令行入口方便自动化。

它是普通 Python 包，运行时不依赖 Codex、ChatGPT、OpenAI API 或任何 AI 能力。

## GUI 效果图

![GUI 效果图](docs/assets/gui-url-export.png)

## 能做什么

- 提供中文桌面 GUI，适合先从粘贴网址、点选文件和填写表单开始。
- 支持把可访问的招聘页面导出为 Excel，并可按城市、岗位/关键词、发布日期范围筛选和关键词高亮。
- 从公开分页 JSON API 采集岗位数据，并记录采集元信息。
- 清洗 CSV 导出文件，自动识别常见中英文列名。
- 规范化薪资区间、城市、关键词匹配和重复岗位。
- 导出 CSV、格式化 XLSX、JSON 和 Markdown 统计报告。
- 可在命令行、计划任务、CI 或普通 Python 自动化脚本里运行。

## 安装

克隆仓库，进入项目目录，并以可编辑模式安装：

```bash
git clone https://github.com/ironping794-creator/job-posting-gui-tool.git
cd job-posting-gui-tool
python -m pip install -e .
```

检查 GUI 和命令是否可用：

```bash
job-postings --help
job-postings-gui
job-postings url "招聘页面网址" --cities "上海,北京" --keywords "算法,AI" --published-within-days 180 --out-dir outputs/url_export
job-postings collect --help
job-postings clean --help
```

如果不想安装包，也可以直接从源码目录运行：

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m job_posting_cli.gui
python -m job_posting_cli.cli --help
```

macOS 或 Linux 使用：

```bash
PYTHONPATH=src python -m job_posting_cli.gui
PYTHONPATH=src python -m job_posting_cli.cli --help
```

## 先从 GUI 开始

大多数用户建议先运行：

```bash
job-postings-gui
```

桌面窗口里有三个标签页：

- `粘贴网址导出`：粘贴可访问的招聘页面网址，填写城市、岗位/关键词、发布日期范围筛选，一键导出 Excel。
- `清洗 CSV`：选择输入 CSV，填写城市、关键词、最低薪资，选择输出目录，然后点击 `开始清洗`。
- `接口采集`：填写接口地址、请求方法、JSON 参数、JSON 路径、采集数量、输出目录，然后点击 `开始采集`。

推荐第一次这样用：

1. 打开 `粘贴网址导出`。
2. 把招聘页面网址粘贴到 `招聘网址`。
3. 按需填写 `城市筛选`、`岗位/关键词筛选`，选择 `发布日期范围`，也可以填写高亮关键词并选择颜色。
4. 点击 `一键导出 Excel`。
5. 完成后点击 `打开输出文件夹` 查看 `.xlsx`。

GUI 和命令行生成的是同一套文件，所以可以随时在图形界面和 CLI 之间切换。

## 粘贴网址导出 Excel

如果只想要 Excel，不想配置接口参数，使用：

```bash
job-postings url "招聘页面网址" --out-dir outputs/url_export
```

也可以增加筛选：

```bash
job-postings url "招聘页面网址" --cities "上海,北京" --keywords "算法,AI" --published-within-days 180 --highlight-keywords "算法,AI" --highlight-color "#FFF2CC" --out-dir outputs/url_export
```

工具会生成 `招聘信息导出_时间戳.xlsx` 和导出摘要 JSON。如果网站需要登录授权，可在 GUI 的 `登录 Token（可选）` 中填写 token，或用命令行参数：

`--max-records` / GUI 里的 `最多导出条数` 指的是筛选前最多保留多少条原始记录，不是最终 Excel 一定会导出多少条。最终导出数量会再经过城市、关键词和发布日期范围筛选。如果数据源本身没有条数上限，就不用额外说明限制；如果数据源/API 有上限，工具会在摘要 JSON 里记录 `max_export_records` 和导出数量。

如果想在 Excel 里高亮关键词，GUI 里填写 `高亮关键词` 并点击 `选择颜色`。如果 `高亮关键词` 留空，网址导出会默认使用 `岗位/关键词筛选` 作为高亮词。命令行可使用 `--highlight-keywords` 和 `--highlight-color`，颜色支持 `#FFFF00` 或 `FFFF00` 这样的写法。

注意：粘贴网址导出不是浏览器自动爬取任意网页。需要登录、动态渲染、验证码或风控校验的招聘搜索页，通常不能直接抓取；这类情况请优先使用平台允许的导出文件，再用 `清洗 CSV` 处理，或在你有公开 JSON API 的前提下使用 `接口采集`。

```bash
job-postings url "招聘页面网址" --token "你的token" --out-dir outputs/url_export
```

## 使用流程

常见有两种用法：

1. 用 `job-postings collect` 从公开分页 JSON API 采集岗位。
2. 用 `job-postings clean` 清洗和筛选已有 CSV 文件。

这两个命令可以独立使用。如果招聘平台已经能导出 CSV/XLSX，就可以跳过采集，直接从清洗开始。

## 从分页 JSON API 采集

当数据源提供公开 JSON 接口，并通过 page / size 等参数分页时，使用 `collect`。

```bash
job-postings collect \
  --url "https://example.com/api/jobs/page-list" \
  --method POST \
  --payload '{"cityId":35}' \
  --page-param page \
  --size-param size \
  --records-path data.records \
  --total-path data.total \
  --page-size 50 \
  --limit all \
  --xlsx \
  --out-dir outputs/my-job-collection
```

采集器会输出：

- `raw_pages.json`：完整 API 响应，便于审计和调试
- `records.json`：抽取出的岗位记录
- `records.csv`：表格形式的岗位记录
- `records.xlsx`：传入 `--xlsx` 时额外生成的格式化工作簿
- `summary.json`：来源 URL、采集时间、页数、记录数等元信息

### 采集参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `--url` | 必填 | JSON API 地址 |
| `--method` | `POST` | `GET` 或 `POST` |
| `--headers` | 空 | JSON 对象，或 JSON 文件路径 |
| `--payload` | `{}` | JSON 对象，或 JSON 文件路径 |
| `--page-param` | `page` | 页码参数的点路径 |
| `--size-param` | `size` | 每页数量参数的点路径 |
| `--page-size` | `50` | 每页记录数 |
| `--records-path` | `data.records` | 岗位列表在响应 JSON 里的点路径 |
| `--total-path` | `data.total` | 总记录数在响应 JSON 里的点路径 |
| `--pages-path` | `data.pages` | 总页数在响应 JSON 里的点路径 |
| `--limit` | 交互/自动 | `all`、`half` 或正整数 |
| `--max-pages` | 无 | 谨慎探测时的最大页数 |
| `--delay` | `0.5` | 每页请求之间的等待秒数 |
| `--timeout` | `30` | 请求超时秒数 |
| `--xlsx` | 关闭 | 额外导出 `records.xlsx` |
| `--out-dir` | `outputs/collected_jobs` | 输出目录 |

如果在交互式终端里没有传 `--limit`，工具会先探测第一页，估算耗时，然后询问采集全部、一半还是指定数量。在计划任务或 CI 中，建议显式传入 `--limit all`、`--limit 200` 或 `--max-pages 3`。

## 清洗和筛选 CSV

当你已经有招聘平台导出的 CSV、浏览器抓取结果、表格导出结果，或采集器生成的 CSV 时，使用 `clean`。

```bash
job-postings clean input.csv \
  --out-dir outputs/filtered \
  --cities "上海,北京,深圳" \
  --keywords "AI,大模型,数据分析" \
  --salary-min 8000 \
  --xlsx
```

清洗器会输出：

- `cleaned_jobs.csv`：规范化和去重后的完整数据
- `filtered_jobs.csv`：符合筛选条件的岗位
- `cleaned_jobs.xlsx`：传入 `--xlsx` 时额外生成的格式化工作簿
- `filtered_jobs.xlsx`：传入 `--xlsx` 时额外生成的格式化工作簿
- `job_distribution.md`：数量、城市分布、关键词分布等统计报告

### 清洗参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `input_csv` | 必填 | 输入 CSV 文件 |
| `--out-dir` | `outputs/jobs` | 输出目录 |
| `--cities` | 空 | 城市筛选，例如 `上海,北京` |
| `--keywords` | 空 | 关键词筛选，例如 `AI,大模型` |
| `--salary-min` | 无 | 最低薪资阈值 |
| `--xlsx` | 关闭 | 额外导出格式化 XLSX 工作簿 |

## 可识别字段

目标字段包括：

`title`, `company`, `city`, `salary`, `job_type`, `requirements`, `publish_time`, `detail_url`, `source`

会自动识别常见中文列名，例如：

`职位名称`, `公司名称`, `工作地点`, `薪资待遇`, `岗位要求`, `发布时间`, `详情链接`

清洗后还会保留派生字段，例如 `salary_min`、`salary_max`、`salary_unit`、`matched_keywords`、`is_target_city`、`is_salary_known`、`dedupe_key`。

## 示例

启动中文图形界面：

```bash
job-postings-gui
```

粘贴招聘页面网址直接导出 Excel，并按城市和岗位关键词筛选：

```bash
job-postings url "招聘页面网址" --cities "上海" --keywords "算法,AI" --published-within-days 30 --out-dir outputs/url_export
```

筛选上海和北京的 AI / 大模型岗位，最低薪资 10000，并导出 XLSX：

```bash
job-postings clean jobs.csv --cities "上海,北京" --keywords "AI,大模型" --salary-min 10000 --xlsx
```

只探测 API 前 3 页：

```bash
job-postings collect --url "https://example.com/api/jobs" --method GET --max-pages 3 --delay 1 --out-dir outputs/probe
```

采集 200 条记录：

```bash
job-postings collect --url "https://example.com/api/jobs" --limit 200 --out-dir outputs/top-200
```

## 常见问题

- 如果提示找不到 `job-postings`，请在仓库根目录重新运行 `python -m pip install -e .`。
- 如果 CSV 在 Excel 里乱码，建议改用 `--xlsx`，或按 UTF-8 编码打开 CSV。
- 如果 API 没有返回总数，请传 `--limit 数字` 或 `--max-pages 数字`。
- 如果 API 需要 cookie 或请求头，请把请求头保存成 JSON 文件，并通过 `--headers headers.json` 传入。
- 如果薪资解析不完美，请以原始 `salary` 列为准，并人工复核 `salary_min` / `salary_max`。

## 测试

```bash
python -m pip install -e .
python -c "import sys, unittest; sys.path.insert(0, 'src'); result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests')); sys.exit(0 if result.wasSuccessful() else 1)"
```

## 合规使用

优先使用官方/公开 API、平台导出的 CSV/XLSX 文件，以及你有权限访问的页面。不要采集超出求职分析必要范围的私人个人信息。
