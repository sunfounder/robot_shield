import time
import subprocess
from typing import Callable, Any


def retry(times: int = 5, delay: float = 0.1):
    """Retry decorator — retry up to *times* with *delay* seconds between attempts.

    Args:
        times: Maximum number of attempts before giving up.
        delay: Seconds to sleep between retries.

    Returns:
        Callable: Decorator that wraps a function with retry logic.

    Raises:
        Exception: Re-raises the last exception if all attempts fail.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*arg, **kwargs):
            last_exc = None
            for _ in range(times):
                try:
                    return func(*arg, **kwargs)
                except Exception as e:
                    last_exc = e
                    time.sleep(delay)
                    continue
            raise last_exc
        return wrapper
    return decorator


def run_command(cmd: str, timeout: float | None = None) -> tuple:
    """Run a shell command, return ``(returncode, stdout)``.

    Args:
        cmd: Shell command string to execute.
        timeout: Max execution time in seconds. If exceeded, returns
                 ``(124, "timed out after Ns")``. ``None`` for no timeout.

    Returns:
        tuple: ``(returncode: int, stdout: str)`` — exit code and decoded stdout.
               On timeout: ``(124, "timed out after Ns")``.
    """
    if timeout is not None:
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, timeout=timeout)
            return r.returncode, r.stdout.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return 124, f"timed out after {timeout}s"

    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode("utf-8")
    status = p.poll()
    return status, result


def mapping(x: float, in_min: float, in_max: float,
            out_min: float, out_max: float) -> float:
    """Linear map *x* from [in_min, in_max] to [out_min, out_max].

    Args:
        x: Input value to map.
        in_min: Lower bound of input range.
        in_max: Upper bound of input range.
        out_min: Lower bound of output range.
        out_max: Upper bound of output range.

    Returns:
        float: *x* linearly remapped to [out_min, out_max].
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def constrain(value: float, min_value: float, max_value: float) -> float:
    """Clamp *value* to [*min_value*, *max_value*].

    Args:
        value: Value to clamp.
        min_value: Lower bound of the range.
        max_value: Upper bound of the range.

    Returns:
        float: *value* clamped to [*min_value*, *max_value*].
    """
    return min(max(value, min_value), max_value)


class LazyReader:
    """Cache a function result for *interval* seconds, re-reading on expiry.

    Args:
        read_function: Callable that returns a value to cache.
        interval: Cache TTL in seconds. Re-reads once this expires.
    """

    def __init__(self, read_function: Callable, interval: int = 10) -> None:
        self._read = read_function
        self._interval = interval
        self._value = None
        self._last = 0.0

    def read(self) -> Any:
        """Return cached value, re-reading from *read_function* on expiry.

        Returns:
            Any: Cached value (refreshed if TTL elapsed).
        """
        if time.time() - self._last > self._interval:
            self._value = self._read()
            self._last = time.time()
        return self._value


__all__ = [
    "retry",
    "run_command",
    "mapping",
    "constrain",
    "LazyReader",
]
