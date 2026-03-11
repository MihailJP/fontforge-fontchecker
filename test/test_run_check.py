import pytest
from fontforge_fontchecker import config, run_check


@pytest.mark.parametrize(('fontspector', 'fontbakery'), [
    ('/usr/local/bin/fontspector', '/usr/local/bin/fontbakery'),
    ('/usr/local/bin/fontspector', None),
    (None, '/usr/local/bin/fontbakery'),
    (None, None),
])
def test_executable(fontspector, fontbakery):
    config._validateConf()
    tmp_config = config.plugin_config['backend']
    tmp_fontspector_path = config.fontspector_path
    tmp_fontbakery_path = config.fontbakery_path
    config.fontspector_path = fontspector
    config.fontbakery_path = fontbakery

    config.plugin_config['backend'] = 'auto'
    if fontspector:
        assert run_check._executable() == fontspector
    else:
        assert run_check._executable() == fontbakery
    config.plugin_config['backend'] = 'fontbakery'
    assert run_check._executable() == fontbakery
    config.plugin_config['backend'] = 'fontspector'
    assert run_check._executable() == fontspector
    config.plugin_config['backend'] = 'spam'
    assert run_check._executable() is None

    config.plugin_config['backend'] = tmp_config
    config.tmp_fontspector_path = tmp_fontspector_path
    config.tmp_fontbakery_path = tmp_fontbakery_path


def _result_summary(errorCnt: int, fatalCnt: int, failCnt: int, warnCnt: int) -> dict:
    summary = {}
    if errorCnt:
        summary['ERROR'] = errorCnt
    if fatalCnt:
        summary['FATAL'] = fatalCnt
    if failCnt:
        summary['FAIL'] = failCnt
    if warnCnt:
        summary['WARN'] = warnCnt
    summary['INFO'] = 3
    summary['SKIP'] = 9
    summary['PASS'] = 27
    return summary


@pytest.mark.parametrize(('errorCnt', 'errorMsg'), [(1, 'Error'), (0, None)])
@pytest.mark.parametrize(('fatalCnt', 'fatalMsg'), [(1, 'Check failed'), (0, None)])
@pytest.mark.parametrize(('failCnt', 'failMsg'), [(1, 'Check failed'), (0, None)])
@pytest.mark.parametrize(('warnCnt', 'warnMsg'), [(1, 'Check passed'), (0, 'Check passed')])
def test_outroTitle(errorCnt, fatalCnt, failCnt, warnCnt, errorMsg, fatalMsg, failMsg, warnMsg):
    assert run_check._outroTitle(
        _result_summary(errorCnt, fatalCnt, failCnt, warnCnt)
    ) == (
        errorMsg or fatalMsg or failMsg or warnMsg
    )


@pytest.mark.parametrize(('errorCnt', 'errorMsg'), [
    (5, 'There are errors'),
    (1, 'There is an error'),
    (0, None),
])
@pytest.mark.parametrize(('fatalCnt', 'fatalMsg'), [
    (5, 'failed with severe issues'),
    (1, 'failed with a severe issue'),
    (0, None),
])
@pytest.mark.parametrize(('failCnt', 'failMsg'), [
    (5, 'failed with some issues'),
    (1, 'failed with an issue'),
    (0, None),
])
@pytest.mark.parametrize(('warnCnt', 'warnMsg'), [
    (5, 'passed, but with warnings'),
    (1, 'passed, but with a warning'),
    (0, 'passed.'),
])
def test_outroMessage(errorCnt, fatalCnt, failCnt, warnCnt, errorMsg, fatalMsg, failMsg, warnMsg):
    assert (errorMsg or fatalMsg or failMsg or warnMsg) in (
        run_check._outroMessage(
            _result_summary(errorCnt, fatalCnt, failCnt, warnCnt)
        )
    )
