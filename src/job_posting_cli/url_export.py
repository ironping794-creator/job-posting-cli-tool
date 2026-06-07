from __future__ import annotations

import argparse
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import parse, request

from .xlsx import write_xlsx


OFFER_API = "https://api.gfjianli.com/api/c/resume/campusRecruitment"
OFFER_FIELDS = [
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


def export_url(url: str, out_dir: str, max_records: int = 20000, token: str = "") -> Path:
    normalized = url.strip()
    if not normalized:
        raise ValueError("请输入网址。")
    parsed = parse.urlparse(normalized)
    host = parsed.netloc.lower()
    if "offer.gfjianli.com" in host:
        return export_offer_gfjianli(normalized, Path(out_dir), max_records=max_records, token=token)
    raise ValueError("当前一键导出仅内置支持 offer.gfjianli.com。你仍然可以使用“接口采集”标签页手动配置其他公开 JSON API。")


def export_offer_gfjianli(url: str, out_dir: Path, max_records: int = 20000, token: str = "") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    query = {"limit": max_records}
    api_url = f"{OFFER_API}?{parse.urlencode(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://offer.gfjianli.com",
        "Referer": "https://offer.gfjianli.com/",
    }
    if token.strip():
        headers["token"] = token.strip()

    payload = fetch_json(api_url, headers)
    if payload.get("code") != 200 or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"Offer星球接口返回异常：{payload.get('msg') or payload}")

    data = payload["data"]
    raw_rows = data.get("list") or []
    if not isinstance(raw_rows, list):
        raise RuntimeError("Offer星球接口没有返回岗位列表。")

    rows = [normalize_offer_row(row, url) for row in raw_rows if isinstance(row, dict)]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_path = out_dir / f"offer星球_校招信息_{timestamp}.xlsx"
    write_xlsx(xlsx_path, rows, OFFER_FIELDS, "Offer星球校招")

    summary = {
        "source_url": url,
        "api_url": api_url,
        "export_time": datetime.now().isoformat(timespec="seconds"),
        "total_reported": data.get("total"),
        "rows_exported": len(rows),
        "max_records": max_records,
        "note": "If total_reported is greater than rows_exported, increase max_records or provide an authorized token.",
    }
    (out_dir / f"offer星球_导出摘要_{timestamp}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return xlsx_path


def fetch_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=120) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def normalize_offer_row(row: dict[str, Any], source_url: str) -> dict[str, str]:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paste a supported job site URL and export an Excel workbook.")
    parser.add_argument("url")
    parser.add_argument("--out-dir", default="outputs/url_export")
    parser.add_argument("--max-records", type=int, default=20000)
    parser.add_argument("--token", default="", help="Optional site token for authorized exports.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    path = export_url(args.url, args.out_dir, args.max_records, args.token)
    print(path)
