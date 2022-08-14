import logging
import typing
from functools import cache
from pathlib import Path
from typing import Union, Optional, AsyncGenerator

import httpx

from .api_client_base import ApiClientBase, json_params, default_page_size
from .auth import PeerBerryCredentials
from .investor import InvestorApi
from .model.loan import Loan

logger = logging.getLogger(__name__)

BASE_URL = 'https://api.peerberry.com'


class Client(ApiClientBase):
    def __init__(
            self,
            email: str,
            password: str,
            credentials_store: Union[Path, str, None] = None,
            page_size=default_page_size
    ):
        """
        :param email: user email
        :param password:  user password
        :param credentials_store: path to a file to store tokens
        """

        super().__init__(
            httpx.AsyncClient(
                auth=PeerBerryCredentials(
                    BASE_URL,
                    email,
                    password,
                    credentials_store,
                ),
                http2=True,
                base_url=BASE_URL,
            ),
            page_size,
        )

    @property
    @cache
    def investor(self):
        return InvestorApi(self._client, self._page_size)

    async def loan_raw(self, loan_id: str) -> dict:
        url = f'v1/loans/{loan_id}'
        logger.debug('get %s', url)
        resp = await self._client.get(url)
        resp.raise_for_status()
        await resp.aread()
        return resp.json(**json_params)

    async def loan(self, loan_id: str) -> Loan:
        d = await self.loan_raw(loan_id)
        return Loan(**d)

    async def loans_raw(self, *, limit: Optional[int] = None) -> AsyncGenerator[dict, None]:
        def generate_pages() -> typing.Generator[httpx.Request, httpx.Response, None]:
            offset = 0
            page_size = min(self._page_size, limit)
            while True:
                response = yield self._client.build_request('GET', 'v1/loans', params=httpx.QueryParams({
                    'sort': '-loanId',
                    'pageSize': page_size,
                    'offset': offset,
                }))
                obj = response.json()
                offset += self._page_size
                if offset >= obj['total'] or (limit is not None and offset >= limit):
                    break

        async for resp in self._get_all_pages(generate_pages()):
            resp.raise_for_status()
            for elem in resp.json(**json_params)['data']:
                yield elem
