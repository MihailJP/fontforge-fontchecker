Fontforge font checker plugin
=============================

Font checker wrapper for Fontforge

This plugin adds frontend of Fontbakery or Fontspector to Fontforge.
Although Fontforge itself has built-in validation feature, these external
tools provides more useful checks.

Python 3.9 or later required.

Install
-------

```shell
pip3 install fontforge_fontchecker
```

### Make sure Fontforge Python module is usable

In interactive mode of Python, run:

```python
import fontforge
```

If it raises ``ModuleNotFoundError`` exception, install Fontforge first. If
installed, make sure the build option set that the Python module gets also
installed. If already so, Python interpreter does not recognize the module
path where the required module.

```shell
export PYTHONPATH=/path/to/fontforge/python/module:$PYTHONPATH
```

Configuration
-------------

This plugin has configuration menu. Select File > Configure Plugins... > Font
checker and click Configure to open.

Configuration will be stored in
`~/.config/fontforge/plugin/Font checker/config.toml` (for Linux.)

### Frontend configuration

#### Backend

Choose from auto (default), Fontbakery, or Fontspector. If auto,
Fontspector will be preferred.

Either or both must be installed to your system; make sure you add the
backend executables to `PATH`. It is not this plugin itself which
checks fonts.

#### Check as

Unfortunately the external check tools cannot check SFDs (Fontforge's native
file type) directly. Fonts must be exported so that the tools can check.

Choose from TTF (default) or UFO. Between these two, usually TTF
is encouraged. Fontbakery's check against UFOs is quite incomplete.

#### Result for glyphs

This plugin can highlight glyphs with issues in the font view.

Enable or disable for 'color' or 'comment.'

##### Color for FAIL and WARN

If 'color' option is enabled, set what color shall be used for respective
results. Hexadecimal color code such as #ffff00 or just ffff00. Defaults
to #ff0000 (red) for FAIL and #ffff00 (lemon) for WARN.

Optionally, color names such as 'crimson' (= #dc143c) or 'goldenrod'
(= #daa520) are accepted if [webcolors](https://pypi.org/project/webcolors/)
module is available. Color names are case-insensitive.

### Common backend configuration

#### Profile

Profiles are what specifies which set of checks will be executed. Choose from
the list. If you want to use custom profile, edit the configuration file.

Default profile is 'Universal' which checks what considered as community
best practice.

These 5 profiles are available for both Fontbakery and Fontspector
(for the latter as built-in profiles):

- OpenType (standards compliance only)
- Univarsal
- Google Fonts
- ISO 15008 (in-car accessibility)
- Fontwerk

#### Explicit checks

Comma-separated list of check IDs (or part of them) which are to be
explicitly executed. If specified, only those checks are executed.

#### Excluded checks

Comma-separated list of check IDs (or part of them) which are
not to be executed. If specified, those checks are skipped.

#### Ideal and acceptable maximum file sizes

The 'file_size' check has options on maximum file size. If ideal maximum file
size is exceeded, the test results WARN. If acceptable maximum is exceeded,
the test FAILs. Leave them blank for default value (1&nbsp;MiB and 9&nbsp;MiB
respectively.)

You may add a unit like k, KB, or KiB (case-insensitive.)
If no unit is included, it is in bytes.
Note that 1&nbsp;MB = 1,000,000 bytes and 1&nbsp;MiB = 1,048,576 bytes.

#### Overrides

**Colon**-separated list of quadruples:

- Check ID (Fontbakery only, e.g. mandatory_glyphs, transformed_components)
- Message code (e.g. empty, transformed-components)
- Status (case-insensitive, e.g. FAIL, WARN)
- Reason (any text)

Both between elements and between quadruples separate with colon.

#### Network check timeout

Fontspector and Fontbakery does some checks which requires network connection.
For example, 'fontdata_namecheck' connects to external service. Input positive
value to set explicit timeout, or zero to unset.

##### Skip network check

If this option is set, instructs the backend to skip network-dependent checks.

### Fontbakery specific configuration

#### Custom order

Comma-separated list of custom check order.

### Fontspector specific configuration

#### Explicit and excluded files

**Colon**-separated list of check IDs and file names specified alternately.
Specified checks shall be done only for or excluding specified files.

No wildcards.

#### Maximum file size of minor issue

If this maximum is exceeded, the test results FATAL.
Defaults to 10&nbsp;MiB for Google Fonts profile, or unset for Universal one.

Usage
-----

This plugin adds following items into "Tools" menu:

- Check font
  - Check current font
  - Check font family

### Check font

For TTF or UFO, check will be done against the file existing on disk.
If such file has unsaved changes, asks which you intend: checking the files
on disk or checking exported font including changes.
For other files, the font will be exported into a temporary directory to check.

**"Check current font"** checks for a single font file.

**"Check font family"** checks font family to which current font belongs.
Only opened files. Closed fonts are excluded.
Fonts with family name different from that of current one are ignored.

If checks are done against TTF files directly (rather than through temporary
files,) every font files (including closed ones) in the directory are checked
as entire family.

#### Project-specific configuration file

If there is 'fontbakery.toml' or 'fontspector.toml' (for respective font check
tools) in the same directory as the font file or the Git repository root
directory in which the font, you will be asked if you intend to use that
configuration file.

#### Highlight and add comment to glyphs with problems

When enabled by the configuration, glyphs with problems are highlighted with
red or yellow, and the result on those glyphs are added as comment.
Regardless of config, problematic glyphs will be selected.

Not all checks are supported.

#### View report

Once the check is finished, result summary is reported in warning log window,
and you are asked if you would like to view details. It will open the browser
to show the detail report.

| Symbol | Level | Explanation (from Fontbakery help text)                       |
|--------|-------|---------------------------------------------------------------|
| 💥     | ERROR | Something wrong with the font checker itself, possibly a bug. |
| ☠      | FATAL | An extremely severe issue that must be addressed immediately. |
| 🔥     | FAIL  | A problem with the font that must be fixed.                   |
| ⚠️     | WARN  | Something that you should consider addressing.                |
| ℹ️     | INFO  | Something useful, typically stats.                            |
| ⏩     | SKIP  | The check does not apply to the given font.                   |
| ✅     | PASS  | The font looks good for the given checking routine.           |

These explanation texts are from Fontbakery; also apply to Fontspector.
Symbols are the same as in HTML output.

Certain environments show the symbols as emojis.
