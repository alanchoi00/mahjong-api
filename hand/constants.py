from enum import Enum


class HandSource(Enum):
    CAMERA = 'camera'
    MANUAL = 'manual'
    IMPORT = 'import'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
