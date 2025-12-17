import attr
from core.exceptions import BaseAPIException


@attr.s(auto_attribs=True, auto_exc=True)
class AssetNotActiveError(BaseAPIException):
    code: str = 'asset_not_active'
    message: str = 'Asset is not active. Complete the upload first.'
    status_code: int = 400


@attr.s(auto_attribs=True, auto_exc=True)
class AssetOwnershipError(BaseAPIException):
    code: str = 'asset_ownership_error'
    message: str = 'Asset does not belong to this client.'
    status_code: int = 403


@attr.s(auto_attribs=True, auto_exc=True)
class DetectionNotFoundError(BaseAPIException):
    code: str = 'detection_not_found'
    message: str = 'Detection not found.'
    status_code: int = 404


@attr.s(auto_attribs=True, auto_exc=True)
class DetectionOwnershipError(BaseAPIException):
    code: str = 'detection_ownership_error'
    message: str = 'Detection does not belong to this client.'
    status_code: int = 403


@attr.s(auto_attribs=True, auto_exc=True)
class UnknownTileLabelError(BaseAPIException):
    code: str = 'unknown_tile_label'
    message: str = 'Model predicted an unknown tile label.'
    status_code: int = 500
