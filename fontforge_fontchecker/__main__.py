import fontforge
from . import config, run_check


def fontforge_plugin_config(**_):
    config.configInterface()


def fontforge_plugin_init(preferences_path=None, **_):
    config.checkFontTools()
    config.loadConf(preferences_path)

    fontforge.registerMenuItem(
        callback=run_check.run_check,
        enable=run_check.enabled,
        context="Font",
        name="Check font"
    )
