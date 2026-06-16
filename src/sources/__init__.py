"""Registru de surse. main.py itereaza peste ALL."""
from .aleph import Aleph
from .eurlex import EurLex
from .gdelt import Gdelt
from .hudoc import Hudoc
from .mdpress import MdPress
from .opensanctions import OpenSanctions
from .worldbank import WorldBank

ALL = [
    OpenSanctions,
    Hudoc,
    Aleph,
    EurLex,
    WorldBank,
    Gdelt,
    MdPress,
]
