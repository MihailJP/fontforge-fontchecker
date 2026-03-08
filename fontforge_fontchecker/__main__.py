import fontforge
from . import config


def dummyFunc(u, glyph):
    fontforge.postNotice("FontForge Plugin Template", "Hello, world!")


def fontforge_plugin_config(**_):
    config.configInterface()


def fontforge_plugin_init(preferences_path=None, **_):
    config.checkFontTools()
    config.loadConf(preferences_path)

    fontforge.registerMenuItem(
        callback=dummyFunc,
        enable=lambda *_: False,
        context="Font",
        name="Check font"
    )
