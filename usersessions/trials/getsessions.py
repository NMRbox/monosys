#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

import yaml

from usersessions import SessionReader

TYAML = Path(__file__).parent / 'session.yaml'

def main():
    logging.basicConfig()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-y', '--yaml',default=TYAML,help="YAML configuration")
    parser.add_argument('op',nargs='?',choices=('list','counts','sort'),default='list',help="Test / display option")

    # parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")

    args = parser.parse_args()
    with open(args.yaml) as f:
        config = yaml.safe_load(f)
    sr = SessionReader(config)
    sess = sr.sessions()
    if args.op == 'list':
        for s in sess.sessions:
            print(s)
    if args.op == 'counts':
        for k,v in sess.user_counts.items():
            print(f"{k} {v}")
        for k,v in sess.type_counts.items():
            print(f"{k} {v}")
    if args.op == 'sort':
        for s in sess.by_usage():
            print(s)



if __name__ == "__main__":
    main()
