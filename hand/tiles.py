"""
Mahjong Tile Constants

Provides canonical tile codes and mappings from ML model labels.
The detection task uses this mapping to convert model predictions
to standardized tile codes stored in DetectionTile.
"""

from enum import Enum


class TileCode(Enum):
    """
    Canonical tile codes for all mahjong tiles.

    Format:
    - Suited tiles: <rank><suit> (e.g., 1B = 1 Bamboo)
    - Winds: <direction>W (e.g., EW = East Wind)
    - Dragons: <color>D (e.g., RD = Red Dragon)
    - Flowers/Seasons: <num><type> (e.g., 1F = Flower 1)
    """

    # Bamboo (条/Tiao)
    BAMBOO_1 = '1B'
    BAMBOO_2 = '2B'
    BAMBOO_3 = '3B'
    BAMBOO_4 = '4B'
    BAMBOO_5 = '5B'
    BAMBOO_6 = '6B'
    BAMBOO_7 = '7B'
    BAMBOO_8 = '8B'
    BAMBOO_9 = '9B'

    # Character (万/Wan)
    CHARACTER_1 = '1C'
    CHARACTER_2 = '2C'
    CHARACTER_3 = '3C'
    CHARACTER_4 = '4C'
    CHARACTER_5 = '5C'
    CHARACTER_6 = '6C'
    CHARACTER_7 = '7C'
    CHARACTER_8 = '8C'
    CHARACTER_9 = '9C'

    # Dot (饼/Bing)
    DOT_1 = '1D'
    DOT_2 = '2D'
    DOT_3 = '3D'
    DOT_4 = '4D'
    DOT_5 = '5D'
    DOT_6 = '6D'
    DOT_7 = '7D'
    DOT_8 = '8D'
    DOT_9 = '9D'

    # Winds
    EAST_WIND = 'EW'
    SOUTH_WIND = 'SW'
    WEST_WIND = 'WW'
    NORTH_WIND = 'NW'

    # Dragons
    RED_DRAGON = 'RD'
    GREEN_DRAGON = 'GD'
    WHITE_DRAGON = 'WD'

    # Flowers
    FLOWER_1 = '1F'
    FLOWER_2 = '2F'
    FLOWER_3 = '3F'
    FLOWER_4 = '4F'

    # Seasons
    SEASON_1 = '1S'
    SEASON_2 = '2S'
    SEASON_3 = '3S'
    SEASON_4 = '4S'

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(tile.value, tile.name) for tile in cls]


# Model label to TileCode mapping
# The ML model outputs class labels that may differ from our canonical codes.
# This mapping converts model labels to TileCode enum values.
MODEL_LABEL_TO_TILE: dict[str, TileCode] = {
    # Bamboo tiles
    '1B': TileCode.BAMBOO_1,
    '2B': TileCode.BAMBOO_2,
    '3B': TileCode.BAMBOO_3,
    '4B': TileCode.BAMBOO_4,
    '5B': TileCode.BAMBOO_5,
    '6B': TileCode.BAMBOO_6,
    '7B': TileCode.BAMBOO_7,
    '8B': TileCode.BAMBOO_8,
    '9B': TileCode.BAMBOO_9,
    # Character tiles
    '1C': TileCode.CHARACTER_1,
    '2C': TileCode.CHARACTER_2,
    '3C': TileCode.CHARACTER_3,
    '4C': TileCode.CHARACTER_4,
    '5C': TileCode.CHARACTER_5,
    '6C': TileCode.CHARACTER_6,
    '7C': TileCode.CHARACTER_7,
    '8C': TileCode.CHARACTER_8,
    '9C': TileCode.CHARACTER_9,
    # Dot tiles
    '1D': TileCode.DOT_1,
    '2D': TileCode.DOT_2,
    '3D': TileCode.DOT_3,
    '4D': TileCode.DOT_4,
    '5D': TileCode.DOT_5,
    '6D': TileCode.DOT_6,
    '7D': TileCode.DOT_7,
    '8D': TileCode.DOT_8,
    '9D': TileCode.DOT_9,
    # Wind tiles
    'EW': TileCode.EAST_WIND,
    'SW': TileCode.SOUTH_WIND,
    'WW': TileCode.WEST_WIND,
    'NW': TileCode.NORTH_WIND,
    # Dragon tiles
    'RD': TileCode.RED_DRAGON,
    'GD': TileCode.GREEN_DRAGON,
    'WD': TileCode.WHITE_DRAGON,
    # Flower tiles
    '1F': TileCode.FLOWER_1,
    '2F': TileCode.FLOWER_2,
    '3F': TileCode.FLOWER_3,
    '4F': TileCode.FLOWER_4,
    # Season tiles
    '1S': TileCode.SEASON_1,
    '2S': TileCode.SEASON_2,
    '3S': TileCode.SEASON_3,
    '4S': TileCode.SEASON_4,
}


def label_to_tile(label: str) -> TileCode | None:
    """
    Convert a model prediction label to TileCode enum.

    Args:
        label: The class label from the ML model prediction.

    Returns:
        The TileCode enum if mapping exists, None otherwise.
    """
    return MODEL_LABEL_TO_TILE.get(label)


def is_valid_tile_code(code: str) -> bool:
    """
    Check if a tile code string is valid.

    Args:
        code: The tile code to validate.

    Returns:
        True if the code is a valid TileCode value, False otherwise.
    """
    return code in {t.value for t in TileCode}
