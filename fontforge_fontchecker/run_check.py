from . import config
import fontforge
import tempfile
from typing import Optional, Iterable, Union
from subprocess import run
import json
import webbrowser
from pathlib import Path
from datetime import datetime

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


def _cmdline(filename: Union[str, Iterable[str]], confPath: Optional[str] = None) -> list[str]:
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
        cmdline.append(
            confPath if confPath else
            config.fontSpectorConfigFile() if isFontSpector else config.fontBakeryConfigFile()
        )
        cmdline.append('--json')
        cmdline.append(_jsonFile())
        cmdline.append('--html')
        cmdline.append(_htmlFile())
        if isinstance(filename, Iterable):
            cmdline += list(filename)
        else:
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


def _addGlyphs(glyphsWithIssues: dict, fontfile: str, glyphname: str, glyphDataDict: dict):
    if glyphname not in glyphsWithIssues[fontfile]:
        glyphsWithIssues[fontfile][glyphname] = []
    glyphsWithIssues[fontfile][glyphname].append(glyphDataDict)


def _addGlyphDataDict_FontSpector(itemResults: str, subresult, moreinfo: list[str]) -> dict:
    return {
        'check_id': itemResults['check_id'],
        'code': subresult.get('code', ''),
        'severity': subresult['severity'],
        'moreinfo': moreinfo,
    }


def _getGlyphNamesWithIssue_FontSpector(jsonDoc) -> dict:
    glyphsWithIssues = {}
    results: dict[str, dict[str, list[dict]]] = jsonDoc['results']
    for fontfile, fileResults in results.items():
        glyphsWithIssues[fontfile] = {}
        for sectionResults in fileResults.values():
            for itemResults in sectionResults:
                for subresult in itemResults['subresults']:
                    if 'message' in subresult:
                        if 'following glyph' in subresult['message']:
                            for line in subresult['message'].splitlines():
                                if line.startswith('* '):
                                    _, glyphname, *moreinfo = line.split(' ')
                                    _addGlyphs(
                                        glyphsWithIssues,
                                        fontfile,
                                        glyphname,
                                        _addGlyphDataDict_FontSpector(itemResults, subresult, moreinfo),
                                    )
                        elif subresult['code'].endswith('-0020') or subresult['code'].endswith('-00A0'):
                            moreinfo = subresult['message'].split(' ')
                            glyphname = moreinfo[4][:-1]
                            _addGlyphs(
                                glyphsWithIssues,
                                fontfile,
                                glyphname,
                                _addGlyphDataDict_FontSpector(itemResults, subresult, moreinfo),
                            )
    return glyphsWithIssues


def _addGlyphDataDict_FontBakery(checks, logs, moreinfo: list[str]) -> dict:
    return {
        'check_id': checks['key'][1].split(':')[1].removesuffix('>'),
        'code': logs['message']['code'],
        'severity': logs['status'],
        'moreinfo': moreinfo,
    }


def _getGlyphNamesWithIssue_FontBakery(jsonDoc, filepath) -> dict:
    glyphsWithIssues = {}
    results: list[dict] = jsonDoc['sections']

    for sectionResults in results:
        for checks in sectionResults['checks']:
            if 'filename' in checks:
                fontfile = filepath
                glyphsWithIssues.setdefault(fontfile, {})
                for logs in checks['logs']:
                    if 'following glyph' in logs['message']['message']:
                        for line in logs['message']['message'].splitlines():
                            if line.lstrip().startswith('- ') or line.lstrip().startswith('* '):
                                _, glyphname, *moreinfo = line.lstrip().replace("\t", ' ').split(' ')
                                if glyphname == 'Glyph' and moreinfo[0] == 'name:':
                                    moreinfo.pop(0)
                                    glyphname = moreinfo.pop(0)
                                _addGlyphs(
                                    glyphsWithIssues,
                                    fontfile,
                                    glyphname,
                                    _addGlyphDataDict_FontBakery(checks, logs, moreinfo),
                                )
    return glyphsWithIssues


def _getGlyphNamesWithIssue(jsonDoc, filepath) -> dict:
    if _executable() == config.fontspector_path:  # isFontSpector
        return _getGlyphNamesWithIssue_FontSpector(jsonDoc)
    else:
        return _getGlyphNamesWithIssue_FontBakery(jsonDoc, filepath)


def _outroColorAndComment(font: fontforge.font, result: dict[str, list[dict]]):
    def colorMarker(font: fontforge.font, glyph, data: list[dict], level: str, color: int) -> bool:
        if level in (d['severity'] for d in data):
            font.selection.select(('more',), glyph)
            if config.plugin_config['glyph_result']['color']:
                font[glyph].color = color
            return True
        return False

    isFontSpector = (_executable() == config.fontspector_path)
    font.selection.none()
    for glyph, data in result.items():
        if glyph in font:
            if not colorMarker(font, glyph, data, 'FAIL', 0xff0000):  # TODO configuration
                colorMarker(font, glyph, data, 'WARN', 0xffff00)  # TODO configuration
            if config.plugin_config['glyph_result']['comment']:
                font[glyph].comment = '\n'.join(font[glyph].comment.splitlines() + [
                    '[{} {} result]'.format(
                        datetime.today().strftime('%Y/%m/%d %H:%M'),
                        'Fontspector' if isFontSpector else 'Fontbakery'
                    ),
                ] + [
                    '{}: {} {} {}'.format(
                        d['check_id'], d['severity'], d['code'], ' '.join(d['moreinfo']),
                    ).strip() for d in data
                ])


def _outro(font: fontforge.font, filename: str, filepath: str):
    isFontSpector = (_executable() == config.fontspector_path)
    with open(_jsonFile(), 'r') as file:
        jsonDoc = json.load(file)
    summary = jsonDoc['summary'] if isFontSpector else jsonDoc['result']
    fontforge.logWarning(filename + ': ' + _outroResultText(summary))
    glyphs = _getGlyphNamesWithIssue(jsonDoc, filepath)
    if filepath in glyphs:
        _outroColorAndComment(font, glyphs[filepath])
    ans = fontforge.ask(
        _outroTitle(summary),
        _outroMessage(summary) + '\n'
        'Would you like to open details with the browser?',
        ['_Yes', '_No'])
    if ans == 0:
        webbrowser.open('file://' + _htmlFile(), 1)


def _outro_multi(fonts: list[fontforge.font], filepaths: list[str]):
    isFontSpector = (_executable() == config.fontspector_path)
    with open(_jsonFile(), 'r') as file:
        jsonDoc = json.load(file)
    summary = jsonDoc['summary'] if isFontSpector else jsonDoc['result']
    fontforge.logWarning(
        '{} ({} font{}): {}'.format(
            _getFamilyName(fonts[0]),
            len(fonts),
            '' if len(fonts) == 1 else 's',
            _outroResultText(summary),
        )
    )
    for font, filepath in zip(fonts, filepaths):
        glyphs = _getGlyphNamesWithIssue(jsonDoc, filepath)
        if filepath in glyphs:
            _outroColorAndComment(font, glyphs[filepath])
    ans = fontforge.ask(
        _outroTitle(summary),
        _outroMessage(summary) + '\n'
        'Would you like to open details with the browser?',
        ['_Yes', '_No'])
    if ans == 0:
        webbrowser.open('file://' + _htmlFile(), 1)


def _check_git_repo(path: Path) -> Optional[Path]:
    chkPath = path.parent.absolute()
    for _ in range(len(chkPath.parts)):
        if (gitPath := chkPath.joinpath('.git')).exists():
            return gitPath
        chkPath = chkPath.parent
    return None


def _check_project_config(font: fontforge.font) -> Optional[str]:
    """Check for project-specific configuration file"""

    if _executable():
        isFontSpector = (_executable() == config.fontspector_path)
        filename = 'fontspector.toml' if isFontSpector else 'fontbakery.toml'
        p = Path(font.path)

        if gitdir := _check_git_repo(p):
            if (conffile := gitdir.parent.joinpath(filename)).exists():
                return str(conffile)

        if (conffile := p.parent.joinpath(filename)).exists():
            return str(conffile)

    return None


def _ask_project_config(font: fontforge.font) -> Optional[str]:
    projectConf = _check_project_config(font)
    if projectConf:
        ans = fontforge.ask(
            'Project-specific configuration file',
            'Project-specific configuration file\n' +
            projectConf + '\n'
            'was found. Use it?',
            ['_Yes', '_No'])
        if ans == 1:
            projectConf = None
    return projectConf


def _basename(font: fontforge.font) -> str:
    return font.default_base_filename or font.cidfontname or font.fontname


def _run_check_direct(font: fontforge.font):
    run(_cmdline(font.path, _ask_project_config(font)))
    _outro(font, Path(font.path).name, font.path)


def _run_check_tmpfile(font: fontforge.font):
    with tempfile.TemporaryDirectory() as tmpdir:
        changed = font.changed
        basename = _basename(font) + '.' + config.plugin_config['check_as']
        testfile = tmpdir + '/' + basename
        font.generate(testfile)
        font.changed = changed
        run(_cmdline(testfile, _ask_project_config(font)))
        _outro(font, basename, testfile)


def _getFamilyName(font: fontforge.font) -> str:
    if name := [string for (language, strid, string) in font.sfnt_names if language == 0x409 and strid == 16]:
        return name[0]
    elif name := [string for (language, strid, string) in font.sfnt_names if language == 0x409 and strid == 21]:
        return name[0]
    elif font.cidfamilyname:
        return font.cidfamilyname
    else:
        return font.familyname


def _tmpfileRequired(font: fontforge.font) -> Optional[bool]:
    config.saveConf()
    if not Path(font.path).exists():
        return True
    elif any(font.path.endswith(x) for x in ['.ttf', '.otf', '.ufo', '.ufo2', '.ufo3']):
        if font.changed:
            return None
        else:
            return False
    else:
        return True


def run_check(u, font: fontforge.font):
    config.saveConf()
    tmpfileRequired = _tmpfileRequired(font)
    if tmpfileRequired is None:
        ans = fontforge.ask(
            'Font has been changed',
            'The font\n' + font.path + '\n'
            'has unsaved changes.\n'
            'How would you like to check?',
            ['Expor_t a temporary file', 'Check _existing font'],
        )
        tmpfileRequired = (ans == 0)
    if tmpfileRequired:
        _run_check_direct(font)
    else:
        _run_check_tmpfile(font)


def _run_check_direct_multi(font: fontforge.font, fonts: Iterable[fontforge.font]):
    run(_cmdline([f.path for f in fonts], _ask_project_config(font)))
    _outro_multi(
        fonts,
        [f.path for f in fonts],
    )


def _run_check_tmpfile_multi(font: fontforge.font, fonts: Iterable[fontforge.font]):
    testfiles = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in fonts:
            changed = f.changed
            basename = _basename(f) + '.' + config.plugin_config['check_as']
            testfile = tmpdir + '/' + basename
            f.generate(testfile)
            f.changed = changed
            testfiles.append(testfile)
        run(_cmdline(testfiles, _ask_project_config(font)))
        _outro_multi(fonts, testfiles)


def run_check_family(u, font: fontforge.font):
    config.saveConf()
    fonts = [f for f in fontforge.fonts() if _getFamilyName(f) == _getFamilyName(font)]
    tmpfileRequired = [_tmpfileRequired(f) for f in fonts]
    if [t for t in tmpfileRequired if t is None]:
        ans = fontforge.ask(
            'Fonts have been changed',
            "At least one font in family '" + _getFamilyName(font) + "'\n"
            'has unsaved changes.\n'
            'How would you like to check?',
            ['Expor_t temporary files', 'Check _existing fonts'],
        )
        tmpfileRequired = [ans == 0]
    if not any(tmpfileRequired):
        _run_check_direct_multi(font, fonts)
    else:
        _run_check_tmpfile_multi(font, fonts)
