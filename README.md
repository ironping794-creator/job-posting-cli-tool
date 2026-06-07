# Job Posting CLI Tool

[English](README.md) | [简体中文](README.zh-CN.md)

Reusable Python GUI and command-line tools for collecting, cleaning, filtering, and reporting public job postings.

This is a normal CLI package. It does not require Codex, ChatGPT, OpenAI APIs, or any AI runtime.

## What You Can Do

- Use a beginner-friendly desktop GUI for CSV cleaning and API collection.
- Collect paginated public JSON APIs with polite delays and capture metadata.
- Clean CSV exports with English and Chinese column aliases.
- Normalize salary ranges, city text, keyword matches, and duplicate rows.
- Export CSV, formatted XLSX, JSON, and Markdown distribution reports.
- Run from a shell, scheduler, CI job, or any Python automation.

## Install

Clone the repository, enter the project folder, and install it in editable mode:

```bash
git clone https://github.com/ironping794-creator/job-posting-cli-tool.git
cd job-posting-cli-tool
python -m pip install -e .
```

Check that the CLI is available:

```bash
job-postings --help
job-postings-gui
job-postings collect --help
job-postings clean --help
```

If you do not want to install the package, you can still run it from the source tree:

```bash
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m job_posting_cli.gui
python -m job_posting_cli.cli --help
```

On macOS or Linux, use:

```bash
PYTHONPATH=src python -m job_posting_cli.gui
PYTHONPATH=src python -m job_posting_cli.cli --help
```

## Start With The GUI

For most users, start here:

```bash
job-postings-gui
```

The desktop window has two tabs:

- `Clean CSV`: choose an input CSV, set cities, keywords, minimum salary, choose an output folder, and click `Run Clean`.
- `Collect API`: enter the API URL, method, JSON payload, JSON paths, limit, output folder, and click `Run Collect`.

Recommended first run:

1. Open `Clean CSV`.
2. Click `Browse` next to `Input CSV`.
3. Keep `Also export formatted XLSX files` enabled.
4. Fill `Cities` and `Keywords`.
5. Click `Run Clean`.
6. Click `Open Output Folder` when it finishes.

The GUI writes the same files as the CLI, so you can switch between GUI and command-line workflows at any time.

## Workflow

Use the tool in two common ways:

1. Collect records from a public paginated JSON API with `job-postings collect`.
2. Clean and filter an existing CSV export with `job-postings clean`.

You can use either command independently. For example, if a job platform already lets you export CSV/XLSX, skip collection and start with cleaning.

## Collect From A Paginated JSON API

Use `collect` when the source exposes a public JSON endpoint with page and size parameters.

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

The collector writes:

- `raw_pages.json`: full API responses for audit/debugging
- `records.json`: extracted job records
- `records.csv`: extracted records in table form
- `records.xlsx`: optional formatted workbook when `--xlsx` is passed
- `summary.json`: source URL, capture time, page count, and record count

### Collection Arguments

| Argument | Default | Description |
|---|---:|---|
| `--url` | required | JSON API endpoint |
| `--method` | `POST` | `GET` or `POST` |
| `--headers` | empty | JSON object or path to a JSON file |
| `--payload` | `{}` | JSON object or path to a JSON file |
| `--page-param` | `page` | Dotted path for the page number parameter |
| `--size-param` | `size` | Dotted path for the page size parameter |
| `--page-size` | `50` | Records per page |
| `--records-path` | `data.records` | Dotted JSON path to the records list |
| `--total-path` | `data.total` | Dotted JSON path to total record count |
| `--pages-path` | `data.pages` | Dotted JSON path to total page count |
| `--limit` | prompt/auto | `all`, `half`, or a positive integer |
| `--max-pages` | none | Hard page cap for cautious probes |
| `--delay` | `0.5` | Seconds to wait between page requests |
| `--timeout` | `30` | Request timeout in seconds |
| `--xlsx` | off | Also export `records.xlsx` |
| `--out-dir` | `outputs/collected_jobs` | Output directory |

When `--limit` is omitted in an interactive terminal, the collector probes page 1, estimates runtime, and asks whether to collect all, half, or a specific number. In scheduled or CI runs, pass `--limit all`, `--limit 200`, or `--max-pages 3`.

## Clean And Filter A CSV Export

Use `clean` when you already have a CSV file from a job platform, browser extraction, spreadsheet export, or the collector output.

```bash
job-postings clean input.csv \
  --out-dir outputs/filtered \
  --cities "上海,北京,深圳" \
  --keywords "AI,大模型,数据分析" \
  --salary-min 8000 \
  --xlsx
```

The cleaner writes:

- `cleaned_jobs.csv`: normalized and deduplicated rows
- `filtered_jobs.csv`: rows that match your filters
- `cleaned_jobs.xlsx`: optional formatted workbook when `--xlsx` is passed
- `filtered_jobs.xlsx`: optional formatted workbook when `--xlsx` is passed
- `job_distribution.md`: count summary, city distribution, keyword distribution

### Cleaning Arguments

| Argument | Default | Description |
|---|---:|---|
| `input_csv` | required | Source CSV file |
| `--out-dir` | `outputs/jobs` | Output directory |
| `--cities` | empty | Comma-separated city filter, for example `上海,北京` |
| `--keywords` | empty | Comma-separated keyword filter, for example `AI,大模型` |
| `--salary-min` | none | Minimum salary threshold |
| `--xlsx` | off | Also export formatted XLSX workbooks |

## Recognized Columns

Target fields are:

`title`, `company`, `city`, `salary`, `job_type`, `requirements`, `publish_time`, `detail_url`, `source`

Common Chinese aliases are mapped automatically, including:

`职位名称`, `公司名称`, `工作地点`, `薪资待遇`, `岗位要求`, `发布时间`, `详情链接`

The cleaner preserves normalized fields such as `salary_min`, `salary_max`, `salary_unit`, `matched_keywords`, `is_target_city`, `is_salary_known`, and `dedupe_key`.

## Examples

Launch the GUI:

```bash
job-postings-gui
```

Clean Shanghai and Beijing AI-related roles with a minimum salary of 10,000:

```bash
job-postings clean jobs.csv --cities "上海,北京" --keywords "AI,大模型" --salary-min 10000 --xlsx
```

Probe only the first three pages of an API:

```bash
job-postings collect --url "https://example.com/api/jobs" --method GET --max-pages 3 --delay 1 --out-dir outputs/probe
```

Collect exactly 200 records:

```bash
job-postings collect --url "https://example.com/api/jobs" --limit 200 --out-dir outputs/top-200
```

## Troubleshooting

- If `job-postings` is not found, run `python -m pip install -e .` again from the repository root.
- If CSV text looks garbled in Excel, open the generated CSV with UTF-8 encoding or use `--xlsx`.
- If the API total count is unknown, pass `--limit NUMBER` or `--max-pages NUMBER`.
- If the API requires cookies or headers, pass `--headers headers.json`.
- If salary parsing is imperfect, keep the original `salary` column and review `salary_min` / `salary_max` before making decisions.

## Test

```bash
python -m pip install -e .
python -c "import sys, unittest; sys.path.insert(0, 'src'); result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests')); sys.exit(0 if result.wasSuccessful() else 1)"
```

## Responsible Use

Prefer official/public APIs, exported CSV/XLSX files, and pages you are authorized to access. Do not collect private personal data beyond what is necessary for job-search analysis.
