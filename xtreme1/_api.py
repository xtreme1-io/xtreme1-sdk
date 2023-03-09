from typing import List, Dict, Optional, Union

import requests

from .exceptions import SDKException, EXCEPTIONS


class Api:

    def __init__(
            self,
            access_token: str,
            base_url: str
    ):
        self.access_token = access_token
        self._headers = {
            'Authorization': f'Bearer {access_token}'
        }
        self.base_url = base_url

    def _base_request(
            self,
            method: str,
            headers: Dict,
            endpoint: str,
            params: Optional[Dict] = None,
            files: Optional[Dict] = None,
            data: Optional[Dict] = None,
            json: Optional[Dict] = None,
            full_url: Optional[str] = None
    ):

        if not full_url:
            full_url = f'{self.base_url}/api/{endpoint}'

        resp = requests.request(
            method=method,
            url=full_url,
            headers=headers,
            params=params,
            files=files,
            data=data,
            json=json
        )

        if resp.status_code == 200:
            info = resp.json()
            if info['code'] == 'OK':
                return info['data']
            else:
                cur_exception = EXCEPTIONS.get(info['code'], SDKException)
                raise cur_exception(code=info['code'], message=info['message'])
        else:
            raise EXCEPTIONS.get(resp.status_code, SDKException(code=resp.status_code))

    def get_request(
            self,
            endpoint: str,
            params: Optional[Dict] = None,
            headers: bool = True,
            full_url: Optional[str] = None
    ) -> Union[Dict, List[Dict]]:
        """
        An encapsulated 'GET' method.

        Parameters
        ----------
        endpoint: str
            The endpoint of current api url.
        params: Optional[Dict], default None
            Parameters to add in 'GET' request.
        headers: bool, default True
            Request with headers or not.
        full_url: Optional[str], default None
            A complete url. If this parameter is passed, 'self.base_url' and 'endpoint' will be invalid.

        Returns
        -------
        Union[Dict, List[Dict]]
            A dict or list of dict transformed from json.
        """
        if headers:
            headers = self._headers
        return self._base_request(
            method='GET',
            headers=headers,
            endpoint=endpoint,
            params=params,
            full_url=full_url
        )

    def post_request(
            self,
            endpoint: str,
            payload: Optional[Dict] = None,
            data: Optional[Dict] = None,
            files: Optional[Dict] = None,
            headers: bool = True,
            full_url: Optional[str] = None
    ) -> Union[str, Dict, None, bool]:
        """
        An encapsulated 'POST' method.

        Parameters
        ----------
        endpoint: str
            The endpoint of current api url.
        payload: Optional[Dict], default None
            Parameters to add in 'POST' request.
        data: Optional[Dict], default None
            Data to add in 'POST' request.
        files: Optional[Dict], default None
            Files to upload.
        headers: bool, default True
            Request with headers or not.
        full_url: Optional[str], default None
            A complete url. If this parameter is passed, 'self.base_url' and 'endpoint' will be invalid.

        Returns
        -------
        Union[str, Dict, None]
            A simple message, a dict or null.
        """
        if headers:
            headers = self._headers
        return self._base_request(
            method='POST',
            headers=headers,
            endpoint=endpoint,
            data=data,
            json=payload,
            files=files,
            full_url=full_url
        )
