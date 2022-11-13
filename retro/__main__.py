import argparse
import logging

from retro import start


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "-s", "--server", action="store_true", help="start up as server"
    )
    parser.add_argument(
        "-so", "--server-only", action="store_true", help="only starts server"
    )
    parser.add_argument("-d", "--debug", action="store_true", help="provide debug logs")
    args = parser.parse_args()

    if args.server_only:
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
    elif args.debug:
        logging.basicConfig(
            filename="server_debug.log" if args.server else "debug.log",
            encoding="utf-8",
            level=logging.DEBUG,
        )

    start(args)


if __name__ == "__main__":
    main()
