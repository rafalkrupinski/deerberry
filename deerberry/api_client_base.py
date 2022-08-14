import typing
from abc import ABC
from decimal import Decimal

import httpx

default_page_size = 100

json_params = {
    'parse_float': Decimal,
}


class ApiClientBase(ABC):
    def __init__(self, http_client: httpx.AsyncClient, page_size: int):
        self._page_size = page_size
        self._client = http_client

    async def _get_all_pages(self, flow: typing.Generator[httpx.Request, httpx.Response, None]) -> typing.AsyncGenerator[httpx.Response, None]:
        request = next(flow)

        while True:
            response = await self._client.send(request)
            await response.aread()
            yield response
            try:
                request = flow.send(response)
            except StopIteration:
                break
