import attr

from core.exceptions import BaseAPIException


@attr.s(auto_attribs=True, auto_exc=True)
class ClientNotFound(BaseAPIException):
    code: str = 'client_not_found'
    message: str = 'The specified client does not exist.'
    status_code: int = 404
