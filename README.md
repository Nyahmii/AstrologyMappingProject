# 🌟 Astrology Chart Generator 🌙✨

A magical desktop application for generating beautiful, customizable astrology charts — **Natal**, **Transit**, and **Synastry** — wrapped in a soft pastel "magical girl" aesthetic. Built with Python, PyQt5, and Kerykeion.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)
![Build](https://github.com/Nyahmii/AstrologyMappingProject/actions/workflows/build.yml/badge.svg)

---

## ✨ Features

- 🪐 **Natal Charts** — the exact sky at the moment of birth
- 🌍 **Transit Charts** — today's sky overlaid on a natal chart
- 💞 **Synastry Charts** — a compatibility wheel between two people
- 🎨 **Pastel Magical-Girl Theme** — every chart is recolored into a soft pastel palette
- 📖 **Plain-English Translation Tab** — every planet, cusp, aspect & lunar phase written out in words (also saved as an HTML file)
- 🕐 **12-hour AM/PM Time Entry** — with automatic 24-hour conversion
- 📁 **Recent Charts Dashboard** — double-click any saved chart to reopen it instantly
- 💾 **Custom Save Folders** — charts + English notes archive wherever you choose
- 🌐 **Swiss Ephemeris Precision** — astronomical accuracy via Kerykeion (internet needed only for geocoding)

## 🚀 Reference Images

<img width="1918" height="987" alt="image" src="https://github.com/user-attachments/assets/33f3e9e4-a0ca-4553-b88f-a94292e64132" />

<img width="1916" height="979" alt="image" src="https://github.com/user-attachments/assets/ce127100-8d18-41fc-8db5-69844ccb3518" />



## 🚀 Quick Start (run from source)

### Requirements
- Python 3.9–3.11 (3.10 recommended)
- Internet connection for city geocoding (OpenStreetMap Nominatim)

### Install & Run
```bash
git clone https://github.com/Nyahmii/AstrologyMappingProject.git
cd AstrologyMappingProject
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python AstroCharter.py
```

## 📦 Download Pre-Built Executables

Head to the **[Releases page](https://github.com/Nyahmii/AstrologyMappingProject/releases)**:

| OS | File | Notes |
|---|---|---|
| Windows | `AstrologyChartGenerator-Windows.exe` | Double-click to run |
| macOS | `AstrologyChartGenerator-macOS` | Right-click → Open the first time (Gatekeeper) |
| Linux | `AstrologyChartGenerator-Linux` | `chmod +x` then run |

## 🛠️ Build Your Own Executable

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "AstrologyChartGenerator" \
  --add-data "astrology_icon.png:." \
  --hidden-import PyQt5.QtWebEngineWidgets \
  --collect-data kerykeion \
  AstroCharter.py
```
*(On Windows use `--add-data "astrology_icon.png;."` with a semicolon.)*

**Or let the cloud do it:** push a tag (`git tag v2.1.0 && git push origin v2.1.0`) and GitHub Actions builds all three platforms and publishes them to a Release automatically.

## 🧭 Using the App

1. Fill in the **Main Person** card — name, birth date, time (1–12 + AM/PM), city & country.
2. Optionally fill in the **Second Person** card for synastry charts.
3. Click a generate button: *Natal*, *Transit* (for either person), or *Synastry* (for the pair).
4. The pastel chart opens in a tab, and a **📖 English tab** opens beside it explaining every placement in plain words.
5. SVG charts + HTML translations are saved to your folder (change it with **Set Save Folder**).
6. Reopen any old chart from the **Recent Charts** list with a double-click.

## 🧱 Project Structure

```
AstroCharter.py               # The entire application
requirements.txt              # Pinned dependencies
astrology_icon.png            # Optional window icon
.github/workflows/build.yml   # Cross-platform CI/CD pipeline
```

## 🙏 Credits & Technologies

- [Kerykeion](https://github.com/g-battaglia/kerykeion) — astrological calculations & SVG chart engine (Swiss Ephemeris)
- [PyQt5 / QtWebEngine](https://www.riverbankcomputing.com/software/pyqt/) — GUI & SVG rendering
- [geopy](https://github.com/geopy/geopy) + [timezonefinder](https://github.com/jannikmi/timezonefinder) — geocoding & timezone resolution
- SVG post-processing & English translation engine — hand-rolled with ❤️

## 🐞 Troubleshooting

- **macOS blocks the app:** Right-click → Open → Open (it's unsigned, this is normal).
- **Linux won't execute the file:** `chmod +x AstrologyChartGenerator-Linux`
- **Chart looks black in some viewers:** Regenerate it — the app inlines all colors so any viewer can read them.
- **Geocoding error:** Check your internet connection; city lookup requires network access.

---

Made with 💕 and starlight by **Nyahmii**

## 🌟 Special Thanks
* **Qwen3.8-Max** 🤖✨ — For being the ultimate debugging companion, wrestling with Docker containers, solving glibc archaeology, and helping bring this pastel dream to life.

