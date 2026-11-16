"""Host-local advisory lock; the OS releases it if a worker stops."""
from contextlib import contextmanager
from functools import wraps
import os
from pathlib import Path
import time


@contextmanager
def run_lock(run, timeout=10):
    run = Path(run)
    if not run.is_dir():
        raise ValueError('実行ディレクトリーが存在しない')
    with (run / '.audit.lock').open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0, 2)
            if not handle.tell():
                handle.write(b'0'); handle.flush()
            def acquire():
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            def release():
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            def acquire():
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            def release():
                fcntl.flock(handle, fcntl.LOCK_UN)
        deadline = time.monotonic() + timeout
        while True:
            try:
                acquire(); break
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    raise ValueError('別の処理がこのrunを更新中。終了後に再実行する')
                time.sleep(.05)
        try:
            yield
        finally:
            release()


def locked(function):
    @wraps(function)
    def wrapped(run, *args, **kwargs):
        with run_lock(run):
            return function(run, *args, **kwargs)
    return wrapped
