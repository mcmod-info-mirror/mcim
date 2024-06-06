import orjson
from fastapi.responses import ORJSONResponse, Response

class BaseBuilder:
    @classmethod
    def encode(cls, value):
        raise NotImplementedError
    
    @classmethod
    def decode(cls, value):
        raise NotImplementedError
    

class ORJsonBuilder(BaseBuilder):
    @classmethod
    def encode(cls, value: ORJSONResponse) -> bytes:
        content = value.body
        headers = value.headers
        status_code = value.status_code

        params = {
            "content": orjson.loads(content),
            "headers": dict(headers),
            "status_code": status_code
        }

        return orjson.dumps(
            params,
        )

    @classmethod
    def decode(cls, value: dict) -> ORJSONResponse:
        return ORJSONResponse(
            content=value["content"],
            headers=value["headers"],
            status_code=value["status_code"]
        )

class BaseRespBuilder(BaseBuilder):
    @classmethod
    def encode(cls, value: Response) -> bytes:
        headers = dict(value.headers)
        status_code = value.status_code

        return orjson.dumps(
            {
                "headers": headers,
                "status_code": status_code
            }
        )
    
    @classmethod
    def decode(cls, value: dict) -> Response:
        return Response(
            headers=value["headers"],
            status_code=value["status_code"]
        )