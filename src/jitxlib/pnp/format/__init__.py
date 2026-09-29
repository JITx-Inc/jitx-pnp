"""Rendering placements as a table, with no dependency on JITX.

Everything here takes plain :py:class:`~jitxlib.pnp.format.model.Part`
records, so the writers and the bottom-side rotation rule are testable
without a runtime.
"""

from .model import BOTTOM as BOTTOM
from .model import FIELDS as FIELDS
from .model import HEADERS as HEADERS
from .model import SPLIT_FIELDS as SPLIT_FIELDS
from .model import TOP as TOP
from .model import Part as Part
from .model import legal_stem as legal_stem
from .rotation import BottomRotation as BottomRotation
from .rotation import rotation as rotation
from .write import TableFormat as TableFormat
from .write import render as render
from .write import write as write
