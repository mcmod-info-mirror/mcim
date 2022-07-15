
__all__ = [
    'StatusCodeException'
]

class StatusCodeException(Exception):
    def __init__(self, code: int):
        super().__init__('Unexcept status code: {}'.format(code))
        self.code = code
