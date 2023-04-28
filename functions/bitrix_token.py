from typing import Optional, Iterable, Any

from .api_call import api_call, ConnectionToBitrixError
from .exceptions import BitrixApiError, ExpiredToken


class BaseBitrixToken:
    DEFAULT_TIMEOUT = 10

    domain = NotImplemented
    auth_token = NotImplemented
    web_hook_auth = NotImplemented

    def get_auth(self):
        return (self.web_hook_auth or self.auth_token), bool(self.web_hook_auth)

    def call_api_method(self, api_method, params=None, timeout=DEFAULT_TIMEOUT):
        auth, webhook = self.get_auth()

        try:
            response = api_call(
                domain=self.domain,
                api_method=api_method,
                auth_token=auth,
                webhook=webhook,
                params=params,
                timeout=timeout,
            )
        except ConnectionToBitrixError:
            # fixme: BitrixApiError явно не ожидает, что туда передадут словарь
            raise BitrixApiError(600, {'error': 'ConnectionToBitrixError'})

        # Пробуем раскодировать json
        try:
            json_response = response.json()
        except ValueError:
            raise BitrixApiError(600, response)

        if response.status_code in [200, 201] and not json_response.get('error'):
            return json_response

        if response.status_code == 401 and json_response['error'] == 'expired_token':
            raise ExpiredToken

        raise BitrixApiError(response.status_code, response)

    call_api_method_v2 = call_api_method

    def batch_api_call(self, methods, timeout=DEFAULT_TIMEOUT, chunk_size=50, halt=0, log_prefix=''):
        """:rtype: bitrix_utils.bitrix_auth.functions.batch_api_call3.BatchResultDict
        """
        from functions.batch_api_call import _batch_api_call
        return _batch_api_call(methods=methods,
                               bitrix_user_token=self,
                               function_calling_from_bitrix_user_token_think_before_use=True,
                               timeout=timeout,
                               chunk_size=chunk_size,
                               halt=halt,
                               log_prefix=log_prefix)


    def call_list_fast(
            self,
            method,  # type: str
            params=None,  # type: Optional[dict]
            descending=False,  # type: bool
            timeout=DEFAULT_TIMEOUT,  # type: Optional[int]
            log_prefix='',  # type: str
            limit=None,  # type: Optional[int]
            batch_size=50,  # type: int
    ):
        # type: (...) -> Iterable[Any]
        """Списочный запрос с параметром ?start=-1
        см. описание bitrix_utils.bitrix_auth.functions.call_list_fast.call_list_fast

        Если происходит KeyError, надо добавить описание метода
        в справочники METHOD_TO_* в bitrix_utils.bitrix_auth.functions.call_list_fast
        """
        from functions.call_list_fast import call_list_fast
        return call_list_fast(self, method, params, descending=descending,
                              limit=limit, batch_size=batch_size,
                              timeout=timeout, log_prefix=log_prefix)

    def call_list_method(
            self,
            method,  # type: str
            fields=None,  # type: Optional[dict]
            limit=None,  # type: Optional[int]
            allowable_error=None,  # type: Optional[int]
            timeout=DEFAULT_TIMEOUT,  # type: Optional[int]
            force_total=None,  # type: Optional[int]
            log_prefix='',  # type: str
            batch_size=50,  # type: int
    ):  # type: (...) -> list
        from .call_list_method import call_list_method
        result = call_list_method(self, method, fields=fields,
                                       limit=limit,
                                       allowable_error=allowable_error,
                                       timeout=timeout,
                                       log_prefix=log_prefix,
                                       batch_size=batch_size,
                                       v=2)
        return result



class BitrixToken(BaseBitrixToken):
    def __init__(self, domain, auth_token=None, web_hook_auth=None):
        self.domain = domain
        self.auth_token = auth_token
        self.web_hook_auth = web_hook_auth
