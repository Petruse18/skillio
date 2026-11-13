"""Locații: distanțe și transformarea unei adrese în coordonate.

Geocodarea folosește OpenStreetMap (Nominatim), gratuit, fără cheie. Dacă nu
merge internetul, folosim centrul cartierului ales.
"""
import logging
import math

import requests

from core import config

log = logging.getLogger("skillio.geo")


def distanta_km(lat1, lon1, lat2, lon2) -> float:
    if None in (lat1, lon1, lat2, lon2):
        return 99.0
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def km(x: float) -> str:
    return f"{x * 1000:.0f} m" if x < 1 else f"{x:.1f} km".replace(".", ",")


def minute_drum(dist_km: float) -> int:
    """Estimare simplă pentru oraș: 22 km/h + 4 minute de parcare."""
    return int(round(dist_km / 22 * 60 + 4))


def coordonate(adresa: str, cartier: str) -> tuple[float, float, str]:
    """Întoarce (lat, lon, sursa). sursa = „adresa” sau „cartier”."""
    if config.GEOCODARE and adresa.strip():
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{adresa}, {config.ORAS}, Romania", "format": "json", "limit": 1},
                headers={"User-Agent": "skillio-hackathon-demo/1.0"}, timeout=4)
            js = r.json()
            if js:
                lat, lon = float(js[0]["lat"]), float(js[0]["lon"])
                if distanta_km(lat, lon, *config.CENTRU_ORAS) < 15:
                    return lat, lon, "adresa"
        except Exception as e:  # noqa: BLE001
            log.info("Geocodarea nu a mers: %s", e)
    lat, lon = config.CARTIERE.get(cartier, config.CENTRU_ORAS)
    return lat, lon, "cartier"
