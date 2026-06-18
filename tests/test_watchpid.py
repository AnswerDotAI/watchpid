import os, subprocess, sys, threading
from watchpid import parent_pid, wait_pid, watch_parent, watch_pid


def _sleep(seconds:float): return subprocess.Popen([sys.executable, "-c", f"import time; time.sleep({seconds})"])


def test_wait_pid_features(monkeypatch):
    proc = _sleep(0.1)
    assert wait_pid(proc.pid, timeout=2)
    proc.wait(timeout=2)
    assert wait_pid(proc.pid, timeout=0)

    proc = _sleep(1)
    try: assert not wait_pid(proc.pid, timeout=0.02, poll=0.005)
    finally:
        proc.terminate()
        proc.wait(timeout=2)
    assert wait_pid(proc.pid, timeout=1)

    monkeypatch.setenv("JPY_PARENT_PID", str(os.getpid()))
    assert parent_pid() == os.getpid()
    monkeypatch.setenv("JPY_PARENT_PID", "bad")
    assert parent_pid() is None


def test_watch_pid_features(monkeypatch):
    proc = _sleep(0.1)
    done = threading.Event()
    watch = watch_pid(proc.pid, done.set, poll=0.005)
    assert done.wait(2)
    watch.join(timeout=2)
    proc.wait(timeout=2)

    called = threading.Event()
    monkeypatch.setenv("JPY_PARENT_PID", str(os.getpid()))
    watch = watch_parent(called.set, timeout=0.02, poll=0.005)
    watch.join(timeout=1)
    assert not called.is_set()
