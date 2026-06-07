from __future__ import annotations

import argparse

from . import __version__
from . import clean as clean_cmd
from . import collect as collect_cmd
from . import url_export as url_export_cmd


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="job-postings", description="AI-free job posting data toolkit.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    url_parser = subparsers.add_parser("url", help="Paste a supported job site URL and export Excel.")
    for action in url_export_cmd.build_parser()._actions:
        if action.dest == "help":
            continue
        url_parser._add_action(action)

    collect_parser = subparsers.add_parser("collect", help="Collect paginated JSON API records.")
    for action in collect_cmd.build_parser()._actions:
        if action.dest == "help":
            continue
        collect_parser._add_action(action)

    clean_parser = subparsers.add_parser("clean", help="Clean and filter CSV job postings.")
    for action in clean_cmd.build_parser()._actions:
        if action.dest == "help":
            continue
        clean_parser._add_action(action)

    args = parser.parse_args(argv)
    if args.command == "url":
        path = url_export_cmd.export_url(args.url, args.out_dir, args.max_records, args.token)
        print(path)
    elif args.command == "collect":
        collect_cmd.collect(args)
    elif args.command == "clean":
        clean_cmd.run(args)
