import fontforge


def dummyFunc(u, glyph):
    fontforge.postNotice("FontForge Plugin Template", "Hello, world!")


def fontforge_plugin_init(**kw):
    fontforge.registerMenuItem(
        callback=dummyFunc,
        enable=lambda *_: False,
        context="Font",
        name="Check font"
    )
