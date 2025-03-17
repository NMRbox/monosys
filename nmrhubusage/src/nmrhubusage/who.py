#!/usr/bin/env python3
"""Who which considers VNC logins, configurable via a YAML file."""
import datetime
import logging
from collections import defaultdict
from pathlib import Path

import psutil
import argparse
import yaml
import os
from nmrhubusage import _YAMLS, ProcessInfo

# Setup local logger named "who_logger"
who_logger = logging.getLogger("who_logger")


class Who:
    def __init__(self, config):
        """
        Initialize Who.

        :param config: Dictionary with keys 'LOGGED_IN_PROCESSES' and 'EXCLUDE_PROCESSES'
        """
        self._logged_in_processes = config['LOGGED_IN_PROCESSES']
        self._exclude_processes = config['EXCLUDE_PROCESSES']
        who_logger.info("Initialized Who with logged_in_processes: %s and exclude_processes: %s",
                         self._logged_in_processes, self._exclude_processes)


    def sessions(self,sample):
        """Find top processes in sample"""
        rval = []
        for p in sample: 
            if p.name in self._logged_in_processes:
                if (tl := p.toplevel).name not in self._exclude_processes:
                    rval.append(tl)
        return rval

    @property
    def toplist(self):
        """Find top processes"""
        return self.sessions(ProcessInfo.collect_sample())

    def show(self):
        for top in self.toplist:
            timestr = top.start.strftime("%Y-%m-%d %H:%M:%S")
            pentry = "{:18} {:8d} {:18} {}".format(top.username, top.pid, top.name, timestr)
            print(pentry)
            who_logger.debug("Displayed process: %s", pentry)

def who_command():
    """Execute as command line"""
    yamls = ','.join(_YAMLS)
    parser = argparse.ArgumentParser(description="Who: Process display tool with VNC login considerations.")
    parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")
    parser.add_argument( "--config", help=f"Path to the YAML configuration file (default: {yamls}")
    args = parser.parse_args()
    who_logger.setLevel(getattr(logging,args.loglevel))
    if args.config is None:
        for y in _YAMLS:
            if (cpath := Path(y)).is_file():
                break
        # noinspection PyUnboundLocalVariable
        if not cpath.is_file():
            raise ValueError(f"No yaml found in {yamls}")
    else:
        cpath = args.config

    with open(cpath) as f:
        config = yaml.safe_load(f)

    who = Who(config)
    who.show()



