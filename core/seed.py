"""Date demo: meșteri cu istoric real (lucrări, recenzii, feedback), clienți și câteva solicitări deschise.

Totul e generat determinist (aceleași date la fiecare resetare), ca prezentarea
să arate la fel de fiecare dată. Conturile de prezentare:

    Client:  Ana Popescu      0722 000 001
    Meșter:  Ionel Mureșan    0722 000 101
    Admin:   Echipa SKILLIO   0700 000 000
"""
import json
import io
import random
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont

from services import stocare

from . import config, db, timp

R = random.Random(2026)

CLIENTI = [
    ("+40722000001", "Ana Popescu", "Elisabetin", "Str. Gheorghe Lazăr 14, ap. 3"),
    ("+40722000002", "Mihai Ionescu", "Fabric", "Str. Ștefan cel Mare 22"),
    ("+40722000003", "Elena Dragomir", "Cetate (Centru)", "Str. Mercy 5"),
    ("+40722000004", "Andrei Pop", "Complexul Studențesc", "Aleea Studenților 8"),
    ("+40722000005", "Ioana Stan", "Iosefin", "Bd. 16 Decembrie 1989 41"),
    ("+40722000006", "Radu Georgescu", "Lipovei", "Calea Lipovei 77"),
    ("+40722000007", "Cristina Matei", "Girocului", "Calea Girocului 120"),
    ("+40722000008", "Vlad Munteanu", "Circumvalațiunii", "Calea Circumvalațiunii 30"),
    ("+40722000009", "Bianca Lungu", "Dâmbovița", "Calea Șagului 15"),
    ("+40722000010", "Florin Radu", "Soarelui", "Str. Grigore Alexandrescu 102"),
]

# telefon, nume, cartier, meserii, ani, tarif, raza, calitate (0-1), seriozitate (0-1), nr lucrări, despre, sim_ok, act
MESTERI = [
    ("+40722000101", "Ionel Mureșan", "Fabric", "instalator,termice", 12, 90, 9, .93, .96, 34,
     "Instalator autorizat, 12 ani experiență. Țevi, obiecte sanitare, centrale și calorifere. Lucrez curat și "
     "vă spun prețul înainte.", 1, "verificat"),
    ("+40722000102", "Mihai Dobre", "Iosefin", "instalator", 6, 70, 7, .80, .82, 18,
     "Reparații rapide la instalații sanitare, desfundări, montaj obiecte sanitare.", 0, "in_asteptare"),
    ("+40722000103", "Andrei Rusu", "Girocului", "instalator,universal", 9, 80, 10, .88, .90, 26,
     "Instalații sanitare și montaje în casă. Disponibil și seara.", 1, "verificat"),
    ("+40722000104", "Sorin Lazăr", "Cetate (Centru)", "electrician", 15, 100, 8, .95, .97, 45,
     "Electrician autorizat ANRE, gradul II. Tablouri electrice, prize, iluminat, verificări.", 1, "verificat"),
    ("+40722000105", "Cătălin Ene", "Lipovei", "electrician,universal", 4, 75, 9, .78, .85, 11,
     "Mici lucrări electrice: prize, întrerupătoare, lustre, montaj aparatură.", 1, "lipsa"),
    ("+40722000106", "Gabriel Toma", "Complexul Studențesc", "termice,instalator", 11, 95, 10, .90, .88, 29,
     "Service centrale termice (Ariston, Vaillant, Bosch), calorifere, încălzire în pardoseală.", 1, "verificat"),
    ("+40722000107", "Dan Pavel", "Circumvalațiunii", "tamplar", 20, 85, 12, .92, .93, 38,
     "Tâmplărie lemn și PVC, reglaj uși și ferestre, mobilier la comandă.", 1, "verificat"),
    ("+40722000108", "Florin Neagu", "Mehala", "tamplar,universal", 7, 65, 8, .83, .80, 15,
     "Reparații mobilă, montaj și asamblare, balamale, sertare.", 1, "lipsa"),
    ("+40722000109", "Marius Ciobanu", "Dâmbovița", "zugrav", 10, 60, 10, .86, .84, 22,
     "Zugrăveli interioare, glet, lavabil, reparații fisuri și tratament mucegai.", 1, "verificat"),
    ("+40722000110", "Laurențiu Olaru", "Freidorf", "zugrav", 3, 55, 9, .74, .76, 7,
     "Zugrav, lucrări mici și mari, prețuri corecte.", 1, "lipsa"),
    ("+40722000111", "Petru Matei", "Elisabetin", "lacatus,universal", 8, 80, 8, .89, .94, 24,
     "Deblocări uși, schimb yale și butuci, montaj încuietori de siguranță. Vin rapid.", 1, "verificat"),
    ("+40722000112", "Răzvan Iliescu", "Torontalului", "electrocasnice", 13, 90, 11, .91, .89, 31,
     "Reparații mașini de spălat, frigidere, cuptoare, mașini de vase. Piese originale.", 1, "verificat"),
    ("+40722000113", "Bogdan Stoica", "Aradului", "electrocasnice,electrician", 5, 70, 9, .79, .78, 12,
     "Electrocasnice mari și mici, plus instalații electrice simple.", 1, "lipsa"),
    ("+40722000114", "Ciprian Avram", "Plopi", "universal,tamplar", 2, 50, 10, .70, .72, 4,
     "Meșter la toate: montaje, rafturi, mici reparații în casă.", 1, "lipsa"),
]

COMENTARII_BUNE = [
    "Rapid și curat, a adus exact piesa care trebuia.",
    "A venit la ora stabilită și a explicat tot ce a făcut.",
    "Foarte serios, prețul a fost exact cel din ofertă.",
    "Recomand! A rezolvat problema din prima.",
    "Profesionist, a lăsat totul curat după el.",
    "Comunicare excelentă, m-a ținut la curent pe chat.",
    "Lucrare făcută cu grijă, se vede experiența.",
    "A venit chiar în aceeași zi, salvare!",
]
COMENTARII_MEDII = [
    "A întârziat puțin, dar lucrarea e bună.",
    "Lucrarea e ok, comunicarea putea fi mai bună.",
    "A rezolvat, dar a durat mai mult decât spusese.",
]
TITLURI = {
    "instalator": ["Robinet care picură", "Scurgere la sifon", "Montaj baterie bucătărie", "WC care curge continuu",
                   "Țeavă fisurată în baie", "Desfundare chiuvetă"],
    "electrician": ["Priză care nu merge", "Sare siguranța", "Montaj lustră", "Înlocuire întrerupătoare",
                    "Tablou electric vechi"],
    "termice": ["Centrala nu pornește", "Calorifer rece", "Revizie centrală", "Presiune scăzută la centrală"],
    "tamplar": ["Ușă care nu se închide", "Reglaj ferestre PVC", "Balama ruptă la dulap", "Sertar blocat"],
    "zugrav": ["Zugrăvit dormitor", "Pată de mucegai pe tavan", "Fisuri în perete", "Zugrăvit hol"],
    "lacatus": ["Schimb butuc yală", "Ușă blocată", "Montaj încuietoare suplimentară"],
    "electrocasnice": ["Mașina de spălat nu evacuează", "Frigiderul nu răcește", "Cuptor care nu încălzește"],
    "universal": ["Montaj televizor pe perete", "Montaj rafturi", "Asamblare dulap"],
}
CULORI = {"instalator": (41, 120, 181), "electrician": (214, 158, 46), "termice": (201, 88, 52),
          "tamplar": (140, 98, 57), "zugrav": (122, 104, 181), "lacatus": (90, 110, 120),
          "electrocasnice": (60, 150, 140), "universal": (18, 122, 78)}


def _poza_lucrare(meserie, eticheta, nume_fisier):
    """Generează o ilustrație simplă (fără internet) pentru portofoliu."""
    w, h = 480, 360
    base = CULORI.get(meserie, (18, 122, 78))
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    for y in range(h):
        f = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(c * (0.65 + 0.45 * f)) if c * (0.65 + 0.45 * f) < 255 else 255
                                            for c in base))
    rr = random.Random(nume_fisier)
    for _ in range(6):
        x, y, s = rr.randint(0, w), rr.randint(0, h), rr.randint(40, 140)
        d.ellipse([x - s, y - s, x + s, y + s], fill=tuple(min(255, c + 30) for c in base))
    d.rounded_rectangle([24, h - 84, w - 24, h - 24], radius=14, fill=(255, 255, 255))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    d.text((40, h - 68), eticheta[:30], fill=(15, 42, 32), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG" if nume_fisier.endswith(".png") else "JPEG", quality=82)
    return stocare.salveaza(buf.getvalue(), nume_fisier)


def _poza_problema(meserie, nume_fisier):
    return _poza_lucrare(meserie, "Poză trimisă de client", nume_fisier)


def _ins(sql, p):
    with db.conn() as c:
        return c.execute(sql, p).lastrowid


def populeaza():
    acum = timp.acum()
    config.UPLOADS.mkdir(parents=True, exist_ok=True)

    def coord(cartier):
        lat, lon = config.CARTIERE[cartier]
        return lat + R.uniform(-.004, .004), lon + R.uniform(-.006, .006)

    # --- admin + clienți ----------------------------------------------------
    _ins("INSERT INTO utilizatori(telefon, nume, rol, creat_la, numar_verificat, cartier, lat, lon, ghid_vazut) "
         "VALUES(?,?,?,?,?,?,?,?,1)", ("+40700000000", "Echipa SKILLIO", "admin", timp.iso(acum - timedelta(days=400)),
                                       1, "Cetate (Centru)", *config.CARTIERE["Cetate (Centru)"]))
    clienti = []
    for tel, nume, cart, adr in CLIENTI:
        lat, lon = coord(cart)
        if tel == "+40722000001":
            lat, lon = 45.7447, 21.2248
        cid = _ins("INSERT INTO utilizatori(telefon, nume, rol, creat_la, numar_verificat, sim_ok, adresa, cartier, "
                   "lat, lon, ghid_vazut) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                   (tel, nume, "client", timp.iso(acum - timedelta(days=R.randint(60, 300))), 1, 1, adr, cart,
                    lat, lon, 0 if tel == "+40722000001" else 1))
        clienti.append(cid)
    ana = clienti[0]

    # --- meșteri cu istoric ---------------------------------------------------
    mesteri = {}
    for (tel, nume, cart, mes, ani, tarif, raza, calit, serioz, n, despre, sim_ok, act) in MESTERI:
        lat, lon = coord(cart)
        mid = _ins("INSERT INTO utilizatori(telefon, nume, rol, creat_la, numar_verificat, sim_ok, sim_verificat_la, "
                   "cartier, lat, lon, despre, meserii, experienta_ani, tarif_ora, raza_km, disponibil, act_status, "
                   "ghid_vazut, adresa) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (tel, nume, "mester", timp.iso(acum - timedelta(days=R.randint(220, 420))), 1, sim_ok,
                    timp.iso(acum - timedelta(hours=3)), cart, lat, lon, despre, mes, ani, tarif, raza,
                    0 if tel == "+40722000110" else 1, act, 0 if tel == "+40722000101" else 1, ""))
        mesteri[tel] = mid
        ms = mes.split(",")
        for k in range(3 if n > 10 else 2):
            meserie = ms[k % len(ms)]
            titlu = R.choice(TITLURI[meserie])
            cale = _poza_lucrare(meserie, titlu, f"port_{mid}_{k}.jpg")
            _ins("INSERT INTO portofoliu(mester_id, poza, descriere, creat_la) VALUES(?,?,?,?)",
                 (mid, cale, titlu, timp.iso(acum - timedelta(days=R.randint(5, 200)))))
        _istoric(mid, ms, n, calit, serioz, clienti[1:], acum)

    # Ana: o lucrare terminată acum 2 zile cu Sorin (electrician): recenzia e dată,
    # întrebarea „după o zi” așteaptă răspuns -> apare pe ecranul ei de start.
    sorin = mesteri["+40722000104"]
    _lucrare_finalizata(ana, sorin, "electrician", "Priză care nu merge în sufragerie", acum - timedelta(days=2),
                        nota=5, punctual=1, raspunde_durab=False, comentariu="Rapid și curat, a explicat tot.")

    # --- solicitări deschise, ca meșterul demo să aibă ce vedea ---------------
    mihai_c, elena, andrei_c, ioana = clienti[1], clienti[2], clienti[3], clienti[4]
    _solicitare(mihai_c, "termice", "Centrala nu pornește, nu avem căldură",
                "De azi-dimineață centrala afișează eroare și nu mai pornește. Avem un copil mic, e frig.",
                "Str. Ștefan cel Mare 22", "Fabric", urgent=1, buget=400, cu_poza=True, acum=acum - timedelta(minutes=25),
                oferte=[(mesteri["+40722000106"], 260)])
    _solicitare(elena, "instalator", "Robinet care picură în bucătărie",
                "Bateria de la chiuveta din bucătărie picură continuu, chiar și închisă.", "Str. Mercy 5",
                "Cetate (Centru)", urgent=0, buget=200, cu_poza=True, acum=acum - timedelta(hours=3),
                oferte=[(mesteri["+40722000102"], 130), (mesteri["+40722000103"], 150)])
    _solicitare(andrei_c, "instalator", "Montaj mașină de spălat vase",
                "Am cumpărat o mașină de spălat vase și trebuie racordată la apă și scurgere.",
                "Aleea Studenților 8", "Complexul Studențesc", urgent=0, buget=250, cu_poza=False,
                acum=acum - timedelta(hours=7), oferte=[])
    _solicitare(ioana, "electrician", "Lustra nu se aprinde",
                "Am schimbat becul, dar lustra din dormitor tot nu se aprinde.", "Bd. 16 Decembrie 1989 41",
                "Iosefin", urgent=0, buget=None, cu_poza=False, acum=acum - timedelta(hours=1),
                oferte=[(mesteri["+40722000105"], 90)])

    # o programare deja făcută pentru Ionel, să nu aibă calendarul gol
    ionel = mesteri["+40722000101"]
    radu = clienti[5]
    zi = (acum + timedelta(days=1)).replace(hour=10, minute=0, second=0)
    lid = _ins("INSERT INTO lucrari(client_id, titlu, descriere, adresa, cartier, lat, lon, urgent, meserie, diagnostic, "
               "status, creat_la, mester_id, programat_la) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (radu, "Calorifer rece în dormitor", "Un calorifer din dormitor rămâne rece, celelalte merg.",
                "Calea Lipovei 77", "Lipovei", *coord("Lipovei"), 0, "termice",
                json.dumps(_diag("termice", "Calorifer rece în dormitor"), ensure_ascii=False), "programata",
                timp.iso(acum - timedelta(days=1)), ionel, timp.iso(zi)))
    oid = _ins("INSERT INTO oferte(lucrare_id, mester_id, pret, total, propus_la, mesaj, status, creat_la) "
               "VALUES(?,?,?,?,?,?,?,?)", (lid, ionel, 180, 180, timp.iso(zi), "Aerisesc și verific robinetul.",
                                           "acceptata", timp.iso(acum - timedelta(days=1))))
    _ins("UPDATE lucrari SET oferta_id = ? WHERE id = ?", (oid, lid))
    _ins("INSERT INTO plati(lucrare_id, client_id, mester_id, suma, comision, tip, status, creat_la) "
         "VALUES(?,?,?,?,?,?,?,?)", (lid, radu, ionel, 180, 0, "oferta", "blocat", timp.iso(acum - timedelta(hours=20))))
    for autor, text in [(None, "Ora e stabilită. Clientul a plătit 180 lei, blocați până la final."),
                        (radu, "Bună ziua! Interfonul e la apartamentul 12."),
                        (ionel, "Mulțumesc, ajung la 10. Vă rog să nu porniți centrala pe maxim până atunci.")]:
        _ins("INSERT INTO mesaje(lucrare_id, autor_id, text, creat_la) VALUES(?,?,?,?)",
             (lid, autor, text, timp.iso(acum - timedelta(hours=19))))

    # o reclamație deschisă pentru panoul de admin
    _ins("INSERT INTO rapoarte(lucrare_id, autor_id, vizat_id, motiv, detalii, disputa, status, creat_la) "
         "VALUES(?,?,?,?,?,?,?,?)", (None, clienti[6], mesteri["+40722000114"], "A cerut bani în afara aplicației",
                                     "Mi-a cerut să-i dau banii cash, ca să nu plătească comisionul.", 0, "deschis",
                                     timp.iso(acum - timedelta(hours=5))))
    db.ex("UPDATE setari SET valoare = valoare WHERE cheie = 'versiune'")


def _diag(meserie, titlu):
    m = config.MESERII[meserie]
    return {"meserie": meserie, "titlu": titlu, "urgenta": "saptamana", "descriere": titlu,
            "pret_min": m["pret"][0], "pret_max": m["pret"][1], "durata_min": m["durata"],
            "materiale": m["materiale"], "intrebari": [], "sfat_siguranta": m["sfat"], "incredere": .8,
            "sursa": "reguli"}


def _lucrare_finalizata(client, mester, meserie, titlu, cand, nota, punctual, raspunde_durab=True,
                        comentariu="", ok_durab=True, acum=None):
    acum = acum or timp.acum()
    cl = db.q1("SELECT * FROM utilizatori WHERE id = ?", (client,))
    pret = R.randrange(*config.MESERII[meserie]["pret"], 10)
    prog = cand.replace(minute=0, second=0, microsecond=0)
    sosit = prog + timedelta(minutes=R.randint(-10, 8) if punctual else R.randint(25, 60))
    gata = sosit + timedelta(minutes=config.MESERII[meserie]["durata"])
    lid = _ins("INSERT INTO lucrari(client_id, titlu, descriere, adresa, cartier, lat, lon, urgent, meserie, "
               "diagnostic, status, creat_la, mester_id, programat_la, sosit_la, sosire_mod, punctual, gata_la, "
               "confirmat_la) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (client, titlu, titlu + ".", cl["adresa"], cl["cartier"], cl["lat"], cl["lon"], 0, meserie,
                json.dumps(_diag(meserie, titlu), ensure_ascii=False), "finalizata",
                timp.iso(prog - timedelta(days=1)), mester, timp.iso(prog), timp.iso(sosit), "simulat", punctual,
                timp.iso(gata), timp.iso(gata + timedelta(minutes=20))))
    oid = _ins("INSERT INTO oferte(lucrare_id, mester_id, pret, total, propus_la, status, creat_la) "
               "VALUES(?,?,?,?,?,?,?)", (lid, mester, pret, pret, timp.iso(prog), "acceptata",
                                         timp.iso(prog - timedelta(days=1))))
    _ins("UPDATE lucrari SET oferta_id = ? WHERE id = ?", (oid, lid))
    _ins("INSERT INTO plati(lucrare_id, client_id, mester_id, suma, comision, tip, status, creat_la, rezolvat_la) "
         "VALUES(?,?,?,?,?,?,?,?,?)", (lid, client, mester, pret, round(pret * config.COMISION, 2), "oferta",
                                       "eliberat", timp.iso(prog - timedelta(hours=20)),
                                       timp.iso(gata + timedelta(minutes=20))))
    conf = gata + timedelta(minutes=20)
    crit = {k: max(1, min(5, round(nota + R.uniform(-.6, .4)))) for k, _ in config.CRITERII_RECENZIE}
    if not punctual:
        crit["punctualitate"] = max(1, crit["punctualitate"] - 2)
    medie = sum(crit.values()) / len(crit)
    _ins("INSERT INTO feedback(lucrare_id, mester_id, client_id, etapa, scadent_la, raspuns_la, nota, criterii, "
         "comentariu) VALUES(?,?,?,?,?,?,?,?,?)", (lid, mester, client, "final", timp.iso(conf),
                                                   timp.iso(conf + timedelta(hours=2)), medie, json.dumps(crit),
                                                   comentariu))
    for etapa, zile in (("zi1", 1), ("sapt1", 7), ("luna1", 30)):
        scad = conf + timedelta(days=zile)
        if scad <= acum and raspunde_durab:
            ok = 1 if ok_durab else 0
            _ins("INSERT INTO feedback(lucrare_id, mester_id, client_id, etapa, scadent_la, raspuns_la, ok) "
                 "VALUES(?,?,?,?,?,?,?)", (lid, mester, client, etapa, timp.iso(scad),
                                           timp.iso(scad + timedelta(hours=3)), ok))
        else:
            _ins("INSERT INTO feedback(lucrare_id, mester_id, client_id, etapa, scadent_la) VALUES(?,?,?,?,?)",
                 (lid, mester, client, etapa, timp.iso(scad)))
    return lid


def _istoric(mid, meserii, n, calit, serioz, clienti, acum):
    for i in range(n):
        meserie = R.choice(meserii)
        cand = acum - timedelta(days=R.randint(4, 240), hours=R.randint(0, 6))
        cand = cand.replace(hour=R.choice(config.SLOTURI))
        if R.random() > serioz + 0.06:  # programare nerespectată
            cl = R.choice(clienti)
            c = db.q1("SELECT * FROM utilizatori WHERE id = ?", (cl,))
            _ins("INSERT INTO lucrari(client_id, titlu, descriere, adresa, cartier, lat, lon, meserie, status, "
                 "creat_la, mester_id, programat_la, anulat_motiv) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (cl, R.choice(TITLURI[meserie]), "", c["adresa"], c["cartier"], c["lat"], c["lon"], meserie,
                  "anulata", timp.iso(cand - timedelta(days=1)), mid, timp.iso(cand), "Meșterul nu a venit"))
            continue
        punctual = 1 if R.random() < serioz else 0
        bun = R.random() < calit
        nota = R.choice([5, 5, 5, 4]) if bun else R.choice([4, 3, 3])
        com = R.choice(COMENTARII_BUNE) if bun else R.choice(COMENTARII_MEDII)
        _lucrare_finalizata(R.choice(clienti), mid, meserie, R.choice(TITLURI[meserie]), cand, nota, punctual,
                            comentariu=com if R.random() < .75 else "", ok_durab=R.random() < (calit + .06),
                            acum=acum)
    if calit < .75:
        _ins("INSERT INTO rapoarte(lucrare_id, autor_id, vizat_id, motiv, detalii, disputa, status, creat_la, "
             "rezolvat_la, rezolutie) VALUES(?,?,?,?,?,?,?,?,?,?)",
             (None, R.choice(clienti), mid, "Lucrare de proastă calitate", "Lucrarea a trebuit refăcută.", 0,
              "confirmat", timp.iso(acum - timedelta(days=40)), timp.iso(acum - timedelta(days=38)),
              "Confirmat după verificarea pozelor."))


def _solicitare(client, meserie, titlu, descriere, adresa, cartier, urgent, buget, cu_poza, acum, oferte):
    lat, lon = config.CARTIERE[cartier]
    lat, lon = lat + R.uniform(-.002, .002), lon + R.uniform(-.003, .003)
    poza = _poza_problema(meserie, f"sol_{client}_{meserie}.jpg") if cu_poza else None
    d = _diag(meserie, titlu)
    d["urgenta"] = "urgent" if urgent else "saptamana"
    d["descriere"] = descriere
    lid = _ins("INSERT INTO lucrari(client_id, titlu, descriere, adresa, cartier, lat, lon, poza, urgent, buget, "
               "meserie, diagnostic, status, creat_la) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (client, titlu, descriere, adresa, cartier, lat, lon, poza, urgent, buget, meserie,
                json.dumps(d, ensure_ascii=False), "deschisa", timp.iso(acum)))
    for mid, pret in oferte:
        cand = (timp.acum() + timedelta(days=1)).replace(hour=R.choice([10, 12, 14]), minute=0, second=0)
        _ins("INSERT INTO oferte(lucrare_id, mester_id, pret, total, propus_la, mesaj, status, creat_la) "
             "VALUES(?,?,?,?,?,?,?,?)", (lid, mid, pret, round(pret * (1.15 if urgent else 1)), timp.iso(cand),
                                         "Pot veni mâine.", "trimisa", timp.iso(acum + timedelta(minutes=10))))
    _ins("INSERT INTO mesaje(lucrare_id, autor_id, text, creat_la) VALUES(?,?,?,?)",
         (lid, None, "Solicitarea a fost trimisă meșterilor potriviți.", timp.iso(acum)))
    return lid
