# Job Posting CLI Tool

Reusable Python command-line tools for collecting, cleaning, filtering, and reporting public job postings.

This is a normal CLI package. It does not require Codex, ChatGPT, OpenAI APIs, or any AI runtime.

## Features

- Collect paginated public JSON APIs with polite delays and capture metadata.
- Clean CSV exports with English and Chinese column aliases.
- Normalize salary ranges, city text, keyword matches, and duplicate rows.
- Export CSV, formatted XLSX, JSON, and Markdown distribution reports.
- Run from a shell, scheduler, CI job, or any Python automation.

## Install

```bash
python -m pip install -e .
```

Then run:

```bash
job-postings --help
job-postings collect --help
job-postings clean --help
```

## Collect From A Paginated JSON API

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

- `raw_pages.json`
- `records.json`
- `records.csv`
- `records.xlsx` when `--xlsx` is passed
- `summary.json`

When `--limit` is omitted in an interactive terminal, the collector probes page 1, estimates runtime, and asks whether to collect all, half, or a specific number. In scheduled or CI runs, pass `--limit all`, `--limit 200`, or `--max-pages 3`.

## Clean And Filter A CSV Export

```bash
job-postings clean input.csv \
  --out-dir outputs/filtered \
  --cities "上海,北京,深圳" \
  --keywords "AI,大模型,数据分析" \
  --salary-min 8000 \
  --xlsx
```

The cleaner writes:

- `cleaned_jobs.csv`
- `filtered_jobs.csv`
- `cleaned_jobs.xlsx` and `filtered_jobs.xlsx` when `--xlsx` is passed
- `job_distribution.md`

## Recognized Columns

Target fields are:

`title`, `company`, `city`, `salary`, `job_type`, `requirements`, `publish_time`, `detail_url`, `source`

Common Chinese aliases are mapped automatically, including `职位名称`, `公司名称`, `工作地点`, `薪资待遇`, `岗位要求`, `发布时间`, and `详情链接`.

## Test

```bash
python -m pip install -e .
python -m pytest
```

## Responsible Use

Prefer official/public APIs, exported CSV/XLSX files, and pages you are authorized to access. Do not collect private personal data beyond what is necessary for job-search analysis.
