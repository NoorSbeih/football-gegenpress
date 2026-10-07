"""Command-line entry point."""

import argparse


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
        from gegenpress.flows import build_flow

        build_flow(competition=args.competition)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
