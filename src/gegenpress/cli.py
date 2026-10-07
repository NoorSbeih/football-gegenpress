"""Command-line entry point.

`build` is declared so the console script exists. Extract, load, and
transform start in later phases.
"""

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="gegenpress",
        description="Measure the first seconds after a team loses the ball.",
    )
    sub = parser.add_subparsers(dest="command")
    build = sub.add_parser(
        "build",
        help="Extract, load, transform, and export a competition.",
    )
    build.add_argument(
        "--competition",
        default="wc2022",
        help="Competition key from config/competitions.yaml (default: wc2022).",
    )
    args = parser.parse_args(argv)
    if args.command == "build":
        print(
            "build is not implemented yet. "
            "Phase 0 is the project scaffold; extract starts in Phase 1.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    parser.print_help()


if __name__ == "__main__":
    main()
