# Ink/Stitch Development Environment Setup

This guide covers setting up a development environment for Ink/Stitch on Ubuntu 22.04+ (tested on Ubuntu 24.04).

## Quick Start

Run the automated setup script:

```bash
./scripts/setup-dev.sh
```

This handles everything. For manual setup or troubleshooting, see below.

---

## Prerequisites

- **Ubuntu 22.04+** (or Debian-based distro)
- **sudo access** for installing system packages
- **~5GB disk space** for all dependencies

---

## Architecture Overview

### Dual Python Environment

Ink/Stitch requires dependencies installed in **two places**:

| Environment | Location | Used By | Purpose |
|-------------|----------|---------|---------|
| **Virtualenv** | `.venv/` | `make` commands, IDE, tests | Development workflow |
| **System Python** | `~/.local/lib/python3.x/` | Inkscape | Running extensions in Inkscape |

**Why two environments?**

When you run an Ink/Stitch extension from Inkscape's **Extensions** menu, Inkscape spawns a subprocess using `/usr/bin/python3` (the system Python), **not** any virtualenv. Inkscape has no knowledge of our `.venv`. Therefore, all Ink/Stitch dependencies must be installed for both:

1. The virtualenv (for `make inx`, `make test`, IDE support)
2. System Python's user site-packages (for Inkscape to run extensions)

## Manual Setup Steps

### 1. Install mise (Tool Version Manager)

```bash
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Install System Dependencies

```bash
# Build essentials
sudo apt update
sudo apt install -y build-essential cmake pkg-config gettext git

# wxPython dependencies
sudo apt install -y libgtk-3-dev libwebkit2gtk-4.1-dev libnotify-dev \
    libsdl2-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    freeglut3-dev libjpeg-dev libpng-dev libtiff-dev libxtst-dev

# PyGObject dependencies  
sudo apt install -y libgirepository1.0-dev libcairo2-dev

# GTK development
sudo apt install -y gir1.2-gtk-3.0 libgtk-3-dev

# NumPy build dependencies
sudo apt install -y gfortran libopenblas-dev liblapack-dev

# pip for system Python
sudo apt install -y python3-pip
```

### 3. Install Inkscape

```bash
sudo add-apt-repository -y ppa:inkscape.dev/stable
sudo apt update
sudo apt install -y inkscape
```

Verify: `inkscape --version` (should be 1.4+)

### 4. Setup Python via mise

```bash
cd /path/to/inkstitch-gen-ai
mise trust --all
mise install
```

This installs Python 3.11 as specified in `.mise.toml`. The `mise trust` command is necessary because `.mise.toml` contains environment variables and tasks that need to be trusted before execution.

### 5. Create Virtual Environment

```bash
# Create venv with system site-packages access (for inkex)
python -m venv .venv --system-site-packages
source .venv/bin/activate

# Install pycairo and PyGObject first (require special handling)
pip install pycairo PyGObject==3.50.0
```

### 6. Install wxPython

wxPython must be compiled for your specific Ubuntu version. Use pre-built wheels:

```bash
# For Ubuntu 22.04 (also works on 24.04)
pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.2-cp311-cp311-linux_x86_64.whl
```

### 7. Install Remaining Dependencies

```bash
pip install -r requirements.txt
pip install pyinstaller mypy  # Dev tools
```

### 8. Install Dependencies for System Python

This is **critical** for testing in Inkscape:

```bash
/usr/bin/python3 -m pip install --user --break-system-packages -r requirements.txt
```

The `--break-system-packages` flag is required on Ubuntu 24.04+ due to [PEP 668](https://peps.python.org/pep-0668/).

### 9. Create Inkscape Extension Symlink

```bash
mkdir -p ~/.config/inkscape/extensions
ln -s $(pwd) ~/.config/inkscape/extensions/inkstitch
```

### 10. Generate INX Files

```bash
make inx
```

This generates the `.inx` files that tell Inkscape what menu items to show.

---

## Ubuntu 24.04 Specific Fixes

### libtiff5 Compatibility

wxPython wheels are built against libtiff5, but Ubuntu 24.04 only has libtiff6:

```bash
sudo ln -sf /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5
```

Or just run Inkscape from a regular terminal (Ctrl+Alt+T) outside VS Code.

---

## Verification

After setup, verify everything works:

```bash
source .venv/bin/activate

# Generate version file
make version
cat VERSION

# Generate locale files
make locales

# Generate INX files (menu definitions)
make inx
ls inx/*.inx | wc -l  # Should show 140+ files

# Run tests
make test
```

---

## Running Inkscape

```bash
# From regular terminal
inkscape

# From VS Code terminal (snap workaround)
unset GTK_PATH && inkscape &
```

Then check **Extensions → Ink/Stitch** for the extension menu.

---

## Common Commands

| Command | Description |
|---------|-------------|
| `make inx` | Generate INX extension files |
| `make test` | Run pytest test suite |
| `make dist` | Build distribution (set `BUILD=linux`) |
| `make mypy` | Run type checker |
| `make clean` | Remove generated files |
| `make locales` | Generate locale directories |
| `make version` | Generate VERSION file |

Or use mise tasks:

```bash
mise run inx
mise run test
mise run build
```

---

## Troubleshooting

### "No module named 'diskcache'" in Inkscape

Dependencies not installed for system Python. Run:

```bash
/usr/bin/python3 -m pip install --user --break-system-packages -r requirements.txt
```

### "libtiff.so.5: cannot open shared object file"

Create the symlink:

```bash
sudo ln -sf /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5
```

### Ink/Stitch not appearing in Extensions menu

1. Check symlink exists: `ls -la ~/.config/inkscape/extensions/inkstitch`
2. Check INX files exist: `ls inx/*.inx | wc -l`
3. Restart Inkscape

### "symbol lookup error" when running Inkscape

VS Code snap conflict. Either:
- Run from a regular terminal outside VS Code
- Or run: `unset GTK_PATH && inkscape`

### wxPython build fails

Use the pre-built wheel instead of building from source:

```bash
pip install https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.2-cp311-cp311-linux_x86_64.whl
```

---

## Files Created by Setup

| File/Directory | Purpose |
|----------------|---------|
| `.venv/` | Python virtual environment |
| `.mise.toml` | mise configuration (Python version, tasks) |
| `VERSION` | Generated version file |
| `inx/*.inx` | Generated Inkscape extension definitions |
| `locales/` | Generated locale directories |
| `~/.config/inkscape/extensions/inkstitch` | Symlink to this repo |

---
