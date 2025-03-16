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
from nmrhubusage import _YAMLS

# Setup local logger named "who_logger"
who_logger = logging.getLogger("who_logger")

class MyProc:
    """Cache process info locally."""
    def __init__(self, p):
        self.p = p
        self._pid = p.pid
        self._name = p.name()
        self._uid = None
        self._ppid = None
        self._username = None
        self._createtime = None
        who_logger.debug(f"Initialized MyProc for PID {self._pid}, Name {self._name}")

    @property
    def pid(self):
        return self._pid

    @property
    def name(self):
        return self._name

    @property
    def uid(self):
        if self._uid is None:
            self._uid = self.p.uids()[0]
            who_logger.debug(f"Fetched UID {self._uid} for PID {self._pid}")
        return self._uid

    @property
    def username(self):
        if self._username is None:
            self._username = self.p.username()
            who_logger.debug(f"Fetched username {self._username} for PID {self._pid}")
        return self._username

    @property
    def ppid(self):
        if self._ppid is None:
            self._ppid = self.p.ppid()
            who_logger.debug(f"Fetched PPID {self._ppid} for PID {self._pid}")
        return self._ppid

    @property
    def createtime(self):
        if self._createtime is None:
            ts = self.p.create_time()
            self._createtime = datetime.datetime.fromtimestamp(ts)
            who_logger.debug(f"Fetched createtime {self._createtime} for PID {self._pid}")
        return self._createtime

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

    def _build(self):
        """Build process dictionaries based on the configured process sets."""
        self.userdict = defaultdict(list)
        self.procdict = {}
        who_logger.info("Building process dictionaries...")
        for p in psutil.process_iter():
            try:
                mp = MyProc(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                who_logger.debug("Skipping process due to error: %s", e)
                continue
            self.procdict[p.pid] = mp
            if mp.name in self._logged_in_processes:
                self.userdict[mp.uid].append(mp)
        who_logger.info("Built userdict with %d UIDs", len(self.userdict))

    def _topproc(self, pinfo: MyProc) -> MyProc:
        """Return the topmost process for a given process with the same uid."""
        uid = pinfo.uid
        working = pinfo
        while True:
            parent = self.procdict.get(working.ppid)
            if parent and parent.uid == uid:
                who_logger.debug("Traversing from PID %d to parent PID %d for UID %s", working.pid, parent.pid, uid)
                working = parent
            else:
                who_logger.debug("Top process for UID %s is PID %d", uid, working.pid)
                return working

    def _resolve(self) -> list:
        """Find all top level processes for users based on LOGGED_IN_PROCESSES."""
        toplist = []
        for uid, proclist in self.userdict.items():
            tops = {}
            for p in proclist:
                tproc = self._topproc(p)
                if tproc.name not in self._exclude_processes:
                    tops[tproc.pid] = tproc
            toplist += list(tops.values())
        who_logger.info("Resolved %d top-level processes", len(toplist))
        return toplist

    @property
    def toplist(self):
        """Find top processes"""
        self._build()
        return self._resolve()

    def show(self):
        for top in self.toplist:
            timestr = top.createtime.strftime("%Y-%m-%d %H:%M:%S")
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


