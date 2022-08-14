import logging
import typing
from decimal import Decimal
from pathlib import Path
from typing import Union

import httpx
import pandas as pd

from .auth import PeerBerryCredentials
from .model.loan import Loan

logger = logging.getLogger(__name__)

BASE_URL = 'https://api.peerberry.com'

default_page_size = 100

_json_params = {
    'parse_float': Decimal,
}


class Client:
    def __init__(self, email, password, credentials_store: Union[Path, str, None] = None, ):
        self._client = httpx.AsyncClient(
            auth=PeerBerryCredentials(
                BASE_URL,
                email,
                password,
                credentials_store,
            ),
            http2=True,
            base_url=BASE_URL,
        )

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

    async def investments(self, inv_type: str) -> pd.DataFrame:
        def prepare_request() -> typing.Generator[httpx.Request, httpx.Response, None]:
            offset = 0
            while True:
                response = yield self._client.build_request('GET', 'v1/investor/investments', params=httpx.QueryParams({
                    'pageSize': default_page_size,
                    'type': inv_type,
                    'sort': 'loanId',
                    'offset': offset,
                }))
                obj = response.json()
                offset += default_page_size
                if offset > obj['total']:
                    break

        responses: list[httpx.Response] = []
        async for resp in self._get_all_pages(prepare_request()):
            resp.raise_for_status()
            responses.append(resp)

        dfs = [pd.json_normalize(resp.json(**_json_params)['data']) for resp in responses]
        return pd.concat(dfs, ignore_index=True)

    async def investments_current(self) -> pd.DataFrame:
        return await self.investments('CURRENT')

    async def investments_finished(self) -> pd.DataFrame:
        return await self.investments('FINISHED')

    async def loan_raw(self, loan_id: str) -> dict:
        url = f'v1/loans/{loan_id}'
        logger.debug('get %s', url)
        resp = await self._client.get(url)
        resp.raise_for_status()
        await resp.aread()
        return resp.json(**_json_params)

    async def loan(self, loan_id: str) -> Loan:
        d = await self.loan_raw(loan_id)
        return Loan(**d)

    async def loans(self, *, page_size: int = default_page_size):
        resp = await self._client.get('v1/loans', params={
            'sort': '-loanId',
            'pageSize': page_size,
        })
        resp.raise_for_status()
        await resp.aread()
        return resp.json(**_json_params)
