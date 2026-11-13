"""Nokia Network as Code: verificarea numărului, SIM swap și locația la sosire.

Fiecare funcție întoarce (rezultat, mod), unde mod e „live” când a răspuns
rețeaua Nokia și „simulat” când nu avem cheie sau apelul a eșuat. Așa demo-ul
merge și fără internet, iar pe ecran se vede sincer de unde vine rezultatul.

Cheile se pun în fișierul .env:
    NOKIA_API_KEY=...
    NOKIA_RAPIDAPI_HOST=...      (îl găsiți în consola Network as Code)
    NOKIA_NUMAR_TEST=+99999991000   (numerele din sandbox)
"""
import logging

from core import config

log = logging.getLogger("skillio.nokia")
_client = None


def activ() -> bool:
    return bool(config.NOKIA_API_KEY)


def _api():
    global _client
    if _client is None:
        from network_as_code import NetworkAsCodeApi
        kw = {"api_key": config.NOKIA_API_KEY, "timeout": 15}
        if config.NOKIA_RAPIDAPI_HOST:
            kw["rapidapi_host"] = config.NOKIA_RAPIDAPI_HOST
        _client = NetworkAsCodeApi(**kw)
    return _client


def _numar(telefon: str) -> str:
    return config.NOKIA_NUMAR_TEST or telefon


def verifica_numar(telefon: str) -> tuple[bool, str]:
    """Number Verification: numărul introdus e chiar pe acest telefon?

    Verificarea completă cere ca telefonul să fie pe date mobile (fluxul OAuth al
    operatorului). Pe laptop, la prezentare, folosim rezultatul simulat.
    """
    if activ():
        try:
            r = _api().number_verification.verify(phone_number=_numar(telefon))
            ok = getattr(r, "device_phone_number_verified", None)
            if ok is None:
                ok = bool(r.model_dump(by_alias=False).get("device_phone_number_verified", True))
            return bool(ok), "live"
        except Exception as e:  # noqa: BLE001
            log.warning("Number Verification a eșuat: %s", e)
    return True, "simulat"


def sim_schimbat_recent(telefon: str, ore: int = 240) -> tuple[bool, str]:
    """SIM Swap: a fost schimbat SIM-ul în ultimele `ore` ore? (semn de cont furat)"""
    if activ():
        try:
            r = _api().sim_swap.check(phone_number=_numar(telefon), max_age=ore)
            return bool(r.swapped), "live"
        except Exception as e:  # noqa: BLE001
            log.warning("SIM Swap a eșuat: %s", e)
    return False, "simulat"


def e_la_adresa(telefon: str, lat: float, lon: float, raza_m: int, departe_demo: bool = False) -> tuple[bool, str]:
    """Device Location Verification: telefonul e în raza de `raza_m` metri de adresă?"""
    if activ():
        try:
            from network_as_code.location import VerifyLocationRequestArea, VerifyLocationRequestDevice
            arie = {"areaType": "CIRCLE", "center": {"latitude": lat, "longitude": lon}, "radius": max(raza_m, 2000)}
            try:
                area = VerifyLocationRequestArea.model_validate(arie)
            except Exception:  # noqa: BLE001
                area = arie
            r = _api().location.verify(
                device=VerifyLocationRequestDevice(phone_number=_numar(telefon)), area=area, max_age=600)
            rez = str(getattr(r, "verification_result", "")).upper()
            return ("TRUE" in rez or "PARTIAL" in rez), "live"
        except Exception as e:  # noqa: BLE001
            log.warning("Location Verification a eșuat: %s", e)
    return (not departe_demo), "simulat"
