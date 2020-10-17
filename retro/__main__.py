import argparse

from retro import start


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-s',
                        '--server',
                        action='store_true',
                        help='start up as server')
    args = parser.parse_args()
    start(server=args.server)


if __name__ == '__main__':
    main()
