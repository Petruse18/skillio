"""Notificări în afara aplicației: email (SMTP) și SMS (Twilio).

Se trimit doar la momentele importante: solicitare nouă, ofertă nouă, ofertă acceptată,
oră propusă / confirmată, plată, lucrare gata, bani încasați.

Configurare în .env (oricare, sau amândouă):
    Email:  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PAROLA, SMTP_FROM
            (Gmail: smtp.gmail.com, port 587, parolă de aplicație din contul Google)
    SMS:    TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM
Fără setări nu se trimite nimic și aplicația merge ca înainte (notificările rămân în clopoțel).
Trimiterea se face în fundal, ca să nu încetinească ecranul.
"""
import logging
import smtplib
import threading
from email.message import EmailMessage

import requests

from core import config

log = logging.getLogger("skillio.mesaje")
ULTIMELE: list[dict] = []        # ultimele încercări, afișate în panoul de admin


def email_activ() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PAROLA)


def sms_activ() -> bool:
    return bool(config.TWILIO_SID and config.TWILIO_TOKEN and config.TWILIO_FROM)


def _jurnal(canal, catre, ok, detaliu=""):
    ULTIMELE.insert(0, {"canal": canal, "catre": catre, "ok": ok, "detaliu": str(detaliu)[:200]})
    del ULTIMELE[30:]


def trimite_email(catre: str, subiect: str, text: str) -> bool:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = f"SKILLIO <{config.SMTP_FROM}>", catre, subiect
    msg.set_content(f"{text}\n\nDeschide aplicația: {config.URL_APP}\n\n— SKILLIO · {config.SLOGAN}")
    try:
        clasa = smtplib.SMTP_SSL if config.SMTP_PORT == 465 else smtplib.SMTP
        with clasa(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as s:
            s.ehlo()
            if clasa is smtplib.SMTP and s.has_extn("starttls"):
                s.starttls()
                s.ehlo()
            if s.has_extn("auth"):
                s.login(config.SMTP_USER, config.SMTP_PAROLA)
            s.send_message(msg)
        _jurnal("email", catre, True)
        return True
    except Exception as e:
        log.warning("Email eșuat către %s: %s", catre, e)
        _jurnal("email", catre, False, e)
        return False


def trimite_sms(catre: str, text: str) -> bool:
    try:
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_SID}/Messages.json",
                          data={"From": config.TWILIO_FROM, "To": catre, "Body": f"SKILLIO: {text}"[:600]},
                          auth=(config.TWILIO_SID, config.TWILIO_TOKEN), timeout=15)
        ok = r.status_code < 300
        _jurnal("sms", catre, ok, "" if ok else r.text)
        return ok
    except Exception as e:
        log.warning("SMS eșuat către %s: %s", catre, e)
        _jurnal("sms", catre, False, e)
        return False


def anunta(user: dict, text: str):
    """Trimite notificarea prin canalele configurate, în fundal."""
    if not user or not user.get("notif_extern", 1):
        return
    sarcini = []
    if email_activ() and user.get("email"):
        sarcini.append(lambda: trimite_email(user["email"], text[:80], text))
    if sms_activ() and user.get("telefon"):
        sarcini.append(lambda: trimite_sms(user["telefon"], text))
    for f in sarcini:
        threading.Thread(target=f, daemon=True).start()
