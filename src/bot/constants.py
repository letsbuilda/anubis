from os import getenv
from typing import NamedTuple


class Roles(NamedTuple):
    admins = int(getenv("BOT_ROLES_ADMINS_ID"))


class Colours:
    blue = 0x0279FD
    twitter_blue = 0x1DA1F2
    bright_green = 0x01D277
    dark_green = 0x1F8B4C
    orange = 0xE67E22
    pink = 0xCF84E0
    purple = 0xB734EB
    soft_green = 0x68C290
    soft_orange = 0xF9CB54
    soft_red = 0xCD6D6D
    yellow = 0xF9F586
    python_blue = 0x4B8BBE
    python_yellow = 0xFFD43B
    grass_green = 0x66FF00
    gold = 0xE6C200

    easter_like_colours = [
        (255, 247, 0),
        (255, 255, 224),
        (0, 255, 127),
        (189, 252, 201),
        (255, 192, 203),
        (255, 160, 122),
        (181, 115, 220),
        (221, 160, 221),
        (200, 162, 200),
        (238, 130, 238),
        (135, 206, 235),
        (0, 204, 204),
        (64, 224, 208),
    ]
