"""Mută datele din SQLite (data/skillio.db) în PostgreSQL (de ex. Tiger Data).

Pași:
    1. Pune DATABASE_URL=postgresql://... în .env
    2. Din folderul proiectului:  python -m scripts.migreaza_in_postgres
       (cu --forta golește întâi tabelele din PostgreSQL, dacă au deja date)

Fișierul SQLite nu se modifică, rămâne ca o copie de siguranță.
"""
import os
import sqlite3
import sys

os.environ["DATE_DEMO"] = "0"          # nu punem date demo peste datele mutate

from core import config, db  # noqa: E402


def main():
    if not db.PG:
        sys.exit("Lipsește DATABASE_URL în .env. Pune adresa bazei PostgreSQL și încearcă din nou.")
    sursa = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else config.DB_PATH
    if not os.path.exists(sursa):
        sys.exit(f"Nu găsesc baza SQLite: {sursa}")
    forta = "--forta" in sys.argv

    db.init()                                      # creează tabelele în PostgreSQL
    if db.val("SELECT COUNT(*) FROM utilizatori", implicit=0) and not forta:
        sys.exit("PostgreSQL are deja utilizatori. Rulează cu --forta ca să-i înlocuiești.")

    src = sqlite3.connect(sursa)
    src.row_factory = sqlite3.Row
    with db.conn() as c:
        for t in db.TABELE:
            c.execute(f"DELETE FROM {t}")
        for t in db.TABELE:
            randuri = src.execute(f"SELECT * FROM {t}").fetchall()
            if not randuri:
                continue
            coloane = randuri[0].keys()
            sql = f"INSERT INTO {t}({', '.join(coloane)}) VALUES({', '.join('?' * len(coloane))})"
            for r in randuri:
                c.execute(sql, tuple(r))
            if t in db._CU_ID:                     # contorul de id-uri continuă după cel mai mare id
                c.raw.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                              f"COALESCE((SELECT MAX(id) FROM {t}), 1))")
            print(f"  {t}: {len(randuri)} rânduri")
    print("Gata. Datele sunt acum în PostgreSQL.")


if __name__ == "__main__":
    main()
