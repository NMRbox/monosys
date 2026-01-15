import sys
from pathlib import Path
from nmrhubusage import who_command


def test_who_command():
    c = Path(__file__).parent / 'nmradmin.yaml'
    assert c.is_file()
    sys.argv = ['teestwho', '--config', c.as_posix()]
    print("\ntest all")
    who_command()
    uid=16342
    print(f"test uid {uid}")
    who_command(uid=uid)
