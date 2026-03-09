from . import config
import fontforge
import tempfile
from typing import Optional
from subprocess import run
import json
import webbrowser
from pathlib import Path

RESULT_JSON = 'lastresult.json'
RESULT_HTML = 'lastresult.html'


def _jsonFile() -> str:
    return config._plugin_dir + '/' + RESULT_JSON


def _htmlFile() -> str:
    return config._plugin_dir + '/' + RESULT_HTML


def _executable() -> Optional[str]:
    if config.plugin_config['backend'] == 'auto':
        return config.fontspector_path or config.fontbakery_path
    elif config.plugin_config['backend'] == 'fontbakery':
        return config.fontbakery_path
    elif config.plugin_config['backend'] == 'fontspector':
        return config.fontspector_path
    else:  # invalid!
        return None


def enabled(u, font) -> bool:
    return bool(_executable())


def _cmdline(filename: str) -> list[str]:
    if _executable():
        isFontSpector = (_executable() == config.fontspector_path)
        cmdline = [_executable()]
        if isFontSpector:
            cmdline.append('-p')
            cmdline.append(config.plugin_config['profile'])
        else:
            cmdline.append('check-' + config.plugin_config['profile'])
        cmdline.append('-q')
        cmdline.append('--full-lists')
        cmdline.append('-l')
        cmdline.append('info' if isFontSpector else 'INFO')
        cmdline.append('--configuration')
        cmdline.append(config.fontSpectorConfigFile() if isFontSpector else config.fontBakeryConfigFile())
        cmdline.append('--json')
        cmdline.append(_jsonFile())
        cmdline.append('--html')
        cmdline.append(_htmlFile())
        cmdline.append(filename)
        return cmdline
    else:
        raise RuntimeError('neither Fontbakery nor Fontspector available')


def _outroTitle(summary: dict) -> str:
    if 'ERROR' in summary and summary['ERROR'] > 0:
        return 'Error'
    elif 'FATAL' in summary and summary['FATAL'] > 0:
        return 'Check failed'
    elif 'FAIL' in summary and summary['FAIL'] > 0:
        return 'Check failed'
    else:
        return 'Check passed'


def _outroMessage(summary: dict) -> str:
    if 'ERROR' in summary and summary['ERROR'] > 0:
        return 'There ' + ('are errors' if summary['ERROR'] > 1 else 'is an error') + 'during check.'
    elif 'FATAL' in summary and summary['FATAL'] > 0:
        return 'Check failed with ' + ('severe issues' if summary['FATAL'] > 1 else 'a severe issue') + '.'
    elif 'FAIL' in summary and summary['FAIL'] > 0:
        return 'Check failed with ' + ('some issues' if summary['FAIL'] > 1 else 'an issue') + '.'
    elif 'WARN' in summary and summary['WARN'] > 0:
        return 'Check passed, but with ' + ('warnings' if summary['WARN'] > 1 else 'a warning') + '.'
    else:
        return 'Check passed.'


def _outroResultText(summary: dict) -> str:
    def toString(key: str, label: str) -> str:
        if key in summary and summary[key] > 0:
            return label + ' ' + str(summary[key])
        else:
            return label + ' 0'

    return ', '.join(
        toString(x[0], x[1]) for x in [
            ('ERROR', '💥'),
            ('FATAL', '☠'),
            ('FAIL', '🔥'),
            ('WARN', '⚠️'),
            ('INFO', 'ℹ️'),
            ('SKIP', '⏩'),
            ('PASS', '✅'),
        ]
    )


def _outro(filename: str):
    isFontSpector = (_executable() == config.fontspector_path)
    with open(_jsonFile(), 'r') as file:
        jsonDoc = json.load(file)
        summary = jsonDoc['summary'] if isFontSpector else jsonDoc['result']
        fontforge.logWarning(filename + ': ' + _outroResultText(summary))
        ans = fontforge.ask(
            _outroTitle(summary),
            _outroMessage(summary) + '\n'
            'Would you like to open details with the browser?',
            ['_Yes', '_No'])
        if ans == 0:
            webbrowser.open('file://' + _htmlFile(), 1)


def _run_check_direct(font: fontforge.font):
    run(_cmdline(font.path))
    _outro(Path(font.path).name)


def _run_check_tmpfile(font: fontforge.font):
    with tempfile.TemporaryDirectory() as tmpdir:
        changed = font.changed
        basename = (
            (font.default_base_filename or font.cidfontname or font.fontname) +
            '.' + config.plugin_config['check_as']
        )
        testfile = tmpdir + '/' + basename
        font.generate(testfile)
        font.changed = changed
        run(_cmdline(testfile))
        _outro(basename)


def run_check(u, font: fontforge.font):
    config.saveConf()
    if any(font.path.endswith(x) for x in ['.ttf', '.otf', '.ufo', '.ufo2', '.ufo3']):
        if font.changed:
            ans = fontforge.ask(
                'Font has been changed',
                'The font\n' + font.path + '\n'
                'has unsaved changes.\n'
                'How would you like to check?',
                ['Expor_t a temporary file', 'Check _existing font'],
            )
            if ans == 0:
                _run_check_tmpfile(font)
            else:
                _run_check_direct(font)
        else:
            _run_check_direct(font)
    else:
        _run_check_tmpfile(font)
