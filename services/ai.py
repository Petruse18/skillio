"""Asistentul AI: din descriere (și poză) scoate meseria, urgența, prețul și ce să aducă meșterul.

Cu GEMINI_API_KEY în .env folosește Gemini. Fără cheie (sau dacă pică internetul)
folosește o clasificare simplă după cuvinte-cheie, ca demo-ul să nu se blocheze.
Rezultatul are mereu aceeași formă (vezi `_rezervă`).
"""
import json
import logging
import re

from core import config

log = logging.getLogger("skillio.ai")

PROMPT = """Ești asistentul aplicației SKILLIO din Timișoara, care leagă clienți de meșteri.
Clientul descrie o problemă din casă (și uneori trimite o poză). Răspunde DOAR cu JSON valid, în română:
{{
  "meserie": una dintre {meserii},
  "titlu": "titlu scurt al lucrării, max 6 cuvinte",
  "urgenta": "urgent" | "azi" | "saptamana" | "flexibil",
  "descriere": "descrierea problemei, reformulată clar, 1-2 propoziții",
  "pret_min": număr (lei, manoperă + materiale uzuale, prețuri Timișoara 2026),
  "pret_max": număr,
  "durata_min": număr (minute),
  "materiale": ["ce ar trebui să aducă meșterul", "..."],
  "intrebari": ["max 2 întrebări scurte care l-ar ajuta pe meșter", "..."],
  "sfat_siguranta": "ce să facă clientul până vine meșterul, 1 propoziție",
  "incredere": număr între 0 și 1
}}
Nu pune diagnostic definitiv: evaluarea finală o face meșterul.

Descrierea clientului: {text}"""


def activ() -> bool:
    return bool(config.GEMINI_API_KEY)


def _rezerva(text: str) -> dict:
    t = (text or "").lower()
    scoruri = {k: sum(1 for c in m["cuvinte"] if c in t) for k, m in config.MESERII.items()}
    meserie = max(scoruri, key=scoruri.get)
    if scoruri[meserie] == 0:
        meserie = "universal"
    m = config.MESERII[meserie]
    if any(c in t for c in ["urgent", "inund", "scântei", "scantei", "fum", "miros de gaz", "nu am apă",
                            "nu am apa", "nu am curent", "baltă", "balta", "curge tare", "blocat afar"]):
        urgenta = "urgent"
    elif any(c in t for c in ["azi", "nu merge", "nu mai merge", "nu funcțion", "nu functioneaza", "curge", "stricat"]):
        urgenta = "azi"
    else:
        urgenta = "saptamana"
    prop = re.split(r"[.!?\n]", text.strip())[0] if text else ""
    cuv = prop.split()[:6]
    while cuv and cuv[-1].lower().strip(",;:") in ("în", "in", "de", "la", "pe", "cu", "și", "si", "din", "sub", "a", "e"):
        cuv.pop()
    titlu = " ".join(cuv).rstrip(",;:") or m["nume"]
    return {
        "meserie": meserie,
        "titlu": titlu[:1].upper() + titlu[1:],
        "urgenta": urgenta,
        "descriere": text.strip(),
        "pret_min": m["pret"][0],
        "pret_max": m["pret"][1],
        "durata_min": m["durata"],
        "materiale": m["materiale"],
        "intrebari": ["De când a apărut problema?", "Poți trimite o poză de aproape?"],
        "sfat_siguranta": m["sfat"],
        "incredere": 0.55 if scoruri[meserie] else 0.3,
        "sursa": "reguli",
    }


def _curata(d: dict, text: str) -> dict:
    baza = _rezerva(text)
    if d.get("meserie") not in config.MESERII:
        d["meserie"] = baza["meserie"]
    if d.get("urgenta") not in ("urgent", "azi", "saptamana", "flexibil"):
        d["urgenta"] = baza["urgenta"]
    for k in ("pret_min", "pret_max", "durata_min", "incredere"):
        try:
            d[k] = float(d.get(k)) if k == "incredere" else int(float(d.get(k)))
        except (TypeError, ValueError):
            d[k] = baza[k]
    if d["pret_max"] < d["pret_min"]:
        d["pret_min"], d["pret_max"] = d["pret_max"], d["pret_min"]
    for k in ("titlu", "descriere", "sfat_siguranta"):
        if not isinstance(d.get(k), str) or not d[k].strip():
            d[k] = baza[k]
    for k in ("materiale", "intrebari"):
        if not isinstance(d.get(k), list):
            d[k] = baza[k]
        d[k] = [str(x) for x in d[k]][:5]
    return d


def diagnosticheaza(text: str, poza: bytes | None = None, mime: str = "image/jpeg") -> dict:
    if activ():
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            parti = [PROMPT.format(meserii=list(config.MESERII), text=text or "(fără text, doar poză)")]
            if poza:
                parti.append(types.Part.from_bytes(data=poza, mime_type=mime))
            r = client.models.generate_content(
                model=config.GEMINI_MODEL, contents=parti,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2))
            d = json.loads(r.text)
            if isinstance(d, list):
                d = d[0]
            d = _curata(d, text)
            d["sursa"] = "gemini"
            return d
        except Exception as e:  # noqa: BLE001
            log.warning("Gemini a eșuat, folosesc regulile: %s", e)
    return _rezerva(text)
