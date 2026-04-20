#!/usr/bin/env bash

set -euo pipefail

APP_NAME="EG Labeling"
DESKTOP_FILE_NAME="Labeling.desktop"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing $APP_NAME from: $CURRENT_DIR"

PYTHON_INTERPRETER="$(type -a python3 | grep -v 'conda' | head -n 1 | awk '{print $NF}')"

if [[ -z "${PYTHON_INTERPRETER}" ]]; then
    echo "python3 not found"
    exit 1
fi

PYTHON_VERSION="$("$PYTHON_INTERPRETER" --version | grep -oP 'Python \K\d+\.\d+')"
VENV_PACKAGE_NAME="python${PYTHON_VERSION}-venv"

echo "Using Python: $PYTHON_INTERPRETER"
echo "Installing system dependencies..."

sudo apt update
sudo apt install -y \
    "$VENV_PACKAGE_NAME" \
    python3-venv \
    python3-pip \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-randr0 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libgl1 \
    libegl1 \
    xdg-utils

echo "Creating virtual environment..."

"$PYTHON_INTERPRETER" -m venv "$CURRENT_DIR/venv"
source "$CURRENT_DIR/venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$CURRENT_DIR/requirements.txt"

echo "Creating desktop shortcut..."

DESKTOP_PATH="$(xdg-user-dir DESKTOP)"
DESKTOP_FILE="$DESKTOP_PATH/$DESKTOP_FILE_NAME"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Exec=bash -c 'cd "$CURRENT_DIR" && "$CURRENT_DIR/venv/bin/python" -m annotation_tool'
Icon=$CURRENT_DIR/icon.png
Terminal=false
StartupNotify=true
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

echo "Go to the Desktop, right click on the Labeling.desktop file and click Allow Launching and press ENTER to continue"
read _

echo "Congratulations, now you can use the annotation tool!"
