import sys
import os
import subprocess  # FIX: Added missing import
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import html
import ssl
import certifi

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
    QHBoxLayout, QWidget, QMessageBox, QGridLayout, QTabWidget, QFileDialog, 
    QScrollArea, QSizePolicy, QComboBox, QListWidget  # <--- add QListWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QIcon

from kerykeion import AstrologicalSubject, KerykeionChartSVG
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- Helper function for PyInstaller one-file mode ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _ca_bundle():
    """Locate the bundled CA certificate file, if present."""
    try:
        pem = certifi.where()
        return pem if os.path.exists(pem) else None
    except Exception:
        return None


def _make_ssl_context():
    """Build an SSL context that trusts the bundled certificates (fixes macOS)."""
    pem = _ca_bundle()
    if pem:
        return ssl.create_default_context(cafile=pem)
    return None


_CA = _ca_bundle()
if _CA:
    # Make every HTTPS library in the app (requests, urllib3, OpenSSL) use it
    os.environ.setdefault("SSL_CERT_FILE", _CA)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", _CA)

PASTEL_MAGICAL_GIRL_COLORS = {
    "#000000": "#000000", "#ffffff": "#ffffff",
    "#0000ff": "#7FBFFF", "#06537f": "#06537f", "#124500": "#124500", 
    "#150052": "#DB6EC0", "#160": "#DB6EC0", "#176": "#DB6EC0", 
    "#1f99b3": "#DB6EC0", "#26bbcf": "#8FD3FF", "#2b4972": "#A7CFFF",
    "#36d100": "#387038", "#666f06": "#387038", "#6a2d04": "#387038", 
    "#6b3d00": "#387038", "#713f04": "#387038", "#7a9810": "#387038", 
    "#984b00": "#387038", "#985a10": "#387038",
    "#6f0766": "#A080FF", "#6f76d1": "#A080FF", "#810757": "#A080FF", 
    "#510060": "#A080FF", "#5757e2": "#A080FF", "#630e73": "#A080FF",
    "#F00": "#DB6EC0", "#FF0000": "#DB6EC0", "#ff7200": "#DB6EC0", 
    "#ff7e00": "#DB6EC0", "#ff6600": "#DB6EC0",
    "#8FD3FF": "#375B73", "#2b4972": "#375B73",
    "#404040": "#000000",
    "#b14e58": "#DB6EC0", "#d59e28": "#d59e28", "#dc0000": "#DB6EC0", 
    "#520800": "#DB6EC0", "#400052": "#DB6EC0", "#47133d": "#DB6EC0",
}

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

SIGN_INFO = {
    "Aries": {"element": "Fire", "keywords": "bold, direct, pioneering",
              "blurb": "Aries is the spark of the zodiac: courageous, spontaneous and full of 'let's go!' energy. It acts first and learns by doing."},
    "Taurus": {"element": "Earth", "keywords": "steady, sensual, practical",
               "blurb": "Taurus is the builder: patient, grounded and devoted to comfort, beauty and things that last. It moves slowly but never stops."},
    "Gemini": {"element": "Air", "keywords": "curious, witty, versatile",
               "blurb": "Gemini is the messenger: quick-minded, chatty and endlessly curious. It collects ideas, stories and connections everywhere it goes."},
    "Cancer": {"element": "Water", "keywords": "nurturing, intuitive, protective",
               "blurb": "Cancer is the caretaker: soft on the outside, tough shell within, deeply tied to home, family and feeling."},
    "Leo": {"element": "Fire", "keywords": "warm, creative, big-hearted",
            "blurb": "Leo is the performer: radiant, loyal and most alive when it can create, celebrate and shine its light on others."},
    "Virgo": {"element": "Earth", "keywords": "precise, helpful, discerning",
              "blurb": "Virgo is the craftsperson: detail-loving, analytical and genuinely happy when things (and people) work at their best."},
    "Libra": {"element": "Air", "keywords": "harmonious, fair, relational",
              "blurb": "Libra is the diplomat: charm, balance and a strong sense of fairness. It thrives on partnership and beauty."},
    "Scorpio": {"element": "Water", "keywords": "intense, magnetic, transformative",
                "blurb": "Scorpio is the alchemist: deep, passionate and unafraid of truth, taboo and rebirth. All or nothing."},
    "Sagittarius": {"element": "Fire", "keywords": "adventurous, honest, philosophical",
                    "blurb": "Sagittarius is the explorer: freedom-loving, optimistic and always aiming its arrow at bigger meaning."},
    "Capricorn": {"element": "Earth", "keywords": "ambitious, disciplined, wise",
                  "blurb": "Capricorn is the strategist: patient, responsible and climbing steadily toward lasting achievement."},
    "Aquarius": {"element": "Air", "keywords": "inventive, independent, humanitarian",
                 "blurb": "Aquarius is the visionary: original, friendly and a little rebellious. It thinks of the future and the collective."},
    "Pisces": {"element": "Water", "keywords": "dreamy, compassionate, artistic",
               "blurb": "Pisces is the mystic: gentle, imaginative and porous to every feeling in the room. It dissolves boundaries with compassion."},
}

HOUSE_MEANINGS = {
    1: "self, appearance, first impressions",
    2: "money, possessions, self-worth",
    3: "communication, learning, siblings",
    4: "home, family, roots",
    5: "creativity, romance, play",
    6: "daily routines, work, health",
    7: "partnerships, marriage, contracts",
    8: "shared resources, depth, transformation",
    9: "travel, higher learning, beliefs",
    10: "career, public life, reputation",
    11: "friendships, groups, hopes",
    12: "privacy, dreams, the subconscious",
}


PLANET_MEANINGS = {
    "Sun": "your core identity, vitality and life purpose",
    "Moon": "your emotions, instincts and inner needs",
    "Mercury": "your thinking, communication and learning style",
    "Venus": "your love language, values and sense of beauty",
    "Mars": "your drive, passion and way of taking action",
    "Jupiter": "your growth, luck and big-picture beliefs",
    "Saturn": "your discipline, boundaries and life lessons",
    "Uranus": "your uniqueness, sudden changes and innovations",
    "Neptune": "your dreams, intuition and imagination",
    "Pluto": "your depth, power and transformation",
    "Chiron": "your deepest wound and healing gift",
}

ASTRO_GLYPHS = "☉☽☿♀♂♃♄♅♆♇☊☋⚷⚸♈♉♊♋♌♍♎♏♐♑♒♓"
SIGN_GLYPHS = "♈♉♊♋♌♍♎♏♐♑♒♓"


INFO_PREFIXES = ("Info:", "Latitude:", "Longitude:", "Type:",
                 "Placidus", "Zodiac:", "Lunar phase", "Apparent")


SIGN_ID_MAP = {"Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
               "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
               "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"}

ASPECT_WORDS = {"conjunction": "conjunct", "opposition": "opposite", "trine": "trine to",
                "square": "square to", "sextile": "sextile to", "quintile": "quintile to",
                "semi-sextile": "semi-sextile to", "semi-square": "semi-square to",
                "sesquiquadrate": "sesquiquadrate to", "biquintile": "biquintile to",
                "quincunx": "quincunx to"}


def parse_chart_svg(svg_path):
    """Read every fact straight off the generated chart sheet."""
    data = {"info": [], "points": [], "cusps": [], "elements": [], "aspects": []}
    try:
        raw = Path(svg_path).read_text(encoding="utf-8")
    except Exception:
        return data
    m = re.search(r'ns1:node="Main_Text"(.*?)ns1:node="Lunar_Phase"', raw, re.S)
    if m:
        data["info"] = [html.unescape(t).strip() for t in re.findall(r'<text[^>]*>([^<]+)</text>', m.group(1))]
    m = re.search(r'ns1:node="Planet_Grid"(.*?)ns1:node="Houses_Grid"', raw, re.S)
    if m:
        for chunk in m.group(1).split('<g transform="translate(0,')[1:]:
            name = re.search(r'<text text-anchor="end"[^>]*>([^<]+)</text>', chunk)
            deg = re.search(r'<text text-anchor="start" x="19"[^>]*>([^<]+)</text>', chunk)
            sign = re.search(r'<use transform="scale\(0\.3\)" ns2:href="#(\w+)"', chunk)
            if name and deg:
                data["points"].append((html.unescape(name.group(1)).strip(),
                                       html.unescape(deg.group(1)).strip(),
                                       SIGN_ID_MAP.get(sign.group(1)) if sign else None,
                                       "#retrograde" in chunk))
    m = re.search(r'ns1:node="Houses_Grid"(.*)', raw, re.S)
    if m:
        for chunk in m.group(1).split('<g transform="translate(0,')[1:]:
            num = re.search(r'Cusp[^<]*?(\d+):', chunk)
            sign = re.search(r'<use transform="scale\(0\.3\)" ns2:href="#(\w+)"', chunk)
            deg = re.search(r'<text x="53"[^>]*>([^<]+)</text>', chunk)
            if num and sign and deg:
                data["cusps"].append((int(num.group(1)), SIGN_ID_MAP.get(sign.group(1)),
                                      html.unescape(deg.group(1)).strip()))
    data["elements"] = re.findall(r'>(Fire \d+%|Earth \d+%|Air \d+%|Water \d+%)<', raw)
    for a in re.findall(r'ns1:aspectname="([^"]+)" ns1:to="([^"]+)" ns1:tooriginaldegrees="[^"]*" ns1:from="([^"]+)"', raw):
        data["aspects"].append(a)
    return data

def _fix_svg_text(m):
    tagname, attrs, content = m.group(1), m.group(2), m.group(3)
    c = content.strip()
    new_attrs = attrs
    if len(c) == 1 and c in ASTRO_GLYPHS:
        if 'font-family=' in new_attrs:
            new_attrs = re.sub(r'font-family="[^"]*"', 'font-family="DejaVu Sans"', new_attrs)
        else:
            new_attrs += ' font-family="DejaVu Sans"'
        new_attrs = re.sub(r'font-size="[^"]*"', 'font-size="11"', new_attrs)
        new_attrs = re.sub(r'font-size:\s*[\d.]+(px)?', 'font-size:11px', new_attrs)
        if 'font-size' not in new_attrs:
            new_attrs += ' font-size="11"'
        if c in SIGN_GLYPHS:
            new_attrs = re.sub(r'fill="[^"]*"', 'fill="#7A4A6F"', new_attrs)
            new_attrs = re.sub(r'fill:\s*#[0-9a-fA-F]{3,6}', 'fill:#7A4A6F', new_attrs)
    elif c.startswith(INFO_PREFIXES):
        new_attrs = re.sub(r'font-size="[^"]*"', 'font-size="12"', new_attrs)
        new_attrs = re.sub(r'font-size:\s*[\d.]+(px)?', 'font-size:12px', new_attrs)
        if 'font-size' not in new_attrs:
            new_attrs += ' font-size="12"'
    return f'<{tagname}{new_attrs}>{content}</{tagname}>'


def polish_svg_glyphs(svg_path):
    """Inline colors, fix spacing/overlaps, and keep headers readable."""
    try:
        raw = Path(svg_path).read_text(encoding="utf-8")
        vars_map = dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{3,6});', raw))
        if vars_map:
            raw = re.sub(r'var\((--[\w-]+)\)', lambda m: vars_map.get(m.group(1), m.group(0)), raw)
        raw = raw.replace('transform="translate(60,-8)"', 'transform="translate(72,-8)"')
        raw = raw.replace('transform="translate(74,-6)"', 'transform="translate(84,-6)"')
        raw = raw.replace('transform="translate(650,-20)"', 'transform="translate(662,-20)"')
        raw = re.sub(r'(<text text-anchor="start" x="19"[^>]*?font-size:)\s*[\d.]+px', r'\1 9px', raw)
        raw = re.sub(r'(<text x="53"[^>]*?font-size:)\s*[\d.]+px', r'\1 9px', raw)

        def fix_text(m):
            tag = m.group(0)
            inner = re.search(r'>([^<]*)</text>$', tag)
            content = inner.group(1).strip() if inner else ""
            if "at the time of the transit" in content:
                # Give the transit header its own line so it can never collide
                if ' y="' not in tag:
                    tag = tag.replace('<text', '<text y="14"', 1)
                size = 10 if len(content) <= 45 else 8
                tag = re.sub(r'font-size:\s*[\d.]+px', f'font-size: {size}px', tag)
                if 'font-size' not in tag:
                    tag = tag.replace('>', f' font-size="{size}">', 1)
            elif content.startswith("Points for"):
                n = len(content)
                size = 14 if n <= 22 else 11 if n <= 30 else 10 if n <= 40 else 9 if n <= 50 else 8
                tag = re.sub(r'font-size:\s*[\d.]+px', f'font-size: {size}px', tag)
            elif any(p in tag for p in INFO_PREFIXES):
                tag = re.sub(r'font-size:\s*[\d.]+px', 'font-size: 9px', tag)
            return tag

        raw = re.sub(r'<text[^>]*>[^<]*</text>', fix_text, raw)
        Path(svg_path).write_text(raw, encoding="utf-8")
    except Exception as e:
        print(f"SVG polish skipped: {e}")

def restyle_chart(default_file_path, pastel_file_path, palette):
    change_svg_colors(default_file_path, pastel_file_path, palette)
    polish_svg_glyphs(pastel_file_path)
    polish_svg_glyphs(default_file_path)


def _fmt_deg(d):
    d = float(d) % 30
    deg = int(d)
    minutes = int(round((d - deg) * 60))
    if minutes == 60:
        deg, minutes = deg + 1, 0
    return f"{deg}°{minutes:02d}'"


def _get_point(subj, key):
    obj = getattr(subj, key, None)
    if obj is not None:
        return obj
    for v in vars(subj).values():
        nm = getattr(v, "name", None)
        if isinstance(nm, str) and nm.strip().lower() == key:
            return v
    return None


def _point_sign_deg(obj):
    """Return (sign_name, degrees_string) for any kerykeion point/house object."""
    if obj is None:
        return None, None
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        lon = float(obj) % 360.0
        return ZODIAC_SIGNS[int(lon // 30) % 12], _fmt_deg(lon % 30)
    abs_lon = None
    for attr in ("abs_lon", "longitude"):
        v = getattr(obj, attr, None)
        try:
            if v is not None and not isinstance(v, bool):
                abs_lon = float(v) % 360.0
                break
        except (TypeError, ValueError):
            continue
    lon_in_sign = None
    for attr in ("lon", "cusp_lon"):
        v = getattr(obj, attr, None)
        try:
            if v is not None and not isinstance(v, bool):
                lon_in_sign = float(v)
                break
        except (TypeError, ValueError):
            continue
    sign_idx = None
    for attr in ("sign", "sign_int"):
        v = getattr(obj, attr, None)
        if isinstance(v, str) and v.strip().title() in ZODIAC_SIGNS:
            deg = lon_in_sign if lon_in_sign is not None else (abs_lon % 30 if abs_lon is not None else 0)
            return v.strip().title(), _fmt_deg(deg)
        try:
            if v is not None and not isinstance(v, bool):
                iv = int(v)
                if 0 <= iv <= 11:
                    sign_idx = iv
                    break
        except (TypeError, ValueError):
            continue
    if abs_lon is not None:
        return ZODIAC_SIGNS[int(abs_lon // 30) % 12], _fmt_deg(abs_lon % 30)
    if sign_idx is not None:
        return ZODIAC_SIGNS[sign_idx], _fmt_deg(lon_in_sign if lon_in_sign is not None else 0)
    return None, None

def _planet_sign(planet):
    """Safely read a planet's zodiac sign from any kerykeion version."""
    if planet is None:
        return None
    v = getattr(planet, "sign", None)
    if isinstance(v, str) and v in ZODIAC_SIGNS:
        return v
    if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 11:
        return ZODIAC_SIGNS[v]
    for attr in ("abs_lon", "lon", "longitude"):
        lv = getattr(planet, attr, None)
        if isinstance(lv, (int, float)) and not isinstance(lv, bool):
            return ZODIAC_SIGNS[int(float(lv) // 30) % 12]
    return None


def _ascendant_sign(subject):
    """Safely read the rising sign from any kerykeion version."""
    v = getattr(subject, "asc_sign", None)
    if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 11:
        return ZODIAC_SIGNS[v]
    if isinstance(v, str) and v in ZODIAC_SIGNS:
        return v
    for attr in ("ascendant", "first_house", "asc"):
        obj = getattr(subject, attr, None)
        if obj is None:
            continue
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            return ZODIAC_SIGNS[int(float(obj) // 30) % 12]
        for lattr in ("abs_lon", "lon", "longitude"):
            lv = getattr(obj, lattr, None)
            if isinstance(lv, (int, float)) and not isinstance(lv, bool):
                return ZODIAC_SIGNS[int(float(lv) // 30) % 12]
    houses = getattr(subject, "houses", None)
    if houses:
        first = houses[0]
        if isinstance(first, (int, float)) and not isinstance(first, bool):
            return ZODIAC_SIGNS[int(float(first) // 30) % 12]
    return None

def change_svg_colors(svg_path, output_path, color_map):
    color_map = {k.lower(): v for k, v in color_map.items()}
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        ET.register_namespace('', namespaces['svg'])
        changes_made = False
        for style_elem in root.findall(".//{http://www.w3.org/2000/svg}style"):
            css_content = style_elem.text
            if css_content:
                css_variable_regex = re.compile(r"(--[\w-]+):\s*(#[0-9a-fA-F]{3,6});")
                updated_css_content = css_content
                for match in css_variable_regex.finditer(css_content):
                    css_var, original_color = match.groups()
                    if original_color.lower() in color_map:
                        updated_color = color_map[original_color.lower()]
                        updated_css_content = updated_css_content.replace(f"{css_var}: {original_color}", f"{css_var}: {updated_color}")
                        changes_made = True
                style_elem.text = updated_css_content
        for elem in root.iter():
            if 'fill' in elem.attrib and elem.attrib['fill'].lower() in color_map:
                elem.attrib['fill'] = color_map[elem.attrib['fill'].lower()]
                changes_made = True
            if 'stroke' in elem.attrib and elem.attrib['stroke'].lower() in color_map:
                elem.attrib['stroke'] = color_map[elem.attrib['stroke'].lower()]
                changes_made = True
            if 'style' in elem.attrib:
                style = elem.attrib['style']
                updated_style = style
                color_regex = re.compile(r"(fill|stroke):\s*(#[0-9a-fA-F]{3,6})")
                for attr, color in color_regex.findall(style):
                    lower_color = color.lower()
                    if lower_color in color_map:
                        updated_style = updated_style.replace(color, color_map[lower_color])
                        changes_made = True
                elem.attrib['style'] = updated_style
        if changes_made:
            tree.write(output_path)
    except Exception as e:
        print(f"Error processing SVG file: {e}")

def get_location_info(city, state, country):
    geolocator = Nominatim(user_agent="astrology_app", ssl_context=_make_ssl_context())
    location_query = f"{city}, {state}, {country}" if state else f"{city}, {country}"
    location = geolocator.geocode(location_query)
    if location:
        latitude, longitude = location.latitude, location.longitude
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=latitude, lng=longitude)
        if timezone is None: raise ValueError(f"Timezone not found.")
        return latitude, longitude, timezone
    else:
        raise ValueError(f"Location '{location_query}' not found.")

class AstrologyChartGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Astrology Chart Generator")
        
        # FIX 1: Use resize() instead of setGeometry() for Linux/Wayland compatibility
        self.resize(1200, 800)
        self.setMinimumSize(900, 600) # Allows window to shrink gracefully
        
        icon_path = resource_path("astrology_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.init_ui()
        self.setStyleSheet(self.get_stylesheet())
        self.open_tabs = {}
        self.save_path = Path.cwd() / "generated_charts"
        self.save_folder_label.setText(f"💾 Saving to: {self.save_path}")
        self.refresh_recent_list()

    def open_recent_chart(self, item):
        path = Path(self.save_path) / item.text()
        if path.exists():
            self.preview_chart(path)

    def get_person_data(self, entries):
        try:
            name = entries["name"].text().strip()
            if not name:
                raise ValueError("Name is required.")

            year = int(entries["year"].text().strip())
            month = int(entries["month"].text().strip())
            day = int(entries["day"].text().strip())
            hour_12 = int(entries["hour"].text().strip())
            minute = int(entries["minute"].text().strip())
            ampm = entries["ampm"].currentText()

            if not 1 <= month <= 12:
                raise ValueError("Month must be between 1 and 12.")
            if not 1 <= day <= 31:
                raise ValueError("Day must be between 1 and 31.")
            if not 1 <= hour_12 <= 12:
                raise ValueError("Hour must be between 1 and 12 (pick AM or PM from the dropdown).")
            if not 0 <= minute <= 59:
                raise ValueError("Minute must be between 0 and 59.")

            if ampm == "AM":
                hour = 0 if hour_12 == 12 else hour_12
            else:
                hour = 12 if hour_12 == 12 else hour_12 + 12

            city = entries["city"].text().strip()
            state = entries["state"].text().strip() or ""
            country = entries["country"].text().strip()

            if not city or not country:
                raise ValueError("City and Country are required.")

            birthplace = ", ".join(p for p in [city, state, country] if p)
            latitude, longitude, timezone = get_location_info(city, state, country)

            return {
                "name": name, "year": year, "month": month, "day": day,
                "hour": hour, "minute": minute,
                "latitude": latitude, "longitude": longitude, "timezone": timezone,
                "birthplace": birthplace
            }
        except ValueError as ve:
            raise ValueError(f"Invalid input: {ve}")
        except Exception as e:
            raise ValueError(f"Error retrieving location: {e}")

    def set_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", str(self.save_path))
        if folder: self.save_path = Path(folder)
        self.save_folder_label.setText(f"💾 Saving to: {self.save_path}")
        self.refresh_recent_list()
        QMessageBox.information(self, "Save Folder", f"Save folder set to: {self.save_path}")

    def open_save_folder(self):
        try:
            if not self.save_path.exists(): self.save_path.mkdir(parents=True, exist_ok=True)
            save_path_str = str(self.save_path.resolve())
            if sys.platform == "win32": os.startfile(save_path_str)
            elif sys.platform == "darwin": subprocess.run(["open", save_path_str], check=True)
            else: subprocess.run(["xdg-open", save_path_str], check=True)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to open folder: {e}")

    def init_ui(self):
        main_layout = QHBoxLayout()

        # FIX 2: Wrap the left side in a QScrollArea so tall layouts don't break resizing
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # scroll instead of clip
        left_scroll.setMinimumWidth(260)
        left_scroll.setMaximumWidth(430)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        left_side_layout = QVBoxLayout()
        left_side_layout.setContentsMargins(6, 6, 6, 6)
        left_side_layout.setSpacing(8)

        # Create input groups for Main and Second Person
        self.main_person = self.create_input_group("Main Person", "#ffffe0")
        self.second_person = self.create_input_group("Second Person", "#ffe6f7")

        # Add input groups vertically
        left_side_layout.addLayout(self.main_person["layout"])
        left_side_layout.addLayout(self.second_person["layout"])

        # Buttons for generating charts (compact 2-column grid)
        button_grid = QGridLayout()
        button_grid.setSpacing(6)
        buttons = [
            ("Natal (1st)", lambda: self.generate_chart("Natal", self.main_person["entries"]), "#ffcccc", 0, 0, 1, 1),
            ("Transit (1st)", lambda: self.generate_chart("Transit", self.main_person["entries"]), "#ccffcc", 0, 1, 1, 1),
            ("Natal (2nd)", lambda: self.generate_chart("Natal", self.second_person["entries"]), "#ccccff", 1, 0, 1, 1),
            ("Transit (2nd)", lambda: self.generate_chart("Transit", self.second_person["entries"]), "#ffffcc", 1, 1, 1, 1),
            ("Generate Synastry Chart", lambda: self.generate_chart("Synastry", None), "#ffccff", 2, 0, 1, 2),
            ("Set Save Folder", self.set_save_folder, "#d4d4d4", 3, 0, 1, 1),
            ("Open Save Folder", self.open_save_folder, "#d4d4d4", 3, 1, 1, 1),
            ("Clear Main Person", self.main_person["clear"], "#ffccee", 4, 0, 1, 1),
            ("Clear Second Person", self.second_person["clear"], "#ccffee", 4, 1, 1, 1),
        ]
        for text, func, color, r, c, rs, cs in buttons:
            button_grid.addWidget(self.create_button(text, func, color), r, c, rs, cs)

        left_side_layout.addLayout(button_grid)
        # --- Bottom card: fills the empty space with something useful ---
        bottom_card = QWidget()
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(10, 8, 10, 8)
        bottom_layout.setSpacing(6)
        bottom_card.setLayout(bottom_layout)
        bottom_card.setStyleSheet(
            "QWidget { background-color: #E3F2F9; border-radius: 12px; }"
            "QLabel { background: transparent; border: none; }"
        )

        self.save_folder_label = QLabel("💾 Saving to: default folder")
        self.save_folder_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.save_folder_label.setWordWrap(True)
        bottom_layout.addWidget(self.save_folder_label)

        tips_label = QLabel(
            "✨ Quick tips\n"
            "• Birth times use 1–12 plus the AM/PM dropdown\n"
            "• Charts and their English notes save to your folder\n"
            "• Double-click a recent chart below to reopen it"
        )
        tips_label.setFont(QFont("Arial", 9))
        tips_label.setWordWrap(True)
        bottom_layout.addWidget(tips_label)

        self.recent_list = QListWidget()
        self.recent_list.setFont(QFont("Arial", 9))
        self.recent_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #CFE3EC; border-radius: 8px; }"
            "QListWidget::item { padding: 4px; }"
            "QListWidget::item:selected { background: #FBE3EF; color: #4A2B41; }"
        )
        self.recent_list.itemDoubleClicked.connect(self.open_recent_chart)
        bottom_layout.addWidget(self.recent_list, 1)

        left_side_layout.addWidget(bottom_card, 1)  # stretches to eat ALL leftover space

        # Put the left layout into a widget for the Scroll Area
        left_widget = QWidget()
        left_widget.setLayout(left_side_layout)
        left_widget.setMinimumWidth(250)
        left_scroll.setWidget(left_widget)

        main_layout.addWidget(left_scroll, 1)

        # Right-side layout for chart previews
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setStyleSheet(
            "QTabBar::tab { background: #E9B7D0; color: #4A2B41; padding: 6px 14px; "
            "border: 1px solid #C98FB0; border-bottom: none; "
            "border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }"
            "QTabBar::tab:selected { background: #FBE3EF; color: #4A2B41; }"
            "QTabBar::tab:hover { background: #F3CDE0; }"
        )
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.tab_widget, 4)

        # Set the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_input_group(self, title, color):
        frame = QWidget()
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(10, 8, 10, 8)
        frame_layout.setSpacing(6)
        frame.setLayout(frame_layout)
        frame.setStyleSheet(f"""
            QWidget {{ background-color: {color}; border-radius: 12px; }}
            QLabel {{ background: transparent; border: none; }}
            QLineEdit {{ background: #ffffff; border: 1px solid #e6c9dc; border-radius: 8px; padding: 4px 8px; font-size: 11px; }}
            QLineEdit:focus {{ border: 2px solid #DB6EC0; }}
            QComboBox {{ background: #ffffff; border: 1px solid #e6c9dc; border-radius: 8px; padding: 3px 6px; font-size: 11px; }}
        """)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(6)

        entries = {}
        def add_field(key, placeholder, row, col, rowspan=1, colspan=1):
            entry = QLineEdit()
            entry.setPlaceholderText(placeholder)
            entry.setMinimumWidth(30)
            entries[key] = entry
            grid.addWidget(entry, row, col, rowspan, colspan)

        add_field("name", "Name", 0, 0, 1, 3)
        add_field("year", "Year", 1, 0)
        add_field("month", "Month", 1, 1)
        add_field("day", "Day", 1, 2)
        add_field("hour", "Hour (1-12)", 2, 0)
        add_field("minute", "Min (0-59)", 2, 1)
        ampm = QComboBox()
        ampm.setMinimumWidth(40)
        ampm.addItems(["AM", "PM"])
        entries["ampm"] = ampm
        grid.addWidget(ampm, 2, 2)
        add_field("city", "City", 3, 0, 1, 2)
        add_field("state", "State", 3, 2)
        add_field("country", "Country", 4, 0, 1, 3)
        frame_layout.addLayout(grid)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frame)

        def clear_entries():
            for w in entries.values():
                if isinstance(w, QLineEdit):
                    w.clear()
                elif isinstance(w, QComboBox):
                    w.setCurrentIndex(0)

        return {"layout": layout, "entries": entries, "clear": clear_entries}

    def create_button(self, text, func, color):
        button = QPushButton(text)
        button.setFont(QFont("Arial", 9, QFont.Bold))
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; border: 1px solid #ffffff; border-radius: 10px; padding: 7px; }}
            QPushButton:hover {{ background-color: {self.darken_color(color)}; }}
            QPushButton:pressed {{ background-color: {self.lighten_color(color)}; }}
        """)
        button.clicked.connect(func)
        return button

    def darken_color(self, color): return color.replace("cc", "99").replace("ff", "cc")
    def lighten_color(self, color): return color.replace("cc", "ee").replace("ff", "ee")

    def generate_chart(self, chart_type, entries=None):
        try:
            output_dir = Path(self.save_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            person_data = self.get_person_data(entries) if chart_type in ["Natal", "Transit"] else None

            if chart_type == "Synastry":
                main_person_data = self.get_person_data(self.main_person["entries"])
                second_person_data = self.get_person_data(self.second_person["entries"])

                first_subject = AstrologicalSubject(
                    name=main_person_data["name"], year=main_person_data["year"],
                    month=main_person_data["month"], day=main_person_data["day"],
                    hour=main_person_data["hour"], minute=main_person_data["minute"],
                    lng=main_person_data["longitude"], lat=main_person_data["latitude"],
                    tz_str=main_person_data["timezone"], city=main_person_data["birthplace"])
                second_subject = AstrologicalSubject(
                    name=second_person_data["name"], year=second_person_data["year"],
                    month=second_person_data["month"], day=second_person_data["day"],
                    hour=second_person_data["hour"], minute=second_person_data["minute"],
                    lng=second_person_data["longitude"], lat=second_person_data["latitude"],
                    tz_str=second_person_data["timezone"], city=second_person_data["birthplace"])

                file_name = f"{main_person_data['name']} and {second_person_data['name']} - Synastry Chart.svg"
                chart = KerykeionChartSVG(first_subject, "Synastry", second_subject, new_output_directory=str(output_dir))
                chart.makeSVG()
                default_file_path = output_dir / f"{main_person_data['name']} - Synastry Chart.svg"
                pastel_file_path = output_dir / file_name
                restyle_chart(default_file_path, pastel_file_path, PASTEL_MAGICAL_GIRL_COLORS)
                self.preview_chart(pastel_file_path)
                self.open_chart_translation_tab(pastel_file_path, main_person_data["birthplace"])

            elif chart_type == "Natal":
                subject = AstrologicalSubject(
                    person_data["name"], person_data["year"], person_data["month"],
                    person_data["day"], person_data["hour"], person_data["minute"],
                    lng=person_data["longitude"], lat=person_data["latitude"],
                    tz_str=person_data["timezone"], city=person_data["birthplace"])
                chart_file = output_dir / f"{subject.name} - Natal Chart.svg"
                pastel_chart_file = output_dir / f"{subject.name} - Natal Chart (Pastel).svg"
                chart = KerykeionChartSVG(subject, new_output_directory=str(output_dir))
                chart.makeSVG()
                restyle_chart(chart_file, pastel_chart_file, PASTEL_MAGICAL_GIRL_COLORS)
                self.preview_chart(pastel_chart_file)
                self.open_chart_translation_tab(pastel_chart_file, person_data["birthplace"])

            elif chart_type == "Transit":
                now = datetime.utcnow()
                natal_subject = AstrologicalSubject(
                    person_data["name"], person_data["year"], person_data["month"],
                    person_data["day"], person_data["hour"], person_data["minute"],
                    lng=person_data["longitude"], lat=person_data["latitude"],
                    tz_str=person_data["timezone"], city=person_data["birthplace"])
                transit_subject = AstrologicalSubject(
                    "Current Planetary Positions", now.year, now.month, now.day,
                    now.hour, now.minute, lng=0.0, lat=0.0, tz_str="UTC",
                    city="Current Sky (UTC)")
                chart_file = output_dir / f"{person_data['name']} - Transit Chart.svg"
                pastel_chart_file = output_dir / f"{person_data['name']} - Transit Chart (Pastel).svg"
                chart = KerykeionChartSVG(natal_subject, "Transit", transit_subject, new_output_directory=str(output_dir))
                chart.makeSVG()
                restyle_chart(chart_file, pastel_chart_file, PASTEL_MAGICAL_GIRL_COLORS)
                self.preview_chart(pastel_chart_file)
                self.open_chart_translation_tab(pastel_chart_file, person_data["birthplace"])

            # Refresh the recent charts list AFTER successful generation
            self.refresh_recent_list()

        except ValueError as ve:
            QMessageBox.warning(self, "Input Error", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


    def refresh_recent_list(self):
        try:
            self.recent_list.clear()
            folder = Path(self.save_path)
            if folder.exists():
                files = sorted(folder.glob("*.svg"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
                for f in files:
                    self.recent_list.addItem(f.name)
        except Exception as e:
            print(f"Recent list error: {e}")
    
    
    def open_chart_translation_tab(self, svg_path, birthplace=""):
        """Translate the finished chart sheet into plain English + save an HTML copy."""
        try:
            data = parse_chart_svg(svg_path)
            stem = Path(svg_path).stem
            title = stem.replace(" - Natal Chart (Pastel)", "").replace(" (Pastel)", "")
            html_parts = ["<html><body style='font-family: Arial, sans-serif; background:#FFF7FB; color:#4A3B47; padding:28px;'>"]
            html_parts.append(f"<h1 style='color:#DB6EC0;'>📖 {title} — the complete chart in plain English</h1>")
            if birthplace:
                html_parts.append(f"<p>A map of the sky at the moment of birth, as seen from <b>{birthplace}</b>.</p>")
            if data["info"]:
                html_parts.append("<h2 style='color:#375B73;'>ℹ️ Chart facts</h2><ul>")
                html_parts += [f"<li>{line}</li>" for line in data["info"] if line and line != "Info:"]
                html_parts.append("</ul>")
            if data["points"]:
                html_parts.append("<h2 style='color:#375B73;'>🪐 Where each body was in the zodiac</h2><ul>")
                for name, deg, sign, retro in data["points"]:
                    sign_txt = f" in <b>{sign}</b>" if sign else ""
                    retro_txt = " — retrograde (appears to move backwards)" if retro else ""
                    html_parts.append(f"<li><b>{name}</b>{sign_txt} at {deg}{retro_txt}</li>")
                html_parts.append("</ul>")
            if data["cusps"]:
                html_parts.append("<h2 style='color:#375B73;'>🏠 The twelve houses (life areas)</h2><ul>")
                for num, sign, deg in data["cusps"]:
                    extra = ""
                    if num == 1:
                        extra = " — the Ascendant (rising sign), your first impression"
                    if num == 10:
                        extra = " — the Midheaven, career & public life"
                    meaning = "" if num in (1, 10) else f" — {HOUSE_MEANINGS.get(num, '')}"
                    html_parts.append(f"<li><b>House {num}</b> begins in {sign} at {deg}{extra}{meaning}.</li>")
                html_parts.append("</ul>")
            if data["elements"]:
                html_parts.append("<p><b>Element balance:</b> " + " · ".join(data["elements"]) + "</p>")
            if data["aspects"]:
                html_parts.append("<h2 style='color:#375B73;'>🔗 Aspects (angles between bodies)</h2><ul>")
                for aspect_name, to_point, from_point in data["aspects"]:
                    word = ASPECT_WORDS.get(aspect_name, aspect_name + " to")
                    html_parts.append(f"<li><b>{from_point.replace('_', ' ')}</b> is {word} <b>{to_point.replace('_', ' ')}</b></li>")
                html_parts.append("</ul>")
            html_parts.append("<h2 style='color:#375B73;'>🎡 How to read the wheel</h2><ul>"
                              "<li><b>Outer colored ring</b>: the 12 zodiac signs — each planet's symbol sits inside the sign it occupied.</li>"
                              "<li><b>Numbered wedges (1–12)</b>: the houses (Placidus system) — the life areas where each planet's energy plays out.</li>"
                              "<li><b>Lines crossing the center</b>: aspects, the angles between planets. Green lines are easy and flowing, pink/red lines are tense and motivating, yellow lines blend both.</li>"
                              "<li><b>'R' beside a planet</b>: retrograde — the planet appears to move backwards from Earth's viewpoint.</li>"
                              "<li><b>Points list (right of the wheel)</b>: the exact position of every body and house cusp, written as degrees°minutes' inside its sign.</li>"
                              "<li><b>Aspect grid (bottom right)</b>: a table of every aspect between planets, using the same colored symbols as the lines.</li>"
                              "</ul>")
            html_parts.append("</body></html>")
            page = "".join(html_parts)
            try:
                out_file = Path(self.save_path) / f"{stem} - English.html"
                out_file.write_text(page, encoding="utf-8")
            except Exception as e:
                print(f"Could not save English file: {e}")
            tab_title = f"📖 {stem} - English"
            for index in range(self.tab_widget.count()):
                if self.tab_widget.tabText(index) == tab_title:
                    self.tab_widget.setCurrentIndex(index)
                    return
            browser = QWebEngineView()
            browser.setHtml(page)
            self.tab_widget.addTab(browser, tab_title)
            self.tab_widget.setCurrentWidget(browser)
        except Exception as e:
            print(f"Translation tab error: {e}")

    def preview_chart(self, html_path):
        try:
            for index in range(self.tab_widget.count()):
                if self.tab_widget.tabText(index) == Path(html_path).stem:
                    self.tab_widget.setCurrentIndex(index)
                    return
            browser = QWebEngineView()
            browser.setUrl(QUrl.fromLocalFile(str(html_path)))
            self.tab_widget.addTab(browser, Path(html_path).name)  # ✅
            self.tab_widget.setCurrentWidget(browser)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to preview chart: {e}")

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        for path, tab in self.open_tabs.items():
            if tab == widget: del self.open_tabs[path]
        self.tab_widget.removeTab(index)

    def get_stylesheet(self):
        return (
            "QWidget { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, "
            "stop:0 rgba(255, 182, 193, 255), stop:1 rgba(173, 216, 230, 255)); "
            "font-family: 'Arial'; color: #4A3B47; } "
            "QLabel { color: #4A3B47; } "
            "QLineEdit { color: #333333; } "
            "QComboBox { color: #333333; } "
            "QListWidget { color: #333333; } "
            "QPushButton { border: 2px solid #fff; color: #333; }"
        )
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")                         # consistent styling on Win/Mac/Linux
    app.setPalette(app.style().standardPalette())  # fixed LIGHT palette -> no dark-mode leak
    window = AstrologyChartGenerator()
    window.show()
    sys.exit(app.exec_())
