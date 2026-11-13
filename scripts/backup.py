"""Backup și restaurare, pentru orice bază (SQLite sau PostgreSQL).

    python -m scripts.backup                         -> salvează backups/skillio-AAAALLZZ-OOMM.json
    python -m scripts.backup --restaureaza FISIER    -> pune la loc datele din fișier (șterge ce e acum!)

Tiger Data face și backup automat zilnic; ăsta e un backup în plus, pe care îl ții tu.
Pe server, rulează-l zilnic din cron (vezi DEPLOY.md).
"""
import json
import sys
from datetime import datetime

from core import config, db

DIR = config.ROOT / "backups"


def salveaza():
    DIR.mkdir(exist_ok=True)
    date = {t: db.q(f"SELECT * FROM {t}") for t in db.TABELE}
    f = DIR / f"skillio-{datetime.now():%Y%m%d-%H%M}.json"
    f.write_text(json.dumps(date, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Backup salvat: {f} ({sum(len(v) for v in date.values())} rânduri)")
    return f


def restaureaza(cale):
    date = json.loads(open(cale, encoding="utf-8").read())
    db.init()
    with db.conn() as c:
        for t in db.TABELE:
            c.execute(f"DELETE FROM {t}")
        for t in db.TABELE:
            for r in date.get(t, []):
                col = list(r)
                c.execute(f"INSERT INTO {t}({', '.join(col)}) VALUES({', '.join('?' * len(col))})",
                          tuple(r.values()))
            if db.PG and t in db._CU_ID:
                c.raw.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                              f"COALESCE((SELECT MAX(id) FROM {t}), 1))")
    db.ex("UPDATE setari SET valoare = valoare WHERE cheie = 'versiune'")
    print(f"Restaurat din {cale}.")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--restaureaza":
        restaureaza(sys.argv[2])
    else:
        salveaza()
