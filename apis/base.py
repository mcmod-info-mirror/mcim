
import requests
import functools

__all__ = [
    'StatusCodeException',
    'res_mustok',
    'retry',
    'retry_req_get_mustok',
    'res_mustok_async',
    'retry_async'
]

class StatusCodeException(Exception):
    def __init__(self, code: int):
        super().__init__('Unexcept status code: {}'.format(code))
        self.status_code = code

def res_mustok(callback):
    @functools.wraps(callback)
    def w(*args, **kwargs):
        res = callback(*args, **kwargs)
        if not res.ok:
            raise StatusCodeException(res.status_code)
        return res
    return w

def retry(callback, count: int, excepts: tuple, /, *args, **kwargs):
    assert hasattr(callback, '__call__'), 'Callback must be callable'
    assert count > 0, 'Try count must greater than zero'
    assert isinstance(excepts, tuple), 'Exceptions must be tuple'
    err = None
    i = 0
    while i < count:
        try:
            return callback(*args, **kwargs)
        except excepts as e:
            err = e
        i += 1
    raise err

def retry_req_get_mustok(limit: int, /, *args, **kwargs):
    return retry(res_mustok(requests.get), limit, (StatusCodeException,), *args, **kwargs)

def res_mustok_async(callback):
    @functools.wraps(callback)
    async def w(*args, **kwargs):
        res = await callback(*args, **kwargs)
        if not res.ok:
            raise StatusCodeException(res.status_code)
        return res
    return w

async def retry_async(callback, count: int, excepts: tuple, /, *args, **kwargs):
    assert hasattr(callback, '__call__'), 'Callback must be callable'
    assert count > 0, 'Try count must greater than zero'
    assert isinstance(excepts, tuple), 'Exceptions must be tuple'
    err = None
    i = 0
    while i < count:
        try:
            return await callback(*args, **kwargs)
        except excepts as e:
            err = e
        i += 1
    raise err
