import typing
import pandas as pd

import httpx

from deerberry.api_client_base import ApiClientBase, json_params


class InvestorApi(ApiClientBase):
    def __init__(self, http_client: httpx.AsyncClient, page_size:int):
        super().__init__(http_client, page_size)

    async def investments_df(self, inv_type: str) -> pd.DataFrame:
        def prepare_request() -> typing.Generator[httpx.Request, httpx.Response, None]:
            offset = 0
            while True:
                response = yield self._client.build_request('GET', 'v1/investor/investments', params=httpx.QueryParams({
                    'pageSize': self._page_size,
                    'type': inv_type,
                    'sort': 'loanId',
                    'offset': offset,
                }))
                obj = response.json()
                offset += self._page_size
                if offset > obj['total']:
                    break

        responses: list[httpx.Response] = []
        async for resp in self._get_all_pages(prepare_request()):
            resp.raise_for_status()
            responses.append(resp)

        dfs = [pd.json_normalize(resp.json(**json_params)['data']) for resp in responses]
        return pd.concat(dfs, ignore_index=True)

    async def investments_current_df(self) -> pd.DataFrame:
        return await self.investments_df('CURRENT')

    async def investments_finished_df(self) -> pd.DataFrame:
        return await self.investments_df('FINISHED')
