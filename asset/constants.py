from enum import Enum


ALLOWED_IMAGE_MIMES = frozenset(
    [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/heic',
        'image/heif',
    ],
)


class StorageProvider(Enum):
    S3 = 's3'
    LOCAL = 'local'


class UploadStatus(Enum):
    CREATED = 'created'
    PRESIGNED = 'presigned'
    COMPLETED = 'completed'
    FAILED = 'failed'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class UploadPurpose(Enum):
    HAND_PHOTO = 'hand_photo'
    OTHER = 'other'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class AssetRole(Enum):
    HAND_PHOTO = 'hand_photo'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


DEFAULT_PRESIGNED_URL_EXPIRY = 3600
