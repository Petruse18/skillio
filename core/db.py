"""Baza de date (SQLite) și câteva funcții scurte pentru interogări.

    q(sql, params)   -> listă de dicționare
    q1(sql, params)  -> un dicționar sau None
    val(sql, params) -> o singură valoare
    ex(sql, params)  -> execută o modificare și întoarce id-ul rândului nou

Fiecare modificare crește un contor („versiune”). Aplicația se uită la el din
2 în 2 secunde și se reîmprospătează singură când se schimbă ceva, așa că
telefonul clientului și cel al meșterului rămân sincronizate.
"""
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS utilizatori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefon TEXT UNIQUE,
    nume TEXT,
    rol TEXT,                        -- client | mester | admin
    creat_la TEXT,
    poza TEXT,                       -- poza de profil (cale fișier)
    numar_verificat INTEGER DEFAULT 0,   -- Nokia Number Verification
    sim_ok INTEGER DEFAULT 1,            -- Nokia SIM Swap: 1 = SIM neschimbat recent
    sim_verificat_la TEXT,
    adresa TEXT DEFAULT '',
    cartier TEXT,
    lat REAL,
    lon REAL,
    ghid_vazut INTEGER DEFAULT 0,
    -- doar pentru meșteri
    despre TEXT DEFAULT '',
    meserii TEXT DEFAULT '',         -- chei separate prin virgulă
    experienta_ani INTEGER DEFAULT 0,
    tarif_ora INTEGER DEFAULT 0,     -- preț orientativ, lei/oră
    raza_km REAL DEFAULT 8,
    disponibil INTEGER DEFAULT 1,
    act_status TEXT DEFAULT 'lipsa', -- lipsa | in_asteptare | verificat
    act_poza TEXT,
    departe_demo INTEGER DEFAULT 0   -- doar pentru prezentare: simulează că nu e la adresă
);
CREATE TABLE IF NOT EXISTS sesiuni (
    token TEXT PRIMARY KEY, user_id INTEGER, creat_la TEXT
);
CREATE TABLE IF NOT EXISTS portofoliu (
    id INTEGER PRIMARY KEY AUTOINCREMENT, mester_id INTEGER, poza TEXT, descriere TEXT, creat_la TEXT
);
CREATE TABLE IF NOT EXISTS lucrari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    titlu TEXT,
    descriere TEXT,
    adresa TEXT,
    cartier TEXT,
    lat REAL,
    lon REAL,
    poza TEXT,
    urgent INTEGER DEFAULT 0,
    buget INTEGER,
    meserie TEXT,
    diagnostic TEXT,                 -- JSON de la asistentul AI
    status TEXT,                     -- deschisa | acceptata | programata | sosit | gata | finalizata | disputa | anulata
    creat_la TEXT,
    mester_id INTEGER,
    oferta_id INTEGER,
    prog_propus TEXT,                -- ora propusă și încă neconfirmată de cealaltă parte
    prog_propus_de TEXT,             -- client | mester
    programat_la TEXT,               -- ora stabilită de ambele părți
    sosit_la TEXT,
    punctual INTEGER,
    sosire_mod TEXT,                 -- live | simulat
    gata_la TEXT,
    nota_mester TEXT,
    poza_dupa TEXT,
    confirmat_la TEXT,
    anulat_motiv TEXT
);
CREATE TABLE IF NOT EXISTS invitatii (
    lucrare_id INTEGER, mester_id INTEGER, loc INTEGER, status TEXT DEFAULT 'noua',  -- noua | refuzata
    PRIMARY KEY (lucrare_id, mester_id)
);
CREATE TABLE IF NOT EXISTS oferte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lucrare_id INTEGER, mester_id INTEGER,
    pret REAL,                       -- prețul cerut de meșter
    total REAL,                      -- ce plătește clientul (cu sporul de urgență)
    propus_la TEXT, mesaj TEXT,
    status TEXT,                     -- trimisa | acceptata | respinsa | retrasa
    creat_la TEXT
);
CREATE TABLE IF NOT EXISTS plati (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lucrare_id INTEGER, client_id INTEGER, mester_id INTEGER,
    suma REAL, comision REAL,
    tip TEXT,                        -- oferta | extra
    status TEXT,                     -- blocat | eliberat | returnat
    creat_la TEXT, rezolvat_la TEXT
);
CREATE TABLE IF NOT EXISTS extra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lucrare_id INTEGER, suma REAL, motiv TEXT,
    status TEXT,                     -- trimisa | acceptata | respinsa
    creat_la TEXT
);
CREATE TABLE IF NOT EXISTS mesaje (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lucrare_id INTEGER, autor_id INTEGER,   -- autor_id NULL = mesaj de sistem
    text TEXT, poza TEXT, creat_la TEXT
);
CREATE TABLE IF NOT EXISTS citit (
    lucrare_id INTEGER, user_id INTEGER, ultimul_id INTEGER DEFAULT 0,
    PRIMARY KEY (lucrare_id, user_id)
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lucrare_id INTEGER, mester_id INTEGER, client_id INTEGER,
    etapa TEXT,                      -- final | zi1 | sapt1 | luna1
    scadent_la TEXT, raspuns_la TEXT,
    nota REAL,                       -- media criteriilor (doar la etapa „final”)
    criterii TEXT,                   -- JSON cu nota pe fiecare criteriu
    ok INTEGER,                      -- 1/0 la etapele zi1, sapt1, luna1
    comentariu TEXT
);
CREATE TABLE IF NOT EXISTS rapoarte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lucrare_id INTEGER, autor_id INTEGER, vizat_id INTEGER,
    motiv TEXT, detalii TEXT, disputa INTEGER DEFAULT 0,
    status TEXT,                     -- deschis | confirmat | respins
    creat_la TEXT, rezolvat_la TEXT, rezolutie TEXT
);
CREATE TABLE IF NOT EXISTS blocari (
    mester_id INTEGER, zi TEXT, ora INTEGER, PRIMARY KEY (mester_id, zi, ora)
);
CREATE TABLE IF NOT EXISTS notificari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, text TEXT, lucrare_id INTEGER, citit INTEGER DEFAULT 0, creat_la TEXT
);
CREATE TABLE IF NOT EXISTS setari (cheie TEXT PRIMARY KEY, valoare TEXT);
CREATE INDEX IF NOT EXISTS i_lucrari_client ON lucrari(client_id);
CREATE INDEX IF NOT EXISTS i_lucrari_mester ON lucrari(mester_id);
CREATE INDEX IF NOT EXISTS i_feedback_mester ON feedback(mester_id);
CREATE INDEX IF NOT EXISTS i_mesaje_lucrare ON mesaje(lucrare_id);
"""


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def q(sql, p=()):
    with conn() as c:
        return [dict(r) for r in c.execute(sql, p).fetchall()]


def q1(sql, p=()):
    r = q(sql, p)
    return r[0] if r else None


def val(sql, p=(), implicit=None):
    with conn() as c:
        r = c.execute(sql, p).fetchone()
    return r[0] if r and r[0] is not None else implicit


def ex(sql, p=()):
    with conn() as c:
        cur = c.execute(sql, p)
        c.execute("UPDATE setari SET valoare = CAST(valoare AS INTEGER) + 1 WHERE cheie = 'versiune'")
        return cur.lastrowid


def versiune():
    return int(val("SELECT valoare FROM setari WHERE cheie = 'versiune'", implicit=0))


def setare(cheie, implicit=None):
    return val("SELECT valoare FROM setari WHERE cheie = ?", (cheie,), implicit)


def pune_setare(cheie, valoare):
    ex("INSERT INTO setari(cheie, valoare) VALUES(?, ?) "
       "ON CONFLICT(cheie) DO UPDATE SET valoare = excluded.valoare", (cheie, str(valoare)))


def init():
    """Creează fișierele și tabelele. La prima pornire pune și datele demo."""
    config.UPLOADS.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript(SCHEMA)
        c.execute("INSERT OR IGNORE INTO setari(cheie, valoare) VALUES('versiune', '0')")
        c.execute("INSERT OR IGNORE INTO setari(cheie, valoare) VALUES('decalaj_zile', '0')")
    if val("SELECT COUNT(*) FROM utilizatori", implicit=0) == 0:
        from . import seed
        seed.populeaza()


def reseteaza():
    """Șterge tot și pune la loc datele demo (buton în panoul de admin)."""
    with conn() as c:
        for t in ("utilizatori", "sesiuni", "portofoliu", "lucrari", "invitatii", "oferte", "plati", "extra",
                  "mesaje", "citit", "feedback", "rapoarte", "blocari", "notificari"):
            c.execute(f"DELETE FROM {t}")
        c.execute("UPDATE setari SET valoare = '0' WHERE cheie = 'decalaj_zile'")
    from . import seed
    seed.populeaza()
    ex("UPDATE setari SET valoare = valoare WHERE cheie = 'decalaj_zile'")
