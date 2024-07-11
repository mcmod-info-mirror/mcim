from fastapi.responses import Response


class BaseBuilder:
    @classmethod
    def encode(cls, value):
        raise NotImplementedError

    @classmethod
    def decode(cls, value):
        raise NotImplementedError


class ResponseBuilder(BaseBuilder):
    @classmethod
    def encode(cls, value: Response) -> bytes:
        body: bytes = value.body
        headers: dict = dict(value.headers)
        status_code: int = value.status_code

        params = {
            "body": body.decode("utf-8"),
            "headers": headers,
            "status_code": status_code,
        }
        return params

    @classmethod
    def decode(cls, value: dict) -> Response:
        return Response(
            content=bytes(value["body"], encoding="utf-8"),
            headers=value["headers"],
            status_code=value["status_code"],
        )
