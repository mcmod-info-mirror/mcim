from fastapi.responses import ORJSONResponse, Response

class TrustableResponse(ORJSONResponse):
    def __init__(self, status_code: int = 200, content: dict = None, trustable: bool = True):
        headers = {}
        headers["Trustable"] = str(trustable)
        super().__init__(status_code=status_code, content=content, headers=headers)

# uncached response
class UncachedResponse(Response):
    def __init__(self, status_code: int = 404):
        headers = {}
        headers["Trustable"] = "False"
        super().__init__(status_code=status_code, headers=headers)