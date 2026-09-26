import fontforge

from . import config, run_check
from .translation import tr, setTranslation


def fontforge_plugin_config(**_):
    config.configInterface()


def fontforge_plugin_init(preferences_path=None, **_):
    setTranslation()
    config.checkFontTools()
    assert preferences_path is not None
    config.loadConf(preferences_path)

    fontforge.registerMenuItem(
        callback=run_check.run_check,
        enable=run_check.enabled,
        context="Font",
        submenu=tr.get("C_heck font"),
        name=tr.get("Check current font"),
    )
    fontforge.registerMenuItem(
        callback=run_check.run_check_family,
        enable=run_check.enabled,
        context="Font",
        submenu=tr.get("C_heck font"),
        name=tr.get("Check font family"),
    )
