import datetime
import pwd
import time
from typing import Any, ClassVar, Iterable

import psutil
from dataclasses import dataclass, field

@dataclass
class ProcessInfo:
    pid: int
    parent_pid: int
    name: str
    uid: int
    exe: str
    commandline: list[str]
    cwd: str
    cpu_util: float
    memory_used: int  # bytes
    start: datetime.datetime
    files: list = field(default_factory=list)

    _procs: ClassVar[dict[int, Any]] = {}
    _user: ClassVar[dict[int, str]] = {}

    def __eq__(self, other):
        if isinstance(other, ProcessInfo):
            return self.pid == other.pid
        return NotImplemented

    def __hash__(self):
        return hash(self.pid)

    def __post_init__(self):
        ProcessInfo._procs[self.pid] = self

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__post_init__()

    @property
    def parent(self) -> 'ProcessInfo':
        return ProcessInfo._procs[self.parent_pid]

    @property
    def toplevel(self):
        candidate = self
        while True:
            if candidate.parent_pid == 0 or (p := ProcessInfo._procs[candidate.parent_pid]).uid != self.uid:
                return candidate
            candidate = p

    @property
    def username(self):
        if (u := ProcessInfo._user.get(self.uid)) is not None:
            return u
        ProcessInfo._user[self.uid] = (u := pwd.getpwuid(self.uid).pw_name)
        return u

    @staticmethod
    def _create(proc: psutil.Process) -> 'ProcessInfo':
        """Create a ProcessInfo object.
        May raise psutil.NoSuchProcess, psutil.AccessDenied.
        """
        return ProcessInfo(
            proc.info['pid'],
            proc.info['ppid'],
            proc.name(),
            proc.info['uids'].real,
            proc.info['exe'],
            proc.info['cmdline'],
            proc.info['cwd'],
            proc.cpu_percent(interval=None),
            proc.memory_info().rss,
            datetime.datetime.fromtimestamp(proc.info['create_time'])
        )

    @staticmethod
    def collect_sample(include_files: bool = False) -> Iterable:
        rval = []

        before_offsets = {}
        if include_files:
            for proc in psutil.process_iter(['pid']):
                try:
                    proc.cpu_percent(interval=None)
                    open_files = proc.open_files()
                    before_offsets[proc.pid] = {}
                    for of in open_files:
                        fd = of.fd
                        fdinfo_path = f"/proc/{proc.pid}/fdinfo/{fd}"
                        try:
                            with open(fdinfo_path, "r") as f:
                                for line in f:
                                    if line.startswith("pos:"):
                                        before_offsets[proc.pid][fd] = int(line.split()[1])
                                        break
                        except Exception:
                            before_offsets[proc.pid][fd] = None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        else:
            for proc in psutil.process_iter():
                try:
                    proc.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        # Wait a short interval so that CPU percent measurement is updated (and used as our I/O delta interval).
        time.sleep(0.1)

        # Now, iterate over processes to create ProcessInfo objects and, if requested, compute file offset differences.
        for proc in psutil.process_iter(['pid', 'ppid', 'name', 'uids', 'exe', 'cmdline', 'cwd', 'create_time']):
            try:
                pi = ProcessInfo._create(proc)
                if include_files:
                    open_files = proc.open_files()
                    files_with_io = []
                    for of in open_files:
                        fd = of.fd
                        fdinfo_path = f"/proc/{proc.pid}/fdinfo/{fd}"
                        offset_after = None
                        try:
                            with open(fdinfo_path, "r") as f:
                                for line in f:
                                    if line.startswith("pos:"):
                                        offset_after = int(line.split()[1])
                                        break
                        except Exception:
                            offset_after = None
                        offset_before = before_offsets.get(proc.pid, {}).get(fd)
                        if offset_before is not None and offset_after is not None:
                            diff = offset_after - offset_before
                        else:
                            diff = "N/A"
                        files_with_io.append((of.path, of.mode, diff))
                    pi.files = files_with_io
                rval.append(pi)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return rval 

def top_level_processes(sample=None) -> Iterable[ProcessInfo]:
    """Return top level processes."""
    if sample is None:
        sample = ProcessInfo.collect_sample()
    return set(p.toplevel for p in sample)

