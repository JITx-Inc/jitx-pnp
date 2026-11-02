"""The bottom-side rotation conventions.

The three conventions coincide at exactly the angles that would hide a
mistake, so the discriminating cases below all use 45 degrees.
"""

from __future__ import annotations

import math

import pytest

from jitxlib.pnp.format import BOTTOM, TOP
from jitxlib.pnp.format.rotation import BottomRotation, resolve, rotation


@pytest.mark.parametrize("convention", list(BottomRotation))
def test_a_top_side_angle_is_the_designs_own_under_every_convention(convention):
    assert rotation(45.0, TOP, convention) == 45.0


def test_native_reports_a_bottom_angle_unchanged():
    assert rotation(45.0, BOTTOM, BottomRotation.NATIVE) == 45.0


def test_negate_reports_a_bottom_angle_negated():
    assert rotation(45.0, BOTTOM, BottomRotation.NEGATE) == 315.0


def test_flip_reports_a_bottom_angle_turned_a_half_turn():
    assert rotation(45.0, BOTTOM, BottomRotation.FLIP) == 225.0


def test_negate_is_not_the_half_turn_of_the_angle():
    """`-r` and `180 - r` differ by 180 degrees at every angle.

    Confusing the two is the mistake this exporter family has already made
    once, and it survives review because it looks like the same reflection.
    """
    for degrees in range(0, 360, 15):
        assert rotation(degrees, BOTTOM, BottomRotation.NEGATE) != (180 - degrees) % 360


def test_the_conventions_agree_only_where_the_algebra_says_they_do():
    """native == negate at 0 and 180; negate == flip at 90 and 270."""
    for degrees in range(0, 360, 5):
        native = rotation(degrees, BOTTOM, BottomRotation.NATIVE)
        negate = rotation(degrees, BOTTOM, BottomRotation.NEGATE)
        flip = rotation(degrees, BOTTOM, BottomRotation.FLIP)
        assert (native == negate) == (degrees % 180 == 0)
        assert (negate == flip) == (degrees % 180 == 90)


def test_every_angle_normalizes_into_a_single_turn():
    assert rotation(-45.0, TOP, BottomRotation.NATIVE) == 315.0
    assert rotation(450.0, TOP, BottomRotation.NATIVE) == 90.0


# The docstring on `rotation` derives each convention from the frame it
# targets. This checks the derivation against those frames as matrices rather
# than re-asserting the formula, so a plausible-looking wrong sign in either
# the code or the docstring fails here.
def test_each_convention_matches_the_frame_its_docstring_claims():
    def turn(degrees):
        radians = math.radians(degrees)
        cos, sin = math.cos(radians), math.sin(radians)
        return ((cos, -sin), (sin, cos))

    def compose(a, b):
        return tuple(
            tuple(sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2))
            for i in range(2)
        )

    def same(a, b):
        return all(abs(a[i][j] - b[i][j]) < 1e-9 for i in range(2) for j in range(2))

    mirror_x = ((-1.0, 0.0), (0.0, 1.0))  # what JITX sets for a bottom placement
    mirror_y = ((1.0, 0.0), (0.0, -1.0))  # the zero `negate` and `flip` target

    for degrees in (0, 30, 45, 90, 137, 180, 270, 315):
        placement = compose(turn(degrees), mirror_x)

        flipped = rotation(degrees, BOTTOM, BottomRotation.FLIP)
        assert same(placement, compose(turn(flipped), mirror_y))

        # the target frame writes `180 - t`, which the docstring says is `-r`
        negated = rotation(degrees, BOTTOM, BottomRotation.NEGATE)
        assert (180 - flipped) % 360 == pytest.approx(negated)


def test_an_unknown_convention_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="native, negate, flip"):
        resolve("mirror")
