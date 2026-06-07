from __future__ import annotations

import argparse

from . import __version__
from . import clean as clean_cmd
from . import collect as collect_cmd


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="job-postings", description="AI-free job posting data toolkit.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

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
    if args.command == "collect":
        collect_cmd.collect(args)
    elif args.command == "clean":
        clean_cmd.run(args)
