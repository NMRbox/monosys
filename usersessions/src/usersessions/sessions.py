#!/usr/bin/env python3
import collections
import pickle
from dataclasses import dataclass

import yaml
from nmrhubusage import ProcessInfo
from nmrhubusage.who import Who
from systemhealthdata import systemhealthdata_logger, ShdRedisClient, PROC_STREAM_PREFIX_SEARCH, process_datastream_host


@dataclass(frozen=True)
class UserSession:
    host: str
    username: str
    name: str
    start: str


@dataclass
class Sessions:
    """User sessions via redis process data"""
    _sessions: set[UserSession]
    _type_counts: None | collections.Counter = None
    _user_counts: None | collections.Counter = None
    _by_usage: None | list[UserSession]  = None

    @property
    def sessions(self) -> list[UserSession]:
        """Readonly sessions"""
        return self._sessions

    @property
    def user_counts(self) -> collections.Counter:
        """count Sessions by user"""
        if self._user_counts is None:
            self._build()
        return self._user_counts

    @property
    def type_counts(self) -> collections.Counter:
        """Count type of sessions"""
        if self._type_counts is None:
            self._build()
        return self._type_counts

    def by_usage(self)->list[UserSession]:
        """Sort sessions by how many user has"""
        if self._by_usage is None:
            umap = collections.defaultdict(list)
            for u_sess in self.sessions:
                umap[u_sess.username].append(u_sess)
            counted = collections.defaultdict(list)
            for user, n in self.user_counts.items():
                counted[n].append(user)
            self._by_usage = []
            for count in sorted(counted.keys(), reverse=True):
                for user in sorted(counted[count]):
                    for sess in umap[user]:
                        self._by_usage.append(sess)
        return self._by_usage

    def _build(self):
        assert self._user_counts is None
        assert self._type_counts is None
        self._user_counts = collections.Counter()
        self._type_counts = collections.Counter()
        for u_sess in self.sessions:
            self._user_counts[u_sess.username] += 1
            self._type_counts[u_sess.name] += 1




class SessionReader(ShdRedisClient):
    """Acecss redis data"""

    def __init__(self, config):
        with open(config['health']) as f:
            rconfig = yaml.safe_load(f)
        super().__init__(rconfig['redis'])
        with open(config['nmradmin']) as f:
            aconfig = yaml.safe_load(f)
        self.who = Who(aconfig)

    def sessions(self)->Sessions:
        """Scan redis. Using the latest process records, generate list of user sessions"""
        # scan Redis
        keys = self.rserver.keys(PROC_STREAM_PREFIX_SEARCH)
        umap = collections.defaultdict(list)
        hostkeys = collections.defaultdict(list)

        for k in keys:
            hostkeys[process_datastream_host(k)].append(k)

        latest = set()

        for n in hostkeys.values():
            ordered = sorted(n, reverse=True)
            latest.add(ordered[0])

        system_unique = set()
        for k in latest:
            host = process_datastream_host(k)
            data = self.rserver.get(k)
            try:
                procs = pickle.loads(data)
            except Exception as e:
                systemhealthdata_logger.debug(f"Skipping key {k!r}: pickle error {e}")
                continue

            # must be a list of ProcessInfo
            if not procs or not isinstance(procs[0], ProcessInfo):
                continue

            # gather sessions
            unique_on_host = set()
            for s in self.who.sessions(procs):
                unique_on_host.add(UserSession(host, s.username, s.name, s.start.isoformat()))
            system_unique.update(unique_on_host)
        return Sessions(system_unique)
