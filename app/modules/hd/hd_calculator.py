# app/modules/hd/hd_calculator.py
"""
Prawdziwy kalkulator Human Design z Swiss Ephemeris
Bazuje na implementacji z HD_v3, ale dostosowany do naszego projektu
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set, Optional
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

try:
    import swisseph as swe
    HAVE_SW = True
except Exception:
    HAVE_SW = False

# ---------- Geo & time ----------
def geocode_place(place: str) -> Tuple[float, float, str]:
    """Geokodowanie miejsca urodzenia"""
    geo = Nominatim(user_agent="hd_backend").geocode(place, addressdetails=True, language="pl")
    if not geo:
        raise ValueError("Nie znaleziono lokalizacji")
    tz = TimezoneFinder().timezone_at(lng=geo.longitude, lat=geo.latitude)
    if not tz:
        raise ValueError("Nie udało się ustalić strefy czasowej")
    return geo.latitude, geo.longitude, tz

def to_utc(dt_local: datetime, tzname: str) -> datetime:
    """Konwersja czasu lokalnego na UTC"""
    return pytz.timezone(tzname).localize(dt_local).astimezone(pytz.utc)

# ---------- Ephemeris (tropical + solar arc -88°) ----------
def set_tropical():
    """Ustawienie trybu tropical zodiac"""
    if HAVE_SW:
        swe.set_sid_mode(0, 0, 0)  # tropical

def set_sidereal():
    """Ustawienie trybu sidereal zodiac"""
    if HAVE_SW:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)  # sidereal

def julday_utc(dt_utc: datetime) -> float:
    """Konwersja daty UTC na Julian Day"""
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600)

def sun_longitude_utc(dt_utc: datetime) -> float:
    """Obliczenie długości ekliptycznej Słońca"""
    return swe.calc_ut(julday_utc(dt_utc), swe.SUN)[0][0] % 360.0

def angular_diff(a: float, b: float) -> float:
    """Różnica kątowa między dwoma długościami ekliptycznymi"""
    return (a - b + 180.0) % 360.0 - 180.0

def find_design_time_solar_arc(dt_birth_utc: datetime, arc_deg: float = 88.0) -> datetime:
    """Znalezienie czasu Design przez solar arc -88°"""
    target = (sun_longitude_utc(dt_birth_utc) - arc_deg) % 360.0
    guess = dt_birth_utc - timedelta(days=88)
    for _ in range(6):
        lon = sun_longitude_utc(guess)
        err = angular_diff(lon, target)
        if abs(err) < 0.01: 
            break
        guess -= timedelta(days=err/0.985647)
    return guess

@dataclass
class PlanetPos:
    """Pozycja planety"""
    name: str
    lon: float

BASE_PLANETS = ["Sun","Earth","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]

def calc_positions(dt_utc: datetime) -> List[PlanetPos]:
    """Obliczenie pozycji planet"""
    if not HAVE_SW:
        return []
    
    jd = julday_utc(dt_utc)
    ids = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
        "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
        "North Node": swe.TRUE_NODE, "South Node": swe.TRUE_NODE  # Węzły księżycowe
    }
    
    positions = []
    north_node_pos = None
    
    for name, planet_id in ids.items():
        try:
            xx, ret = swe.calc_ut(jd, planet_id)
            if ret >= 0:
                lon = xx[0] % 360.0
                positions.append(PlanetPos(name, lon))
                if name == "North Node":
                    north_node_pos = lon
        except:
            pass
    
    # Earth jest przeciwieństwem Słońca
    sun_pos = next((p for p in positions if p.name == "Sun"), None)
    if sun_pos:
        earth_lon = (sun_pos.lon + 180.0) % 360.0
        positions.append(PlanetPos("Earth", earth_lon))
    
    # South Node jest przeciwieństwem North Node
    if north_node_pos is not None:
        south_node_lon = (north_node_pos + 180.0) % 360.0
        positions.append(PlanetPos("South Node", south_node_lon))
    
    return positions

# ---------- Human Design Gates (canonical Rave Mandala) ----------
def _d(sign_start_deg: float, deg: int, minutes: int = 0, seconds: int = 0) -> float:
    return sign_start_deg + deg + minutes / 60 + seconds / 3600

# Zodiac sign starts
AR, TA, GE, CA, LE, VI, LI, SC, SG, CP, AQ, PI = 0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330

# Each tuple: (start_degree, end_degree, gate_number)
GATE_RANGES: List[Tuple[float, float, int]] = [
    (_d(PI,28,15,0), _d(AR,3,52,30), 25), (_d(AR,3,52,30), _d(AR,9,30,0), 17),
    (_d(AR,9,30,0), _d(AR,15,7,30), 21), (_d(AR,15,7,30), _d(AR,20,45,0), 51),
    (_d(AR,20,45,0), _d(AR,26,22,30), 42), (_d(AR,26,22,30), _d(TA,2,0,0), 3),
    (_d(TA,2,0,0), _d(TA,7,37,30), 27), (_d(TA,7,37,30), _d(TA,13,15,0), 24),
    (_d(TA,13,15,0), _d(TA,18,52,30), 2), (_d(TA,18,52,30), _d(TA,24,30,0), 23),
    (_d(TA,24,30,0), _d(GE,0,7,30), 8), (_d(GE,0,7,30), _d(GE,5,45,0), 20),
    (_d(GE,5,45,0), _d(GE,11,22,30), 16), (_d(GE,11,22,30), _d(GE,17,0,0), 35),
    (_d(GE,17,0,0), _d(GE,22,27,30), 45), (_d(GE,22,37,30), _d(GE,28,15,0), 12),
    (_d(GE,28,15,0), _d(CA,3,52,30), 15), (_d(CA,3,52,30), _d(CA,9,30,0), 52),
    (_d(CA,9,30,0), _d(CA,15,7,30), 39), (_d(CA,15,7,30), _d(CA,20,45,0), 53),
    (_d(CA,20,45,0), _d(CA,26,22,30), 62), (_d(CA,26,22,30), _d(LE,2,0,0), 56),
    (_d(LE,2,0,0), _d(LE,7,37,30), 31), (_d(LE,7,37,30), _d(LE,13,15,0), 33),
    (_d(LE,13,15,0), _d(LE,18,52,30), 7), (_d(LE,18,52,30), _d(LE,24,30,0), 4),
    (_d(LE,24,30,0), _d(VI,0,7,30), 29), (_d(VI,0,7,30), _d(VI,5,45,0), 59),
    (_d(VI,5,45,0), _d(VI,11,22,30), 40), (_d(VI,11,22,30), _d(VI,17,0,0), 64),
    (_d(VI,17,0,0), _d(VI,22,37,30), 47), (_d(VI,22,37,30), _d(VI,28,15,0), 6),
    (_d(VI,28,15,0), _d(LI,3,52,30), 46), (_d(LI,3,52,30), _d(LI,9,30,0), 18),
    (_d(LI,9,30,0), _d(LI,15,7,30), 48), (_d(LI,15,7,30), _d(LI,20,45,0), 57),
    (_d(LI,20,45,0), _d(LI,26,22,30), 32), (_d(LI,26,22,30), _d(SC,2,0,0), 50),
    (_d(SC,2,0,0), _d(SC,7,37,30), 28), (_d(SC,7,37,30), _d(SC,13,15,0), 44),
    (_d(SC,13,15,0), _d(SC,18,52,30), 1), (_d(SC,18,52,30), _d(SC,24,30,0), 43),
    (_d(SC,24,30,0), _d(SG,0,7,30), 14), (_d(SG,0,7,30), _d(SG,5,45,0), 34),
    (_d(SG,5,45,0), _d(SG,11,22,30), 9), (_d(SG,11,22,30), _d(SG,17,0,0), 5),
    (_d(SG,17,0,0), _d(SG,22,37,30), 26), (_d(SG,22,37,30), _d(SG,28,15,0), 11),
    (_d(SG,28,15,0), _d(CP,3,52,30), 10), (_d(CP,3,52,30), _d(CP,9,30,0), 58),
    (_d(CP,9,30,0), _d(CP,15,7,30), 38), (_d(CP,15,7,30), _d(CP,20,45,0), 54),
    (_d(CP,20,45,0), _d(CP,26,22,30), 61), (_d(CP,26,22,30), _d(AQ,2,0,0), 60),
    (_d(AQ,2,0,0), _d(AQ,7,37,30), 41), (_d(AQ,7,37,30), _d(AQ,13,15,0), 19),
    (_d(AQ,13,15,0), _d(AQ,18,52,30), 13), (_d(AQ,18,52,30), _d(AQ,24,30,0), 49),
    (_d(AQ,24,30,0), _d(PI,0,7,30), 30), (_d(PI,0,7,30), _d(PI,5,45,0), 55),
    (_d(PI,5,45,0), _d(PI,11,22,30), 37), (_d(PI,11,22,30), _d(PI,17,0,0), 63),
    (_d(PI,17,0,0), _d(PI,22,37,30), 22), (_d(PI,22,37,30), _d(PI,28,15,0), 36),
]

def gate_bounds_for(lon: float) -> Tuple[int, float, float]:
    x = lon % 360.0
    for start, end, g in GATE_RANGES:
        if (start < end and start <= x < end) or (start > end and (x >= start or x < end)):
            return g, start, end
    return -1, 0.0, 0.0

def gate_line_for(lon: float) -> Tuple[int, int]:
    g, start, end = gate_bounds_for(lon)
    if g <= 0:
        return -1, -1
    width = (end - start) % 360.0
    if width == 0:
        return g, 1
    frac = ((lon - start) % 360.0) / width
    line = int(frac * 6.0) + 1
    return g, min(max(line, 1), 6)

# ---------- Centers & Channels (canonical) ----------
# Map channel gate pairs to their two connected centers
CHANNELS: Dict[Tuple[int, int], Tuple[str, str]] = {
    (1,8):("G","Throat"),(2,14):("G","Sacral"),(3,60):("Sacral","Root"),(4,63):("Ajna","Head"),
    (5,15):("Sacral","G"),(6,59):("Solar Plexus","Sacral"),(7,31):("G","Throat"),(9,52):("Sacral","Root"),
    (10,20):("G","Throat"),(10,34):("G","Sacral"),(10,57):("G","Spleen"),(11,56):("Ajna","Throat"),
    (12,22):("Throat","Solar Plexus"),(13,33):("G","Throat"),(14,2):("Sacral","G"),(15,5):("G","Sacral"),
    (16,48):("Throat","Spleen"),(17,62):("Ajna","Throat"),(18,58):("Spleen","Root"),(19,49):("Root","Solar Plexus"),
    (20,34):("Throat","Sacral"),(20,57):("Throat","Spleen"),(21,45):("Ego","Throat"),(23,43):("Throat","Ajna"),
    (24,61):("Ajna","Head"),(25,51):("G","Ego"),(26,44):("Ego","Spleen"),(27,50):("Sacral","Spleen"),
    (28,38):("Spleen","Root"),(29,46):("Sacral","G"),(30,41):("Solar Plexus","Root"),(32,54):("Spleen","Root"),
    (35,36):("Throat","Solar Plexus"),(37,40):("Solar Plexus","Ego"),(39,55):("Root","Solar Plexus"),(42,53):("Sacral","Root"),
    (47,64):("Ajna","Head"),
}
# Include reverse mapping for convenience
for (a, b), centers in list(CHANNELS.items()):
    CHANNELS[(b, a)] = centers

def compute_definition(active_gates: Set[int]) -> Tuple[Set[Tuple[int, int]], Set[str]]:
    """Oblicz zdefiniowane kanały oraz centra na podstawie aktywnych bramek."""
    defined_channels: Set[Tuple[int, int]] = set()
    defined_centers: Set[str] = set()
    for (g1, g2), (c1, c2) in CHANNELS.items():
        if g1 < g2 and g1 in active_gates and g2 in active_gates:
            defined_channels.add((g1, g2))
            defined_centers.update([c1, c2])
    return defined_channels, defined_centers

def _build_center_graph(defined_channels: Set[Tuple[int, int]]) -> Dict[str, Set[str]]:
    graph: Dict[str, Set[str]] = {}
    for (g1, g2) in defined_channels:
        c1, c2 = CHANNELS[(g1, g2)]
        graph.setdefault(c1, set()).add(c2)
        graph.setdefault(c2, set()).add(c1)
    return graph

def _has_motor_to_throat_path(defined_channels: Set[Tuple[int, int]]) -> bool:
    motor_centers = {"Sacral", "Solar Plexus", "Ego", "Root"}
    graph = _build_center_graph(defined_channels)
    from collections import deque
    for start in motor_centers:
        if start not in graph:
            continue
        seen = {start}
        q = deque([start])
        while q:
            u = q.popleft()
            if u == "Throat":
                return True
            for v in graph.get(u, []):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
    return False

def compute_type(defined_centers: Set[str], defined_channels: Set[Tuple[int, int]]) -> str:
    """Określ typ na podstawie sakralu i połączeń silników do Gardła."""
    if not defined_centers:
        return "Reflector"
    sacral = "Sacral" in defined_centers
    motor_to_throat = _has_motor_to_throat_path(defined_channels)
    if sacral and motor_to_throat:
        return "Manifesting Generator"
    if sacral:
        return "Generator"
    if ("Throat" in defined_centers and motor_to_throat) and not sacral:
        return "Manifestor"
    return "Projector"

def compute_authority(defined_centers: Set[str], hd_type: str) -> str:
    """Określ autorytet zgodnie z kolejnością centrów."""
    if "Solar Plexus" in defined_centers:
        return "Solar Plexus"
    if "Sacral" in defined_centers:
        return "Sacral"
    if "Spleen" in defined_centers:
        return "Splenic"
    if "Ego" in defined_centers:
        return "Ego"
    if "G" in defined_centers:
        return "Self-Projected"
    if hd_type == "Projector":
        return "Mental"
    if hd_type == "Reflector":
        return "Lunar"
    return "Unknown"

def compute_profile(sun_p_lon: float, sun_d_lon: float) -> str:
    """Profil z linii słońca (Personality/Design) według granic bramek."""
    _, lP = gate_line_for(sun_p_lon)
    _, lD = gate_line_for(sun_d_lon)
    return f"{lP}/{lD}" if (lP > 0 and lD > 0) else "—"

# ---------- Public API ----------
def compute_hd_chart(name: str, date_str: str, time_str: str, place: str, 
                     zodiac_system: str = "tropical", calculation_method: str = "degrees") -> Dict:
    """Główna funkcja obliczania Human Design"""
    if not HAVE_SW:
        raise RuntimeError("Brak pyswisseph - nie można obliczyć Human Design")
    
    # Input → times
    lat, lon, tzname = geocode_place(place)
    dt_local = datetime.fromisoformat(f"{date_str}T{time_str}")
    dt_utc = to_utc(dt_local, tzname)
    
    # Ustawienie systemu zodiaku
    if zodiac_system == "sidereal":
        set_sidereal()
    else:
        set_tropical()
    
    # Personality positions
    pos_pers = calc_positions(dt_utc)
    
    # Design time calculation
    if calculation_method == "degrees":
        # Solar arc -88°
        dt_utc_design = find_design_time_solar_arc(dt_utc, arc_deg=88.0)
    else:
        # -88 days
        dt_utc_design = dt_utc - timedelta(days=88)
    
    pos_des = calc_positions(dt_utc_design)
    
    def table(positions: List[PlanetPos], side: str):
        rows = []
        for p in positions:
            g, l = gate_line_for(p.lon)
            rows.append({
                "side": side, 
                "planet": p.name, 
                "lon": round(p.lon, 6),
                "gate": g if g > 0 else None, 
                "line": l if l > 0 else None
            })
        return rows
    
    rows = table(pos_pers, "Personality") + table(pos_des, "Design")
    active_gates: Set[int] = set(r["gate"] for r in rows if r["gate"])
    
    # DEBUG: Print all positions and gates
    print("🔍 DEBUG: All planet positions and gates:")
    for r in rows:
        if r["gate"]:
            print(f"  {r['side']} {r['planet']}: {r['lon']:.2f}° → Gate {r['gate']}, Line {r['line']}")
    
    print(f"🔍 DEBUG: Active gates: {sorted(active_gates)}")
    
    defined_ch, defined_cent = compute_definition(active_gates)
    
    t = compute_type(defined_cent, defined_ch)
    a = compute_authority(defined_cent, t)
    
    sun_p = next(p.lon for p in pos_pers if p.name == "Sun")
    sun_d = next(p.lon for p in pos_des if p.name == "Sun")
    profile = compute_profile(sun_p, sun_d)
    
    # Strategy based on type
    strategy_map = {
        "Generator": "To Respond",
        "Manifesting Generator": "To Respond", 
        "Manifestor": "To Inform",
        "Projector": "To Wait for Invitation",
        "Reflector": "To Wait a Lunar Cycle"
    }
    strategy = strategy_map.get(t, "Unknown")
    
    return {
        "input": {
            "name": name,
            "date": date_str,
            "time": time_str,
            "place": place,
            "lat": lat,
            "lon": lon,
            "timezone": tzname,
            "zodiac_mode": zodiac_system.title(),
            "design_mode": "-88° (łuk Słońca)" if calculation_method == "degrees" else "-88 dni"
        },
        "timestamps": {
            "utc_birth": dt_utc.isoformat(),
            "utc_design": dt_utc_design.isoformat()
        },
        "summary": {
            "type": t,
            "strategy": strategy,
            "authority": a,
            "profile": profile,
            "defined_centers": sorted(list(defined_cent)),
            "channels": sorted([f"{min(a,b)}-{max(a,b)}" for (a,b) in defined_ch]),
            "active_gates": sorted(list(active_gates))
        },
        "positions": rows
    }
