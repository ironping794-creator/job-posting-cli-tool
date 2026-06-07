from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import parse, request

from .xlsx import write_xlsx


KNOWN_SITE_API = "https://api.gfjianli.com/api/c/resume/campusRecruitment"
EXPORT_FIELDS = [
    "发布时间",
    "公司",
    "标题",
    "投递方式",
    "工作地点",
    "行业",
    "岗位",
    "信息类型",
    "备注",
    "记录ID",
    "创建时间",
    "来源网址",
]


def export_url(
    url: str,
    out_dir: str,
    max_records: int = 20000,
    token: str = "",
    cities: str = "",
    keywords: str = "",
    published_within_days: int | None = None,
) -> Path:
    normalized = url.strip()
    if not normalized:
        raise ValueError("请输入网址。")
    parsed = parse.urlparse(normalized)
    host = parsed.netloc.lower()
    if "offer.gfjianli.com" in host:
        return export_known_recruitment_site(
            normalized,
            Path(out_dir),
            max_records=max_records,
            token=token,
            cities=cities,
            keywords=keywords,
            published_within_days=published_within_days,
        )
    raise ValueError(unsupported_url_message(host))


def unsupported_url_message(host: str) -> str:
    if "zhipin.com" in host:
        return (
            "该招聘搜索页通常需要浏览器登录态、动态渲染或风控校验，不能用“粘贴网址导出”模式直接抓取。"
            "请优先使用平台允许的导出文件并在“清洗 CSV”中处理；如果你有可访问的公开 JSON API，"
            "可以在“接口采集”标签页手动配置。"
        )
    return "暂未识别该网址的数据结构。你可以使用“接口采集”标签页手动配置公开 JSON API，或先导出 CSV 后用“清洗 CSV”处理。"


def export_known_recruitment_site(
    url: str,
    out_dir: Path,
    max_records: int = 20000,
    token: str = "",
    cities: str = "",
    keywords: str = "",
    published_within_days: int | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    query = {"limit": max_records}
    api_url = f"{KNOWN_SITE_API}?{parse.urlencode(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://offer.gfjianli.com",
        "Referer": "https://offer.gfjianli.com/",
    }
    if token.strip():
        headers["token"] = token.strip()

    payload = fetch_json(api_url, headers)
    if payload.get("code") != 200 or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"网站接口返回异常：{payload.get('msg') or payload}")

    data = payload["data"]
    raw_rows = data.get("list") or []
    if not isinstance(raw_rows, list):
        raise RuntimeError("网站接口没有返回岗位列表。")

    rows = [normalize_site_row(row, url) for row in raw_rows if isinstance(row, dict)]
    rows = filter_export_rows(rows, cities, keywords, published_within_days)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_path = out_dir / f"招聘信息导出_{timestamp}.xlsx"
    write_xlsx(xlsx_path, rows, EXPORT_FIELDS, "招聘信息")

    summary = {
        "source_url": url,
        "api_url": api_url,
        "export_time": datetime.now().isoformat(timespec="seconds"),
        "total_reported": data.get("total"),
        "rows_exported": len(rows),
        "max_records": max_records,
        "scan_limit": max_records,
        "city_filter": cities,
        "keyword_filter": keywords,
        "published_within_days": published_within_days,
        "note": "scan_limit/max_records is the maximum number of source records read before filters are applied. If the data source reports more rows than the scan limit, increase it or provide authorization when appropriate.",
    }
    (out_dir / f"招聘信息导出摘要_{timestamp}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return xlsx_path


def fetch_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=120) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def normalize_site_row(row: dict[str, Any], source_url: str) -> dict[str, str]:
    return {
        "发布时间": clean_value(row.get("recordTime")),
        "公司": clean_value(row.get("company")),
        "标题": clean_value(row.get("title")),
        "投递方式": clean_value(row.get("referralMethod")),
        "工作地点": clean_value(row.get("workLocation")),
        "行业": clean_value(row.get("industry")),
        "岗位": clean_value(row.get("positions")),
        "信息类型": clean_value(row.get("infoType")),
        "备注": clean_value(row.get("remarks")),
        "记录ID": clean_value(row.get("id")),
        "创建时间": clean_value(row.get("createTime")),
        "来源网址": source_url,
    }


def clean_value(value: Any) -> str:
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def split_filter_terms(value: str) -> list[str]:
    separators = [",", "，", ";", "；", "|", "\n", "\t"]
    text = value or ""
    for separator in separators:
        text = text.replace(separator, ",")
    return [item.strip().lower() for item in text.split(",") if item.strip()]


def filter_export_rows(
    rows: list[dict[str, str]],
    cities: str = "",
    keywords: str = "",
    published_within_days: int | None = None,
) -> list[dict[str, str]]:
    city_terms = split_filter_terms(cities)
    keyword_terms = split_filter_terms(keywords)
    cutoff = None
    if published_within_days is not None:
        if published_within_days <= 0:
            raise ValueError("发布日期范围天数必须大于 0。")
        cutoff = datetime.now() - timedelta(days=published_within_days)

    if not city_terms and not keyword_terms and cutoff is None:
        return rows

    filtered: list[dict[str, str]] = []
    for row in rows:
        city_text = row.get("工作地点", "").lower()
        keyword_text = " ".join(
            [
                row.get("公司", ""),
                row.get("标题", ""),
                row.get("行业", ""),
                row.get("岗位", ""),
                row.get("备注", ""),
            ]
        ).lower()
        city_ok = not city_terms or any(term in city_text for term in city_terms)
        keyword_ok = not keyword_terms or any(term in keyword_text for term in keyword_terms)
        date_ok = cutoff is None or is_published_after(row.get("发布时间", ""), cutoff)
        if city_ok and keyword_ok and date_ok:
            filtered.append(row)
    return filtered


def is_published_after(value: str, cutoff: datetime) -> bool:
    parsed = parse_datetime(value)
    return parsed is not None and parsed >= cutoff


def parse_datetime(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    candidates = [text, text[:19], text[:10]]
    for candidate in candidates:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paste a supported job site URL and export an Excel workbook.")
    parser.add_argument("url")
    parser.add_argument("--out-dir", default="outputs/url_export")
    parser.add_argument("--max-records", type=int, default=20000, help="Maximum source records to scan before filters are applied.")
    parser.add_argument("--token", default="", help="Optional site token for authorized exports.")
    parser.add_argument("--cities", default="", help="Optional city filter, comma-separated.")
    parser.add_argument("--keywords", default="", help="Optional title/company/position keyword filter, comma-separated.")
    parser.add_argument("--published-within-days", type=int, default=None, help="Only keep records published in the last N days.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    path = export_url(
        args.url,
        args.out_dir,
        args.max_records,
        args.token,
        args.cities,
        args.keywords,
        args.published_within_days,
    )
    print(path)
