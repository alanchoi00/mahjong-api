import attr
from core.exceptions import BaseAPIException


@attr.s(auto_attribs=True, auto_exc=True)
class S3Error(BaseAPIException):
    code: str = 's3_error'
    message: str = 'An error occurred while interacting with S3.'
    status_code: int = 500


@attr.s(auto_attribs=True, auto_exc=True)
class InvalidFileTypeError(BaseAPIException):
    code: str = 'invalid_file_type'
    message: str = 'The uploaded file type is not allowed.'
    status_code: int = 400


@attr.s(auto_attribs=True, auto_exc=True)
class UploadNotCompleteError(BaseAPIException):
    code: str = 'upload_not_complete'
    message: str = 'The file has not been uploaded to storage.'
    status_code: int = 400


@attr.s(auto_attribs=True, auto_exc=True)
class InvalidUploadSessionStateError(BaseAPIException):
    code: str = 'invalid_upload_session_state'
    message: str = 'Upload session is in an invalid state for this operation.'
    status_code: int = 400


@attr.s(auto_attribs=True, auto_exc=True)
class ModelDownloadError(BaseAPIException):
    code: str = 'model_download_error'
    message: str = 'Failed to download model from S3.'
    status_code: int = 500
