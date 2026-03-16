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


@pytest.mark.parametrize(('prm', 'expected'), [
    ('60', 60),
    ('-60', 0),
    ('', 0),
    ('0', 0),
    ('spam', 0),
])
def test_timeoutStrToVal(prm, expected):
    assert config._timeoutStrToVal(prm) == expected


@pytest.mark.parametrize(('prm', 'expected'), [
    (None, {}),
    ('', {}),
    (
        'has_HVAR:MyFont-VF.ttf',
        {
            'has_HVAR': ['MyFont-VF.ttf'],
        },
    ),
    (
        'has_HVAR:MyFont-VF.ttf:nested_components:MyFont.ttf:nested_components:MyFont-VF.ttf',
        {
            'has_HVAR': ['MyFont-VF.ttf'],
            'nested_components': ['MyFont.ttf', 'MyFont-VF.ttf'],
        },
    ),
    ('not enough parameters', {}),
])
def test_parseExplicitExcludeFiles(prm, expected):
    assert config._parseExplicitExcludeFiles(prm) == expected


@pytest.mark.parametrize(('prm', 'expected'), [
    (None, ''),
    ({}, ''),
    (
        {
            'has_HVAR': ['MyFont-VF.ttf'],
        },
        'has_HVAR:MyFont-VF.ttf',
    ),
    (
        {
            'has_HVAR': ['MyFont-VF.ttf'],
            'nested_components': ['MyFont.ttf', 'MyFont-VF.ttf'],
        },
        'has_HVAR:MyFont-VF.ttf:nested_components:MyFont.ttf:nested_components:MyFont-VF.ttf',
    ),
])
def test_dumpExplicitExcludeFiles(prm, expected):
    assert config._dumpExplicitExcludeFiles(prm) == expected


@pytest.mark.parametrize(('sizeexpr', 'expected'), [
    (None, None),
    ('', None),
    ('0', 0),
    ('900', 900),
    ('900b', 900),
    ('900B', 900),
    ('900o', 900),
    ('900O', 900),
    ('900k', 900_000),
    ('900kb', 900_000),
    ('900kB', 900_000),
    ('900ko', 900_000),
    ('900kO', 900_000),
    ('900K', 900_000),
    ('900Kb', 900_000),
    ('900KB', 900_000),
    ('900Ko', 900_000),
    ('900KO', 900_000),
    ('900ki', 921_600),
    ('900kib', 921_600),
    ('900kiB', 921_600),
    ('900kio', 921_600),
    ('900kiO', 921_600),
    ('900Ki', 921_600),
    ('900Kib', 921_600),
    ('900KiB', 921_600),
    ('900Kio', 921_600),
    ('900KiO', 921_600),
    ('900KiO', 921_600),
    ('1.5MiB', 1_572_864),
    ('1.5 MiB', 1_572_864),
    ('spam', ValueError),
])
def test_filesizeExpressionToInt(sizeexpr, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            config._filesizeExpressionToInt(sizeexpr)
    else:
        assert config._filesizeExpressionToInt(sizeexpr) == expected


@pytest.mark.parametrize(('prm', 'expected'), [
    (None, {}),
    ('', {}),
    (
        'mandatory_glyphs:empty:FAIL:Because I think this would be really bad, actually',
        {
            'mandatory_glyphs': [
                {
                    'code': 'empty',
                    'status': 'FAIL',
                    'reason': 'Because I think this would be really bad, actually',
                },
            ],
        },
    ),
    (
        'spam:eggs:FAIL:test1:spam:ham:WARN:test2:ham:spam:fail:test3',
        {
            'spam': [
                {
                    'code': 'eggs',
                    'status': 'FAIL',
                    'reason': 'test1',
                },
                {
                    'code': 'ham',
                    'status': 'WARN',
                    'reason': 'test2',
                },
            ],
            'ham': [
                {
                    'code': 'spam',
                    'status': 'FAIL',
                    'reason': 'test3',
                },
            ],
        },
    ),
    ('not:enough:parameters', {}),
])
def test_parseExplicitOverrides(prm, expected):
    assert config._parseExplicitOverrides(prm) == expected


@pytest.mark.parametrize(('prm', 'expected'), [
    (None, ''),
    ({}, ''),
    (
        {
            'mandatory_glyphs': [
                {
                    'code': 'empty',
                    'status': 'FAIL',
                    'reason': 'Because I think this would be really bad, actually',
                },
            ],
        },
        'mandatory_glyphs:empty:FAIL:Because I think this would be really bad, actually',
    ),
    (
        {
            'spam': [
                {
                    'code': 'eggs',
                    'status': 'FAIL',
                    'reason': 'test1',
                },
                {
                    'code': 'ham',
                    'status': 'WARN',
                    'reason': 'test2',
                },
            ],
            'ham': [
                {
                    'code': 'spam',
                    'status': 'FAIL',
                    'reason': 'test3',
                },
            ],
        },
        'spam:eggs:FAIL:test1:spam:ham:WARN:test2:ham:spam:FAIL:test3',
    ),
])
def test_dumpExplicitOverrides(prm, expected):
    assert config._dumpExplicitOverrides(prm) == expected
