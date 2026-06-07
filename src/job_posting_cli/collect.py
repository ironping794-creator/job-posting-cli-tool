from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from .xlsx import write_xlsx

Json = dict[str, Any]


def parse_json_object(value: str, label: str) -> Json:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"{label} must be a JSON object")
    return parsed


def load_json_object(value: str, label: str) -> Json:
    if not value:
        return {}
    path = Path(value)
    if path.exists():
        return parse_json_object(path.read_text(encoding="utf-8"), label)
    return parse_json_object(value, label)


def get_path(data: Any, dotted_path: str, default: Any = None) -> Any:
    if not dotted_path:
        return data
    current = data
    for part in dotted_path.split("."):
        if isinstance(current, dict):
            current = current.get(part, default)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            current = current[index] if 0 <= index < len(current) else default
        else:
            return default
    return current


def set_path(data: Json, dotted_path: str, value: Any) -> Json:
    current: Json = data
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value
    return data


def flatten_for_query(value: Json, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten_for_query(item, name))
        else:
            result[name] = item
    return result


def make_request(args: argparse.Namespace, page: int) -> Json:
    headers = dict(args.headers_obj)
    payload = json.loads(json.dumps(args.payload_obj))
    set_path(payload, args.page_param, page)
    set_path(payload, args.size_param, args.page_size)

    if args.method.upper() == "GET":
        query = parse.urlencode(flatten_for_query(payload), doseq=True)
        separator = "&" if "?" in args.url else "?"
        final_url = f"{args.url}{separator}{query}" if query else args.url
        body = None
    else:
        final_url = args.url
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json;charset=UTF-8", **headers}

    req = request.Request(final_url, data=body, headers=headers, method=args.method.upper())
    try:
        with request.urlopen(req, timeout=args.timeout) as response:
            raw = response.read()
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {final_url}: {detail[:500]}") from exc
    return json.loads(raw.decode("utf-8"))


def get_records(response: Json, records_path: str) -> list[Json]:
    records = get_path(response, records_path, [])
    if not isinstance(records, list):
        raise RuntimeError(f"Records path `{records_path}` did not resolve to a list.")
    return records


def get_int(response: Json, path: str) -> int | None:
    if not path:
        return None
    value = get_path(response, path)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_limit(limit: str | None, total: int | None) -> int | None:
    if limit is None:
        return None
    normalized = str(limit).strip().lower()
    if normalized in {"all", "全部"}:
        return total
    if normalized in {"half", "一半"}:
        return math.ceil(total / 2) if total is not None else None
    count = int(normalized)
    if count <= 0:
        raise ValueError("--limit must be positive")
    return min(count, total) if total is not None else count


def ask_limit(total: int | None, estimate_all_seconds: float) -> int | None:
    print(f"Detected total postings: {total if total is not None else 'unknown'}")
    print(f"Estimated time for all: {estimate_all_seconds:.1f}s")
    while True:
        choice = input("Collect all, half, or a number? ").strip().lower()
        if choice in {"all", "全部"}:
            return total
        if choice in {"half", "一半"}:
            return math.ceil(total / 2) if total is not None else None
        try:
            count = int(choice)
        except ValueError:
            print("Please type all, half, or a positive number.")
            continue
        if count > 0:
            return min(count, total) if total is not None else count


def record_fields(records: list[Json]) -> list[str]:
    fields: list[str] = []
    for record in records:
        if isinstance(record, dict):
            for key in record:
                if key not in fields:
                    fields.append(key)
    return fields


def records_to_csv(path: Path, records: list[Json]) -> None:
    fields = record_fields(records)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(record for record in records if isinstance(record, dict))


def collect(args: argparse.Namespace) -> dict[str, Any]:
    args.headers_obj = load_json_object(args.headers, "--headers")
    args.payload_obj = load_json_object(args.payload, "--payload")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    first = make_request(args, 1)
    first_elapsed = time.perf_counter() - started
    first_records = get_records(first, args.records_path)
    total = get_int(first, args.total_path)
    source_pages = get_int(first, args.pages_path)
    inferred_pages = math.ceil(total / args.page_size) if total is not None else None
    available_pages = source_pages or inferred_pages
    estimated_all_pages = available_pages or args.max_pages or 1
    estimate_all_seconds = first_elapsed * estimated_all_pages + args.delay * max(0, estimated_all_pages - 1)

    target_count = parse_limit(args.limit, total)
    should_prompt = args.limit is None and not args.no_prompt and sys.stdin.isatty()
    if target_count is None and should_prompt:
        target_count = ask_limit(total, estimate_all_seconds)
    if target_count is None:
        target_count = total
    if target_count is None and args.max_pages is None:
        raise RuntimeError("Total count is unknown; pass --limit NUMBER or --max-pages.")

    target_pages = math.ceil(target_count / args.page_size) if target_count is not None else available_pages
    if available_pages is not None:
        target_pages = min(target_pages, available_pages)
    if args.max_pages is not None:
        target_pages = min(target_pages or args.max_pages, args.max_pages)
    target_pages = max(1, target_pages or 1)

    records = list(first_records)
    page_responses = [{"page": 1, "response": first}]
    for page in range(2, target_pages + 1):
        time.sleep(args.delay)
        response = make_request(args, page)
        page_records = get_records(response, args.records_path)
        records.extend(page_records)
        page_responses.append({"page": page, "response": response})
        print(f"Fetched page {page}/{target_pages}: +{len(page_records)} records")
        if len(page_records) == 0:
            break
        if target_count is not None and len(records) >= target_count:
            break

    if target_count is not None:
        records = records[:target_count]

    summary = {
        "source_url": args.url,
        "method": args.method.upper(),
        "capture_time": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "requested_limit": args.limit or ("prompt" if should_prompt else None),
        "target_count": target_count,
        "page_size": args.page_size,
        "pages_fetched": len(page_responses),
        "source_total": total,
        "source_pages": available_pages,
        "records_collected": len(records),
    }
    (out_dir / "raw_pages.json").write_text(json.dumps(page_responses, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if records and all(isinstance(record, dict) for record in records):
        records_to_csv(out_dir / "records.csv", records)
        if args.xlsx:
            write_xlsx(out_dir / "records.xlsx", records, record_fields(records), "Records")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect paginated recruitment data from a public JSON API.")
    parser.add_argument("--url", required=True, help="JSON API endpoint.")
    parser.add_argument("--method", choices=["GET", "POST"], default="POST")
    parser.add_argument("--headers", default="", help="JSON object or path to a JSON file.")
    parser.add_argument("--payload", default="{}", help="JSON object or path to a JSON file.")
    parser.add_argument("--page-param", default="page", help="Dotted path for the page number parameter.")
    parser.add_argument("--size-param", default="size", help="Dotted path for the page size parameter.")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--records-path", default="data.records")
    parser.add_argument("--total-path", default="data.total")
    parser.add_argument("--pages-path", default="data.pages")
    parser.add_argument("--limit", default=None, help="all, half, or a positive integer.")
    parser.add_argument("--no-prompt", action="store_true", help="Do not ask for a collection size.")
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--xlsx", action="store_true", help="Also export records as formatted XLSX.")
    parser.add_argument("--out-dir", default="outputs/collected_jobs")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.page_size <= 0:
        parser.error("--page-size must be positive")
    if args.max_pages is not None and args.max_pages <= 0:
        parser.error("--max-pages must be positive")
    try:
        collect(args)
    except Exception as exc:
        parser.exit(1, f"job-postings collect: error: {exc}\n")
