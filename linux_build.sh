#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  python3.10 python3-pip python3-venv \
  libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 \
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
  libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 x11-utils
python3.10 -m venv /opt/venv
. /opt/venv/bin/activate
pip install --upgrade pip
pip install "kerykeion>=4.18.5,<5.0.0" PyQt5 PyQtWebEngine geopy timezonefinder pyswisseph pyinstaller
if [ -f astrology_icon.png ]; then
  pyinstaller --noconfirm --onefile --windowed --name "AstrologyChartGenerator" \
    --add-data "astrology_icon.png:." \
    --hidden-import PyQt5.QtWebEngineWidgets \
    --collect-data kerykeion AstroCharter.py
else
  pyinstaller --noconfirm --onefile --windowed --name "AstrologyChartGenerator" \
    --hidden-import PyQt5.QtWebEngineWidgets \
    --collect-data kerykeion AstroCharter.py
fi
