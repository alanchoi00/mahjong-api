from enum import Enum


class HandSource(Enum):
    CAMERA = 'camera'
    MANUAL = 'manual'
    IMPORT = 'import'
    OTHER = 'other'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class DetectionStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
