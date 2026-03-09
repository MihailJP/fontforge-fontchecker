import fontforge
import shutil
import os
from tomlkit.toml_file import TOMLFile, TOMLDocument
from typing import Iterable, Optional

fontbakery_path = None
fontspector_path = None
fontbakery_config = TOMLDocument()
fontspector_config = TOMLDocument()

plugin_config = TOMLDocument()
_plugin_dir = ''
CONFIGFILE = 'config.toml'
FONTBAKERY_CONFIGFILE = 'fontbakery.toml'
FONTSPECTOR_CONFIGFILE = 'fontspector.toml'

profiles = {
    'opentype': 'OpenType (standards compliance)',
    'universal': 'Universal (community best practice)',
    'googlefonts': 'Google Fonts',
    'iso15008': 'ISO 15008 (in-car accessibility)',
    'fontwerk': 'Fontwerk',
    'adobefonts': 'Adobe Fonts',
    'fontbureau': 'Font Bureau',
    'microsoft': 'Microsoft',
    'notofonts': 'Noto fonts',
    'typenetwork': 'Type Network',
}
"""List of known Fontbakery/Fontspector check profile"""


def checkFontTools():
    global fontbakery_path, fontspector_path
    fontbakery_path = shutil.which('fontbakery')
    fontspector_path = shutil.which('fontspector')


def _validateConfItem(key: str, defaultVal, *, choice: Optional[Iterable] = None) -> bool:
    loaded = True
    if (key not in plugin_config) or (not isinstance(plugin_config[key], type(defaultVal))):
        plugin_config[key] = defaultVal  # load default
        loaded = False
    if choice:
        if not any(plugin_config[key] == x for x in choice):
            fontforge.logWarning("Invalid " + key + " '" + str(plugin_config[key]) + "' ignored")
            plugin_config[key] = defaultVal
    return loaded


def _validateConf():
    global profiles
    _validateConfItem('backend', 'auto', choice=['auto', 'fontbakery', 'fontspector'])
    _validateConfItem('check_as', 'ttf', choice=['ttf', 'ufo'])
    if _validateConfItem('profiles', profiles):
        profiles |= plugin_config['profiles']
    if _validateConfItem('profile', 'universal'):
        if plugin_config['profile'] not in profiles:
            profiles[plugin_config['profile']] = plugin_config['profile']
    _validateConfItem('explicit_checks', [])
    _validateConfItem('exclude_checks', [])


def fontBakeryConfigFile():
    return _plugin_dir + '/' + FONTBAKERY_CONFIGFILE


def fontSpectorConfigFile():
    return _plugin_dir + '/' + FONTSPECTOR_CONFIGFILE


def loadConf(confdir: str):
    global _plugin_dir, plugin_config, fontbakery_config, fontspector_config
    _plugin_dir = confdir
    try:
        plugin_config = TOMLFile(_plugin_dir + '/' + CONFIGFILE).read()
    except FileNotFoundError:
        pass

    _validateConf()

    try:
        fontbakery_config = TOMLFile(fontBakeryConfigFile()).read()
    except FileNotFoundError:
        pass
    try:
        fontspector_config = TOMLFile(fontSpectorConfigFile()).read()
    except FileNotFoundError:
        pass


def saveConf():
    os.makedirs(_plugin_dir, exist_ok=True)
    TOMLFile(_plugin_dir + '/' + CONFIGFILE).write(plugin_config)
    TOMLFile(_plugin_dir + '/' + FONTBAKERY_CONFIGFILE).write(fontbakery_config)
    TOMLFile(_plugin_dir + '/' + FONTSPECTOR_CONFIGFILE).write(fontspector_config)


def _writeBackendConf():
    fontspector_config['explicit_checks'] \
        = fontbakery_config['explicit_checks'] \
        = plugin_config['explicit_checks']
    fontspector_config['exclude_checks'] \
        = fontbakery_config['exclude_checks'] \
        = plugin_config['exclude_checks']
    for conf in (fontspector_config, fontbakery_config):
        for i in [x[0] for x in conf.items() if not x[1]]:
            conf.remove(i)


def configInterface():
    ans = fontforge.askMulti(
        'Configuration',
        [
            {
                'type': 'choice',
                'question': 'Backend',
                'tag': 'backend',
                'checks': True,
                'answers': [
                    {'name': p.capitalize(), 'tag': p, 'default': plugin_config['backend'] == p}
                    for p in ['auto', 'fontbakery', 'fontspector']
                ],
            },
            {
                'type': 'choice',
                'question': 'Check as',
                'tag': 'check_as',
                'checks': True,
                'answers': [
                    {'name': p, 'tag': p.lower(), 'default': plugin_config['check_as'] == p.lower()}
                    for p in ['TTF', 'UFO']
                ],
            },
            {
                'type': 'choice',
                'question': 'Profile',
                'tag': 'profile',
                'answers': [
                    {'name': p[1], 'tag': p[0], 'default': plugin_config['profile'] == p[0]}
                    for p in profiles.items()
                ],
            },
            {
                'type': 'string',
                'question': 'Explicit checks\n(comma-separated)',
                'tag': 'explicit_checks',
                'default': ','.join(plugin_config['explicit_checks']),
            },
            {
                'type': 'string',
                'question': 'Excluded checks\n(comma-separated)',
                'tag': 'exclude_checks',
                'default': ','.join(plugin_config['exclude_checks']),
            },
        ]
    )
    if ans:
        plugin_config['backend'] = ans['backend']
        plugin_config['check_as'] = ans['check_as']
        plugin_config['profile'] = ans['profile']
        plugin_config['explicit_checks'] = [a for a in (ans['explicit_checks'] or '').split(',') if a]
        plugin_config['exclude_checks'] = [a for a in (ans['exclude_checks'] or '').split(',') if a]
        _writeBackendConf()
        saveConf()
