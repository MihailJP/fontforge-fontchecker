import pytest
from fontforge_fontchecker import config


def _webcolors_is_unavailable() -> bool:
    try:
        import webcolors  # noqa: F401
        return False
    except ModuleNotFoundError:
        return True


webcolors_dependent = pytest.mark.skipif(
    _webcolors_is_unavailable(),
    reason="depends on 'webcolors' module",
)


@pytest.mark.parametrize(('col', 'expected'), [
    (0xf0f8ff, 'f0f8ff'),
    ('f0f8ff', 'f0f8ff'),
    ('#f0f8ff', 'f0f8ff'),
    ('aliceblue', 'aliceblue'),
    ('AliceBlue', 'AliceBlue'),
    (0xdc143c, 'dc143c'),
    ('dc143c', 'dc143c'),
    ('#dc143c', 'dc143c'),
    ('crimson', 'crimson'),
    ('Crimson', 'Crimson'),
])
def test_colorValToStr(col, expected):
    assert config._colorValToStr(col) == expected


@pytest.mark.parametrize(('col', 'expected'), [
    ('f0f8ff', 0xf0f8ff),
    ('#f0f8ff', 0xf0f8ff),
    ('aliceblue', 'aliceblue'),
    ('AliceBlue', 'AliceBlue'),
    ('dc143c', 0xdc143c),
    ('#dc143c', 0xdc143c),
    ('crimson', 'crimson'),
    ('Crimson', 'Crimson'),
])
def test_colorStrToVal(col, expected):
    assert config._colorStrToVal(col) == expected


@pytest.mark.parametrize(('col', 'expected'), [
    (0xf0f8ff, 0xf0f8ff),
    ('f0f8ff', 0xf0f8ff),
    ('#f0f8ff', 0xf0f8ff),
    pytest.param('aliceblue', 0xf0f8ff, marks=webcolors_dependent),
    pytest.param('AliceBlue', 0xf0f8ff, marks=webcolors_dependent),
    (0xdc143c, 0xdc143c),
    ('dc143c', 0xdc143c),
    ('#dc143c', 0xdc143c),
    pytest.param('crimson', 0xdc143c, marks=webcolors_dependent),
    pytest.param('Crimson', 0xdc143c, marks=webcolors_dependent),
    ('spam', -1),
])
def test_getColorVal(col, expected):
    assert config.getColorVal(col) == expected
