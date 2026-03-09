from . import config
import fontforge
import tempfile
from typing import Optional
from subprocess import run


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
        cmdline.append('test.json')
        cmdline.append('--html')
        cmdline.append('test.html')
        cmdline.append(filename)
        return cmdline
    else:
        raise RuntimeError('neither Fontbakery nor Fontspector available')


def run_check(u, font: fontforge.font):
    with tempfile.TemporaryDirectory() as tmpdir:
        config.saveConf()
        changed = font.changed
        testfile = (
            tmpdir + '/' +
            (font.default_base_filename or font.cidfontname or font.fontname) +
            '.' + config.plugin_config['check_as']
        )
        font.generate(testfile)
        font.changed = changed
        run(_cmdline(testfile))
