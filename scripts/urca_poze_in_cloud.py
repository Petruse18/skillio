"""Urcă în cloud (Vultr Object Storage / S3) pozele care sunt încă salvate local.

    python -m scripts.urca_poze_in_cloud

Ai nevoie de S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY în .env.
Pozele locale nu se șterg; doar referințele din baza de date trec pe cloud.
"""
import sys
from pathlib import Path

from core import db
from services import stocare

COLOANE = [("utilizatori", "poza"), ("utilizatori", "act_poza"), ("portofoliu", "poza"), ("lucrari", "poza"),
           ("lucrari", "poza_dupa"), ("mesaje", "poza")]


def main():
    if not stocare.activ():
        sys.exit("Lipsesc cheile S3 în .env (S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY).")
    urcate = 0
    for tabel, col in COLOANE:
        for r in db.q(f"SELECT id, {col} AS ref FROM {tabel} WHERE {col} IS NOT NULL AND {col} != ''"):
            ref = r["ref"]
            if ref.startswith("s3:"):
                continue
            date = stocare.citeste(ref)
            if not date:
                print(f"  lipsește fișierul: {ref}")
                continue
            nou = stocare.salveaza(date, Path(ref.split(":", 1)[-1].replace("\\", "/")).name)
            if nou.startswith("s3:"):
                db.ex(f"UPDATE {tabel} SET {col} = ? WHERE id = ?", (nou, r["id"]))
                urcate += 1
    print(f"Gata: {urcate} poze urcate în cloud.")


if __name__ == "__main__":
    main()
