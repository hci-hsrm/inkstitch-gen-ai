#!/bin/bash
# Ink/Stitch Development Environment Setup Script
# This script sets up a complete development environment on Ubuntu 22.04+

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ink/Stitch Development Setup Script  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID_LIKE" != *"debian"* && "$ID_LIKE" != *"ubuntu"* ]]; then
            warn "This script is designed for Ubuntu/Debian. Your OS: $ID"
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
}

install_mise() {
    if command -v mise &> /dev/null; then
        success "mise is already installed: $(mise --version)"
    else
        info "Installing mise..."
        curl https://mise.run | sh
        
        if ! grep -q "mise activate" ~/.bashrc 2>/dev/null; then
            echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
        fi
        
        export PATH="$HOME/.local/bin:$PATH"
        eval "$(~/.local/bin/mise activate bash)"
        
        success "mise installed successfully"
    fi
}

install_system_deps() {
    info "Installing system dependencies..."
    
    sudo apt-get update
    
    sudo apt-get install -y \
        build-essential \
        cmake \
        pkg-config \
        git \
        curl
    
    sudo apt-get install -y gettext
    
    sudo apt-get install -y \
        libnotify4 \
        libsdl2-dev \
        libsdl2-2.0-0 \
        glib-networking
    
    sudo apt-get install -y \
        libgirepository1.0-dev \
        libcairo2-dev \
        gir1.2-gtk-3.0
    
    sudo apt-get install -y \
        libgtk-3-dev
    
    sudo apt-get install -y \
        gfortran \
        libopenblas-dev \
        liblapack-dev
    
    if [ ! -f /usr/lib/x86_64-linux-gnu/libtiff.so.5 ]; then
        if [ -f /usr/lib/x86_64-linux-gnu/libtiff.so.6 ]; then
            info "Creating libtiff5 compatibility symlink for Ubuntu 24.04..."
            sudo ln -sf /usr/lib/x86_64-linux-gnu/libtiff.so.6 /usr/lib/x86_64-linux-gnu/libtiff.so.5
        fi
    fi
    
    success "System dependencies installed"
}

# Install Inkscape
install_inkscape() {
    if command -v inkscape &> /dev/null; then
        INKSCAPE_VERSION=$(env -i PATH=/usr/bin:/bin inkscape --version 2>/dev/null | head -1 || echo "installed")
        success "Inkscape is already installed: $INKSCAPE_VERSION"
    else
        info "Installing Inkscape..."
        
        if sudo add-apt-repository -y ppa:inkscape.dev/stable 2>/dev/null; then
            sudo apt-get update
        fi
        
        sudo apt-get install -y inkscape
        INKSCAPE_VERSION=$(env -i PATH=/usr/bin:/bin inkscape --version 2>/dev/null | head -1 || echo "installed")
        success "Inkscape installed: $INKSCAPE_VERSION"
    fi
}

# Setup Python with mise
setup_python() {
    info "Setting up Python with mise..."
    
    cd "$PROJECT_DIR"
    
    if [ -f ".mise.toml" ]; then
        mise trust --all
        mise install
        success "Python $(python --version) configured via mise"
    else
        error ".mise.toml not found in project directory"
        exit 1
    fi
}

# Create virtual environment and install Python deps
setup_python_deps() {
    info "Setting up Python virtual environment..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -d ".venv" ]; then
        python -m venv .venv --system-site-packages
        success "Virtual environment created with system site-packages access"
    else
        info "Virtual environment already exists"
    fi
    
    source .venv/bin/activate
    
    info "Upgrading pip..."
    pip install --upgrade pip wheel
    
    info "Installing pycairo and PyGObject..."
    pip install pycairo
    pip install PyGObject==3.50.0
    
    info "Installing wxPython (this may take a moment)..."
    
    UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "22.04")
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
    
    WXPYTHON_URL="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/wxPython-4.2.2-cp311-cp311-linux_x86_64.whl"
    
    pip install "$WXPYTHON_URL" || {
        warn "Pre-built wxPython wheel failed. Trying pip install (may take a long time)..."
        pip install wxPython
    }
    
    info "Installing remaining Python dependencies..."
    pip install -r requirements.txt
    
    info "Installing development tools..."
    pip install pyinstaller mypy
    
    success "Python dependencies installed"
}

verify_installation() {
    info "Verifying installation..."
    
    cd "$PROJECT_DIR"
    source .venv/bin/activate
    
    echo ""
    echo -e "${BLUE}Testing make version...${NC}"
    make version
    cat VERSION
    echo ""
    
    echo -e "${BLUE}Testing make locales...${NC}"
    make locales
    echo "Locales generated: $(ls -1 locales/ 2>/dev/null | wc -l) directories"
    echo ""
    
    echo -e "${BLUE}Testing make inx...${NC}"
    make inx
    echo "INX files generated: $(ls -1 inx/*.inx 2>/dev/null | wc -l) files"
    echo ""
    
    success "All verifications passed!"
}

# Install Python dependencies for system Python (used by Inkscape)
# 
# IMPORTANT: Inkscape uses the SYSTEM Python interpreter, not our virtualenv.
# When you run an extension from Inkscape's Extensions menu, Inkscape spawns
# a subprocess using /usr/bin/python3 (the system Python), NOT the Python
# in our .venv. This means all Ink/Stitch dependencies must also be installed
# for the system Python.
#
# The virtualenv is still useful for:
#   - Running make commands (make inx, make test, etc.)
#   - Development with IDE integration
#   - Building distribution packages
#
# But for testing in Inkscape, we need deps in both places.
setup_system_python_deps() {
    info "Installing Python dependencies for system Python (used by Inkscape)..."
    
    SYSTEM_PYTHON=$(which /usr/bin/python3)
    SYSTEM_PY_VERSION=$($SYSTEM_PYTHON --version 2>&1)
    info "System Python: $SYSTEM_PY_VERSION"
    
    info "Installing to user site-packages (~/.local/lib/python3.x/site-packages)..."
    
    $SYSTEM_PYTHON -m pip install --user --break-system-packages -r "$PROJECT_DIR/requirements.txt" || {
        error "Failed to install system Python dependencies"
        warn "You may need to install python3-pip: sudo apt install python3-pip"
        return 1
    }
    
    success "System Python dependencies installed"
    info "Inkscape will now be able to run Ink/Stitch extensions"
}

# Create symlink in Inkscape extensions directory
#
# This symlink makes Inkscape discover Ink/Stitch as an extension.
# Inkscape scans ~/.config/inkscape/extensions/ for extension folders
# containing .inx files, and adds them to the Extensions menu.
setup_inkscape_symlink() {
    info "Setting up Inkscape extension symlink..."
    
    INKSCAPE_EXT_DIR="$HOME/.config/inkscape/extensions"
    SYMLINK_PATH="$INKSCAPE_EXT_DIR/inkstitch"
    
    mkdir -p "$INKSCAPE_EXT_DIR"
    
    if [ -L "$SYMLINK_PATH" ]; then
        CURRENT_TARGET=$(readlink -f "$SYMLINK_PATH")
        if [ "$CURRENT_TARGET" = "$PROJECT_DIR" ]; then
            success "Inkscape extension symlink already exists and points to correct location"
            return
        else
            warn "Inkscape extension symlink exists but points to: $CURRENT_TARGET"
            read -p "Replace with link to current project? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm "$SYMLINK_PATH"
            else
                warn "Skipping symlink creation"
                return
            fi
        fi
    elif [ -e "$SYMLINK_PATH" ]; then
        warn "A file/directory already exists at $SYMLINK_PATH"
        warn "Skipping symlink creation - please handle manually"
        return
    fi
    
    ln -s "$PROJECT_DIR" "$SYMLINK_PATH"
    success "Created symlink: $SYMLINK_PATH -> $PROJECT_DIR"
    info "Restart Inkscape to see Ink/Stitch under Extensions menu"
}

main() {
    echo ""
    info "Starting Ink/Stitch development environment setup..."
    echo ""
    
    check_os
    
    echo -e "${YELLOW}This script will install/configure:${NC}"
    echo "  - mise (tool version manager)"
    echo "  - System packages (build tools, libraries)"
    echo "  - Inkscape (from official PPA)"
    echo "  - Python 3.11 via mise (for make commands)"
    echo "  - Python dependencies in virtualenv (.venv)"
    echo "  - Python dependencies for system Python (for Inkscape)"
    echo "  - Symlink in ~/.config/inkscape/extensions/"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    
    echo ""
    
    install_mise
    echo ""
    
    install_system_deps
    echo ""
    
    install_inkscape
    echo ""
    
    setup_python
    echo ""
    
    setup_python_deps
    echo ""
    
    verify_installation
    echo ""
    
    setup_inkscape_symlink
    echo ""
    
    setup_system_python_deps
    echo ""
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Setup Complete!                       ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Your development environment is ready!"
    echo ""
    echo -e "${YELLOW}Understanding the dual Python setup:${NC}"
    echo "  - The .venv virtualenv is used by make commands and your IDE"
    echo "  - System Python (~/.local/) is used by Inkscape when running extensions"
    echo "  - Both have the same dependencies installed"
    echo ""
    echo "To activate the virtualenv in a new terminal:"
    echo ""
    echo -e "  ${BLUE}cd $PROJECT_DIR${NC}"
    echo -e "  ${BLUE}source .venv/bin/activate${NC}"
    echo ""
    echo "Available commands:"
    echo -e "  ${BLUE}make inx${NC}      - Generate INX files"
    echo -e "  ${BLUE}make test${NC}     - Run tests"
    echo -e "  ${BLUE}make dist${NC}     - Build distribution (set BUILD=linux)"
    echo -e "  ${BLUE}make mypy${NC}     - Type checking"
    echo ""
    echo "Or use mise tasks:"
    echo -e "  ${BLUE}mise run inx${NC}"
    echo -e "  ${BLUE}mise run test${NC}"
    echo -e "  ${BLUE}mise run build${NC}"
    echo ""
    echo "To run Inkscape (if using VS Code snap, unset GTK_PATH first):"
    echo -e "  ${BLUE}unset GTK_PATH && inkscape &${NC}"
    echo ""
}

main "$@"
