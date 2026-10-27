#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  binutils \
  python3.10 python3-pip python3-venv libpython3.10 \
  libegl1 libgl1 libgles2 \
  libnss3 libnspr4 \
  libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 \
  libxkbcommon0 libxkbcommon-x11-0 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
  libasound2 libpango-1.0-0 libcairo2 \
  libx11-xcb1 libxcb1 libxcursor1 libxi6 libxtst6 libxss1 \
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
  libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libxcb-cursor0 \
  fonts-liberation libfontconfig1 x11-utils
python3.10 -m venv /opt/venv
. /opt/venv/bin/activate
pip install --upgrade pip
pip install "kerykeion>=4.18.5,<5.0.0" PyQt5 PyQtWebEngine geopy timezonefinder pyswisseph pyinstaller
python -c "import PyQt5.QtWebEngineWidgets; print('OK: QtWebEngine imports cleanly')"
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
# Hand the build output back to the runner user so later steps can rename/upload it
chmod -R a+rwX /work/dist /work/build 2>/dev/null || true
[ -f /work/AstrologyChartGenerator.spec ] && chmod a+rw /work/AstrologyChartGenerator.spec || true
