import hashlib
import xxhash
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Union
from typing_extensions import Protocol

_Func = Callable[..., Any]

IGNORE_KWARGS = "requests"


def filter_kwargs(kwargs: Dict[str, Any], keys: Tuple[str, ...]) -> Dict[str, Any]:
    return {k: v for k, v in kwargs.items() if k not in keys}


class KeyBuilder(Protocol):
    def __call__(
        self,
        __function: _Func,
        __namespace: str = ...,
        *,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[str], str]: ...


def default_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    cache_key = hashlib.md5(  # noqa: S324
        f"{func.__module__}:{func.__name__}:{args}:{filter_kwargs(kwargs, IGNORE_KWARGS)}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"


def xxhash_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    cache_key = xxhash.xxh3_64(  # noqa: S324
        f"{func.__module__}:{func.__name__}:{args}:{filter_kwargs(kwargs, IGNORE_KWARGS)}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"
