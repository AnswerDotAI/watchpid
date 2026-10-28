import subprocess, sys, threading
from watchpid import _wait_poll, wait_pid, watch_pid


def _sleep(seconds:float): return subprocess.Popen([sys.executable, "-c", f"import time; time.sleep({seconds})"])


def test_process_lifecycle():
    proc = _sleep(0.2)
    done = threading.Event()
    try:
        watch = watch_pid(proc.pid, done.set, timeout=0.02)
        assert not wait_pid(proc.pid, timeout=0.02)
        watch.join(timeout=2)
        assert not watch.is_alive() and not done.is_set()
        assert not _wait_poll(proc.pid, timeout=0.02, poll=0.005)
        watch = watch_pid(proc.pid, done.set, timeout=2)
        assert wait_pid(proc.pid, timeout=2)
        proc.wait(timeout=2)
        assert done.wait(2)
        watch.join(timeout=2)
        assert not watch.is_alive()
        assert wait_pid(proc.pid, timeout=0)
    finally:
        proc.terminate()
        proc.wait(timeout=2)
