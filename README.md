# watchpid

`watchpid` is a tiny stdlib-only package for waiting until a process exits.

It uses OS process notifications when Python exposes them:

- Linux: `os.pidfd_open()`
- macOS/BSD: `select.kqueue()`
- Other platforms: polling fallback

## Usage

Block until a pid exits:

```python
from watchpid import wait_pid

if wait_pid(1234, timeout=5):
    print("exited")
```

Run a callback in a daemon thread:

```python
from watchpid import watch_pid

watch_pid(1234, lambda: print("exited"))
```

Watch the parent pid set by `jupyter_client`:

```python
from watchpid import watch_parent

watch_parent(lambda: print("parent exited"))
```

`watch_parent()` reads `JPY_PARENT_PID` by default. It returns `None` when the env var is unset, invalid, or `<= 1` (so `pid 1`/init is never watched).

### Caveats

- The event-based backends (`pidfd`, `kqueue`) detect exit reliably. The polling fallback uses pid liveness checks, so it is best-effort: it can't distinguish a reused pid, and an unreaped child process stays "alive" to the poller until it's `wait()`ed.

## API

```python
wait_pid(pid, timeout=None, poll=0.1) -> bool
watch_pid(pid, callback, timeout=None, poll=0.1, daemon=True, name=None) -> Thread
parent_pid(env="JPY_PARENT_PID") -> int | None
watch_parent(callback, env="JPY_PARENT_PID", timeout=None, poll=0.1, daemon=True, name="watchpid-parent") -> Thread | None
```

`wait_pid()` returns `True` when the process exits and `False` on timeout.

## Development

```bash
pip install -e ".[test]"
pytest -q
```
