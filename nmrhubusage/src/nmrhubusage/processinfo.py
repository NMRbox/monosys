import datetime
import pwd
import time
from typing import Any, ClassVar, Iterable

import psutil
from dataclasses import dataclass

@dataclass
class ProcessInfo:
    pid: int
    parent_pid: int
    name : str
    uid: int
    exe: str
    commandline: list[str]
    cwd: str
    cpu_util: float
    memory_used: int #bytes
    start: datetime.datetime

    _procs : ClassVar[dict[int,Any]] = {}
    _user : ClassVar[dict[int,str]] = {}

    def __eq__(self, other):
        if isinstance(other, ProcessInfo):
            return self.pid == other.pid
        return NotImplemented

    def __hash__(self):
        return hash(self.pid)

    def __post_init__(self):
        ProcessInfo._procs[self.pid] = self

    @property
    def parent(self)->'ProcessInfo':
        return ProcessInfo._procs[self.parent_pid]

    @property
    def toplevel(self):
        candidate = self
        while True:
            if  candidate.parent_pid == 0 or (p := ProcessInfo._procs[candidate.parent_pid]).uid != self.uid:
                return candidate
            candidate = p

    @property
    def username(self):
        if (u := ProcessInfo._user.get(self.uid)) is not None:
            return u
        ProcessInfo._user[self.uid] = (u := pwd.getpwuid(self.uid).pw_name)
        return u


    @staticmethod
    def _create(proc:psutil.Process)->'ProcessInfo':
        """Create ProcessInfo object. proc.cpu_percent must be called prior to create to properly collect_sample
        May raise psutil.NoSuchProcess, psutil.AccessDenied
        """
        # noinspection PyUnresolvedReferences
        return ProcessInfo(
            proc.info['pid'],
            proc.info['ppid'],
            proc.name(),
            proc.info['uids'].real ,
            proc.info['exe'],
            proc.info['cmdline'],
            proc.info['cwd'],
            proc.cpu_percent(interval=None),
            proc.memory_info().rss,  # memory in bytes
            datetime.datetime.fromtimestamp(proc.info['create_time'])
        )

    @staticmethod
    def collect_sample()->Iterable:
        rval = []

        # Initialize CPU percent for each process. This call starts the measurement.
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Wait a short interval so that a subsequent CPU percentage call provides a measurement
        time.sleep(0.1)

        # Iterate over processes to collect data.
        for proc in psutil.process_iter(['pid', 'ppid','name','uids', 'exe', 'cmdline', 'cwd','create_time']):
            try:
                rval.append(ProcessInfo._create(proc))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return rval 

def top_level_processes(sample = None)->Iterable[ProcessInfo]:
    """Return top level processes"""
    if sample is None:
        sample = ProcessInfo.collect_sample()
    return set(p.toplevel for p in sample)