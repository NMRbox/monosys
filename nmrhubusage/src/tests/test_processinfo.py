from nmrhubusage import ProcessInfo


def test_collect_sample():
    procs = ProcessInfo.collect_sample(True,0.8)
    p: ProcessInfo
    for p in procs:
        if p.files:
            print(p.name)
            for f in p.files:
                print(f"\t{f[0]} {f[2]}")

def test_without():
    procs = ProcessInfo.collect_sample(False)
    print(len(procs))

