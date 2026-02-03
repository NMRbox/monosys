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
    print("\nSample of first 10 processes:")
    print(f"{'PID':<8} {'PPID':<8} {'UID':<8} {'Name':<20} {'Exe':<30} {'CWD':<30}")
    print("-" * 120)

    for proc in list(sample)[:10]:
        exe = proc.exe if proc.exe else "<access denied>"
        cwd = proc.cwd if proc.cwd else "<access denied>"
        print(f"{proc.pid:<8} {proc.parent_pid:<8} {proc.uid:<8} {proc.name:<20.20} {exe:<30.30} {cwd:<30.30}")

    # Count how many processes have restricted fields
    total = len(sample)
    no_exe = sum(1 for p in sample if p.exe is None)
    no_cmdline = sum(1 for p in sample if p.commandline is None)
    no_cwd = sum(1 for p in sample if p.cwd is None)

    print(f"\nAccess statistics:")
    print(f"  Total processes: {total}")
    print(f"  Processes with exe=None: {no_exe} ({no_exe*100//total if total > 0 else 0}%)")
    print(f"  Processes with cmdline=None: {no_cmdline} ({no_cmdline*100//total if total > 0 else 0}%)")
    print(f"  Processes with cwd=None: {no_cwd} ({no_cwd*100//total if total > 0 else 0}%)")

if __name__ == '__main__':
    test_collect_sample()
