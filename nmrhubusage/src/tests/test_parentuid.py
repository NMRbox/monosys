#!/usr/bin/env python3
"""Test processinfo collection with restricted /proc access."""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nmrhubusage import ProcessInfo

def test_collect_sample():
    """Test that ProcessInfo.collect_sample() works with restricted /proc access."""
    print("Collecting process sample...")
    sample = list(ProcessInfo.collect_sample(include_files=False, interval=0.1))

    print(f"\nCollected {len(sample)} processes")
    print(f"{'PID':<8} {'PPID':<8} {'UID':<8} {'Name':<20} {'parents':<30}")
    print("-" * 120)

    for proc in list(sample):
        if len(parents := proc.parent_uids) > 1:
            pstr = ','.join(str(p) for p in parents)
            print(f"{proc.pid:<8} {proc.parent_pid:<8} {proc.uid:<8} {proc.name:<20.20} {pstr}")

    # Count how many processes have restricted fields
    total = len(sample)
    no_exe = sum(1 for p in sample if p.exe is None)
    no_cmdline = sum(1 for p in sample if p.commandline is None)
    no_cwd = sum(1 for p in sample if p.cwd is None)


if __name__ == '__main__':
    test_collect_parents()
