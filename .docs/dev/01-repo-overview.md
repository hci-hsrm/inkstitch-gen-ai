# Repository Overview

This document gives a high-level tour of the Ink/Stitch Gen-AI repository so that
new contributors can orient themselves quickly.

---

## What Is This Repo?

This is a **fork / extension** of [Ink/Stitch](https://inkstitch.org) — an open-source
machine-embroidery design platform that lives inside
[Inkscape](https://inkscape.org) as a set of Python extensions.
The Gen-AI branch adds a **ComfyUI-backed AI image-to-SVG pipeline** on top of the
existing Ink/Stitch feature set.

---

## Top-Level Directory Map

```
.
├── inkstitch.py              # ← Entry point invoked by Inkscape
├── Makefile                  # Build orchestration (inx, locales, dist, test …)
├── requirements.txt          # Python dependencies
├── inkstitch.spec            # PyInstaller spec for frozen builds
├── VERSION                   # Generated version string
│
├── lib/                      # ★ Core Python package
│   ├── extensions/           #   Every Inkscape menu action (one file each)
│   ├── gui/                  #   wxPython GUI panels
│   │   └── ai_svg_generator/ #   GUI for the AI extension
│   ├── comfyui_adapter/      #   ComfyUI workflow builders & API glue
│   ├── elements/             #   SVG → stitch-plan element classes
│   ├── stitch_plan/          #   Stitch plan model
│   ├── stitches/             #   Low-level stitch algorithms
│   ├── inx/                  #   INX template rendering logic
│   ├── lettering/            #   Font / lettering subsystem
│   ├── threads/              #   Thread colour catalogues
│   └── …                     #   (svg, utils, debug, i18n, …)
│
├── templates/                # Jinja2 XML templates → one per extension
├── inx/                      # Generated .inx files (never edit by hand)
├── locales/                  # Generated gettext locale directories
│
├── fonts/                    # Embroidery font definitions
├── palettes/                 # Thread palette files
├── tiles/                    # Fill-pattern tile definitions
├── symbols/                  # Inkscape symbol libraries
│
├── bin/                      # Shell helpers (build, package, generate)
├── scripts/                  # Developer scripts (setup-dev.sh …)
├── tests/                    # Pytest test suite
│
├── .docs/                    # Project documentation
│   ├── dev/                  #   Developer docs (you are here)
│   └── user/                 #   End-user docs
│
├── .github/workflows/        # CI: build.yml, test.yml, translations.yml
├── .mise.toml                # mise tool-version config (Python 3.11)
└── .vscode/                  # Editor settings / launch configs
```

---

## Key Conventions

These are the main aspects to consider when adding new features, especially new AI workflows:

| Convention | Detail |
|---|---|
| **Naming** | Extension file = `snake_case.py`, class = `PascalCase`, INX template = `snake_case.xml`. All three names must be consistent. |
| **Builder pattern** | ComfyUI workflow builders use a **fluent interface** — every setter returns `self`. |
| **Introspection-driven GUI** | The settings panel reads builder method signatures at runtime to generate controls automatically. |
| **INX generation** | INX files are **generated** from Jinja2 templates (`templates/*.xml`) — never edit `inx/` directly. |

---

## Next Steps

| Topic | Document |
|---|---|
| Adding a new AI workflow | [02-adding-workflows.md](02-adding-workflows.md) |
| Building & packaging | [03-build-and-pack.md](03-build-and-pack.md) |
| Dev-environment setup | [00-installation.md](00-installation.md) |
