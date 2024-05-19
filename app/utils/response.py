from fastapi.responses import ORJSONResponse, Response

class TrustableResponse:
    def __init__(self, status_code: int = 200, content: dict = None, trustable: bool = True):
        headers = {}
        headers["Trustable"] = trustable
        return ORJSONResponse(status_code=status_code, content=content, headers=headers)

# uncached response
class UncachedResponse:
    def __init__(self, status_code: int = 404):
        headers = {}
        headers["Trustable"] = False
        return Response(status_code=status_code, headers=headers)