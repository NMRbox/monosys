#!/usr/bin/env python3
import argparse
import logging

from nmrhubusage import who_command, ProcessInfo


def main():
    logging.basicConfig()
    who_command()
    ProcessInfo.collect_sample()


if __name__ == "__main__":
    main()
