#!/usr/bin/env python3
from nmrhubusage import ProcessInfo
if __name__ == "__main__":
    procs = ProcessInfo.collect_sample(True)
    p: ProcessInfo
    for p in procs:
        if p.files:
            print(p.name)
            for f in p.files:
                print(f"\t{f[0]} {f[2]}")


