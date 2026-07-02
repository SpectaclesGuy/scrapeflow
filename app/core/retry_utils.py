from __future__ import annotations

from collections.abc import Awaitable, Callable

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed


Retryable = Callable[..., Awaitable[object]]


def build_retry(func: Retryable) -> Retryable:
    return retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_fixed(1),
        stop=stop_after_attempt(3),
        reraise=True,
    )(func)
