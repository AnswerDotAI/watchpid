__version__ = "0.1.0"

import errno, os, select, threading, time
from collections.abc import Callable

__all__ = ["__version__", "parent_pid", "wait_pid", "watch_parent", "watch_pid"]


def parent_pid(env:str = "JPY_PARENT_PID")->int|None:
    "Return parent pid from `env`, or None when unset/invalid."
    try: pid = int(os.environ.get(env) or 0)
    except ValueError: return None
    return pid if pid > 1 else None


def _pid_exists(pid:int)->bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError: return False
    except PermissionError: return True


def _wait_pidfd(pid:int, timeout:float|None)->bool|None:
    pidfd_open = getattr(os, "pidfd_open", None)
    if pidfd_open is None: return None
    try: fd = pidfd_open(pid)
    except ProcessLookupError: return True
    except OSError: return None
    try:
        ready, _, _ = select.select([fd], [], [], timeout)
        return bool(ready)
    finally: os.close(fd)


def _wait_kqueue(pid:int, timeout:float|None)->bool|None:
    if not hasattr(select, "kqueue"): return None
    try:
        kq = select.kqueue()
        event = select.kevent(pid, filter=select.KQ_FILTER_PROC,
            flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_ONESHOT, fflags=select.KQ_NOTE_EXIT)
        kq.control([event], 0, 0)
        return bool(kq.control(None, 1, timeout))
    except OSError as exc:
        if exc.errno == errno.ESRCH: return True
        return None
    finally:
        try: kq.close()
        except UnboundLocalError: pass


def _wait_poll(pid:int, timeout:float|None, poll:float)->bool:
    end = None if timeout is None else time.monotonic() + timeout
    while _pid_exists(pid):
        if end is not None:
            rem = end - time.monotonic()
            if rem <= 0: return False
            time.sleep(min(poll, rem))
        else: time.sleep(poll)
    return True


def wait_pid(pid:int, timeout:float|None = None, poll:float = 0.1)->bool:
    "Wait for `pid` to exit. Return True on exit, False on timeout."
    if pid <= 0: raise ValueError("pid must be positive")
    if not _pid_exists(pid): return True
    for waiter in (_wait_pidfd, _wait_kqueue):
        if (res := waiter(pid, timeout)) is not None: return res
    return _wait_poll(pid, timeout, poll)


def watch_pid(pid:int, callback:Callable[[], None], *, timeout:float|None = None, poll:float = 0.1,
    daemon:bool = True, name:str|None = None)->threading.Thread:
    "Run `callback` in a daemon thread when `pid` exits."
    def run():
        if wait_pid(pid, timeout=timeout, poll=poll): callback()
    thread = threading.Thread(target=run, daemon=daemon, name=name or f"watchpid-{pid}")
    thread.start()
    return thread


def watch_parent(callback:Callable[[], None], *, env:str = "JPY_PARENT_PID", timeout:float|None = None, poll:float = 0.1,
    daemon:bool = True, name:str = "watchpid-parent")->threading.Thread|None:
    "Watch parent pid from `env`; return None when env is unset/invalid."
    pid = parent_pid(env)
    return None if pid is None else watch_pid(pid, callback, timeout=timeout, poll=poll, daemon=daemon, name=name)
