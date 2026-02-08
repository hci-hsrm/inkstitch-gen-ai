# Building & Packaging

This document covers how to build Ink/Stitch for development, run the test
suite, and produce distributable packages.

---

## Prerequisites

Make sure you have completed the [Installation](00-installation.md) guide
first. In particular you need:

- Python 3.11 (via mise)
- Active virtualenv (`.venv`)
- System dependencies (wxPython, GTK, …)
- Inkscape 1.4+

---

## Makefile Targets

The `Makefile` in the repo root is the single entry point for most tasks:

| Target | Command | What It Does |
|---|---|---|
| **`make inx`** | `python bin/generate-inx-files` | Renders `templates/*.xml` → `inx/*.inx` via Jinja2. |
| **`make locales`** | `bash bin/generate-translation-files` | Compiles `.po` → `.mo` locale files into `locales/`. |
| **`make version`** | `bash bin/generate-version-file` | Writes the current version string to `VERSION`. |
| **`make test`** | `pytest` | Runs the full test suite. |
| **`make mypy`** | `python -m mypy` | Runs the type checker (config in `mypy.ini`). |
| **`make style`** | `bash bin/style-check` | Lints code style. |
| **`make dist`** | version + locales + inx + PyInstaller + archives | Full release build (see below). |
| **`make distlocal`** | Auto-detects OS, sets `VERSION=local-build`, runs `distclean` then `dist`. | Quick local build for testing. |
| **`make distclean`** | Removes `build/ dist/ inx/ locales/ artifacts/` | Cleans all generated artifacts. |
| **`make clean`** | Removes `messages.po` | Cleans translation intermediates. |
| **`make messages.po`** | xgettext + pybabel | Extracts translatable strings from INX + Python. |

---

## Development Build (Day-to-Day)

For normal development you only need INX files and a symlink:

```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Generate INX files (needed after any template or extension change)
make inx

# 3. (First time only) Symlink into Inkscape
mkdir -p ~/.config/inkscape/extensions
ln -sf "$(pwd)" ~/.config/inkscape/extensions/inkstitch

# 4. Restart Inkscape — your changes are live
inkscape
```

No compilation step is needed — Inkscape runs the Python source directly.

---

## Running Tests

```bash
source .venv/bin/activate
make test          # or: pytest
make mypy          # type-checking
make style         # lint
```

Pytest configuration lives in `pytest.ini`. Tests are in the `tests/` directory.

---

### Quick Local Build

```bash
make distlocal
```

Auto-detects OS, sets `VERSION=local-build`, cleans, and builds everything.
The output lands in `artifacts/`.+

## Full Distribution Build

A distribution build produces a **self-contained, frozen binary** via
PyInstaller plus a platform-specific installer/archive.

### Step 1 — Set Environment Variables

```bash
export BUILD=linux          # or: osx, windows
export VERSION=1.0.0        # or let make derive it from git
```

### Step 2 — Build

```bash
make dist
```

This runs three stages in sequence:

#### Stage A: Generate Artifacts

```
make version   →  writes VERSION
make locales   →  compiles locales/
make inx       →  renders inx/
```

#### Stage B: PyInstaller (`bin/build-python`)

- Bundles `inkstitch.py` + all imported modules into `dist/inkstitch/`.

#### Stage C: Package (`bin/build-distribution-archives`)

Copies runtime resources into the distribution directory:

```
dist/
└── inkstitch/
    ├── bin/inkstitch          # frozen executable
    ├── inx/                   # generated INX files
    ├── fonts/                 # embroidery fonts
    ├── palettes/              # thread palettes
    ├── symbols/               # command symbols
    ├── tiles/                 # fill-pattern tiles
    ├── addons/                # extra resources
    ├── dbus/                  # D-Bus helpers
    ├── LICENSE
    └── VERSION
```

Then creates the final distributable:

| Platform | Output |
|---|---|
| Linux | `artifacts/inkstitch-<version>--linux-x86_64.sh` (self-extracting installer) |
| macOS | `.pkg` installer (optionally signed + notarized) |
| Windows | NSIS-based `.exe` installer |



---
