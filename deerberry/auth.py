import datetime as dt
import email.utils
import json
import typing
from pathlib import Path
from typing import Optional

import httpx
from httpx import Request, Response
from pydantic import BaseModel

spoof_body = {
    "params": "{\"pbLastCookie\":\"https://peerberry.com/\",\"pbFirstCookie\":\"/\"}",
    "parsedCookies": {
        "cookies[JivoSiteLoaded]": "1",
        "cookies[last_click]": "https://peerberry.com/",
        "cookies[pb_first_cookie]": "/",
        "cookies[pb_last_cookie]": "https://peerberry.com/"
    },
}


class CredentialsStore(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: Optional[dt.datetime]


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class PeerBerryCredentials(httpx.Auth):
    def __init__(self, base_url: str, email: str, password: str, store_file: Optional[Path] = None):
        super().__init__()

        self.auth_url = base_url + '/v1/investor/login'
        self.email = email
        self.password = password
        self.store_file = store_file

        self.credentials: Optional[CredentialsStore] = None

        if self.store_file and self.store_file.exists():
            with open(self.store_file, 'rt') as fb:
                data = fb.read()
            self.credentials = CredentialsStore(**json.loads(data))

    async def async_auth_flow(self, request: Request) -> typing.AsyncGenerator[Request, Response]:
        if not self.credentials:
            response: httpx.Response = yield httpx.Request('POST', self.auth_url, json={
                'email': self.email,
                'password': self.password,
                **spoof_body,
            })

            await response.aread()
            auth_resp = AuthResponse(**response.json())

            date = email.utils.parsedate_to_datetime(response.headers['date'])

            self.credentials = CredentialsStore(
                access_token=auth_resp.access_token,
                refresh_token=auth_resp.refresh_token,
                expires_at=date + dt.timedelta(seconds=auth_resp.expires_in),
            )

            if self.store_file:
                with open(self.store_file, 'wt') as fb:
                    fb.write(self.credentials.json())

        request.headers['Authorization'] = 'Bearer ' + self.credentials.access_token
        yield request
