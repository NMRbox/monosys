#!/usr/bin/env python3
import argparse
import logging

from nmrhubusage import who_command



def main():
    logging.basicConfig()
    who_command()


if __name__ == "__main__":
    main()
