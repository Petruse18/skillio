"""Setările aplicației: căi, constante, meserii, cartiere.

Tot ce se schimbă des (comision, spor de urgență, lista de meserii) stă aici,
ca să nu căutați prin cod.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

NUME_APP = "SKILLIO"
SLOGAN = "Find skills. Build trust."

# --- fișiere ---------------------------------------------------------------
DATA_DIR = ROOT / "data"
UPLOADS = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "skillio.db"

# --- reguli de business ------------------------------------------------------
COMISION = 0.10            # platforma reține 10% din fiecare lucrare finalizată
SPOR_URGENT = 0.15         # lucrările urgente costă cu 15% mai mult
SLOTURI = [8, 10, 12, 14, 16]   # ora de început a fiecărui interval de 2 ore
DURATA_SLOT = 2
ZILE_CALENDAR = 7          # câte zile în față se pot face programări
RAZA_SOSIRE_M = 200        # cât de aproape de adresă trebuie să fie meșterul
TOLERANTA_PUNCTUAL_MIN = 15
MAX_INVITATI = 6           # câți meșteri primesc o solicitare

# --- chei API (din fișierul .env) -------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
NOKIA_API_KEY = os.getenv("NOKIA_API_KEY", "").strip()
NOKIA_RAPIDAPI_HOST = os.getenv("NOKIA_RAPIDAPI_HOST", "").strip()
# În sandbox-ul Nokia merg doar numere de test (ex. +99999991000). Dacă e setat,
# toate apelurile către rețea folosesc acest număr în locul celui din cont.
NOKIA_NUMAR_TEST = os.getenv("NOKIA_NUMAR_TEST", "").strip()
GEOCODARE = os.getenv("GEOCODARE", "1").strip() == "1"
MOD_PREZENTARE = os.getenv("MOD_PREZENTARE", "1").strip() == "1"

# --- meserii -----------------------------------------------------------------
# pret = interval orientativ (lei), folosit când Gemini nu e disponibil
MESERII = {
    "instalator": {
        "scurt": "Instalator", "nume": "Instalator", "icon": "plumbing", "emoji": "🚿", "pret": (120, 300), "durata": 60,
        "cuvinte": ["apă", "apa", "țeav", "teav", "chiuvet", "robinet", "curge", "wc", "toalet",
                    "scurger", "sifon", "infundat", "înfundat", "baterie", "duș", "dus", "cadă", "cada", "inunda"],
        "materiale": ["racord flexibil", "garnituri", "bandă teflon"],
        "sfat": "Închide robinetul de sub chiuvetă sau robinetul general și pune un prosop.",
    },
    "electrician": {
        "scurt": "Electrician", "nume": "Electrician", "icon": "bolt", "emoji": "⚡", "pret": (100, 350), "durata": 60,
        "cuvinte": ["priz", "siguranț", "sigurant", "curent", "lumin", "bec", "tablou", "întrerup", "intrerup",
                    "scântei", "scantei", "cablu", "electric", "lustr"],
        "materiale": ["priză / întrerupător", "siguranță automată", "cablu"],
        "sfat": "Oprește siguranța circuitului respectiv din tablou și nu atinge priza.",
    },
    "termice": {
        "scurt": "Centrale", "nume": "Centrale și calorifere", "icon": "mode_heat", "emoji": "🔥", "pret": (150, 450), "durata": 90,
        "cuvinte": ["central", "calorifer", "căldur", "caldur", "încălzire", "incalzire", "boiler", "termostat", "presiune"],
        "materiale": ["robinet calorifer", "aerisitor", "vas de expansiune"],
        "sfat": "Verifică presiunea de pe manometru și nu demonta nimic la centrală.",
    },
    "tamplar": {
        "scurt": "Tâmplar", "nume": "Tâmplar", "icon": "carpenter", "emoji": "🪚", "pret": (100, 400), "durata": 90,
        "cuvinte": ["ușă", "usa", "usă", "fereastr", "geam", "dulap", "balama", "sertar", "mobil", "parchet", "raft", "pervaz"],
        "materiale": ["balamale", "șuruburi", "adeziv lemn"],
        "sfat": "Nu forța piesa blocată, ca să nu se rupă balamalele.",
    },
    "zugrav": {
        "scurt": "Zugrav", "nume": "Zugrav", "icon": "format_paint", "emoji": "🎨", "pret": (200, 900), "durata": 240,
        "cuvinte": ["zugrăv", "zugrav", "vopsea", "vopsit", "perete", "pereți", "tavan", "mucegai", "glet", "fisur", "tencuial", "igrasie"],
        "materiale": ["vopsea lavabilă", "glet", "amorsă"],
        "sfat": "Aerisește camera; dacă e mucegai, nu-l freca pe uscat.",
    },
    "lacatus": {
        "scurt": "Lăcătuș", "nume": "Lăcătuș", "icon": "key", "emoji": "🔑", "pret": (100, 350), "durata": 45,
        "cuvinte": ["yal", "ial", "încuietoare", "incuietoare", "cheie", "cheia", "blocat afar", "butuc", "lacăt", "lacat", "broasc"],
        "materiale": ["butuc yală", "broască"],
        "sfat": "Nu forța cheia în yală, se poate rupe înăuntru.",
    },
    "electrocasnice": {
        "scurt": "Aparate", "nume": "Reparații electrocasnice", "icon": "kitchen", "emoji": "🧺", "pret": (120, 400), "durata": 75,
        "cuvinte": ["mașină de spălat", "masina de spalat", "frigider", "cuptor", "aragaz", "hotă", "hota",
                    "mașina de vase", "masina de vase", "uscător", "uscator", "microunde", "congelator"],
        "materiale": ["furtun evacuare", "garnitură ușă", "pompă"],
        "sfat": "Scoate aparatul din priză și închide robinetul de apă al aparatului.",
    },
    "universal": {
        "scurt": "Diverse", "nume": "Meșter universal", "icon": "handyman", "emoji": "🛠️", "pret": (80, 300), "durata": 60,
        "cuvinte": ["montaj", "montat", "montez", "tablou", "poliț", "polit", "galerie", "televizor", "suport", "asambl"],
        "materiale": ["dibluri", "șuruburi"],
        "sfat": "Pregătește locul de lucru și eliberează accesul.",
    },
}

# --- cartiere din Timișoara (centru aproximativ) -----------------------------
ORAS = "Timișoara"
CENTRU_ORAS = (45.7537, 21.2257)
CARTIERE = {
    "Cetate (Centru)": (45.7576, 21.2290),
    "Fabric": (45.7605, 21.2520),
    "Iosefin": (45.7455, 21.2130),
    "Elisabetin": (45.7440, 21.2260),
    "Complexul Studențesc": (45.7475, 21.2400),
    "Circumvalațiunii": (45.7660, 21.2110),
    "Mehala": (45.7650, 21.1950),
    "Blașcovici": (45.7625, 21.2030),
    "Aradului": (45.7800, 21.2250),
    "Lipovei": (45.7760, 21.2420),
    "Torontalului": (45.7790, 21.2060),
    "Dâmbovița": (45.7400, 21.1950),
    "Calea Șagului": (45.7270, 21.2050),
    "Girocului": (45.7300, 21.2400),
    "Soarelui": (45.7290, 21.2500),
    "Freidorf": (45.7280, 21.1770),
    "Plopi": (45.7500, 21.2700),
    "Ghiroda Nouă": (45.7640, 21.2740),
}

MOTIVE_RAPORT_CLIENT = [
    "Meșterul nu a venit",
    "Lucrare de proastă calitate",
    "A cerut bani în afara aplicației",
    "Comportament nepotrivit",
    "Altceva",
]
MOTIVE_RAPORT_MESTER = [
    "Clientul nu a fost acasă",
    "Refuză să confirme lucrarea fără motiv",
    "Solicitare falsă sau poză înșelătoare",
    "Comportament nepotrivit",
    "Altceva",
]

CRITERII_RECENZIE = [
    ("calitate", "Calitatea lucrării"),
    ("punctualitate", "Punctualitate"),
    ("comunicare", "Comunicare"),
    ("pret", "Respectarea prețului"),
    ("profesionalism", "Profesionalism"),
]
