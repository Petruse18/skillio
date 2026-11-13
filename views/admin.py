"""Panoul echipei SKILLIO: rapoarte și dispute, bani blocați, comision, controale pentru prezentare."""
import streamlit as st

from core import config, db, logica, timp
from services import ai, nokia
from ui import comp as c


def panou(u):
    c.h('<div class="sk-title">Panou SKILLIO</div><div class="sk-cap">Doar pentru echipa SKILLIO</div>')
    s = logica.statistici_platforma()
    c.h('<div class="sk-stats">'
        f'<div class="sk-stat"><span class="v">{s["lucrari_active"]}</span><span class="l">Lucrări active</span></div>'
        f'<div class="sk-stat"><span class="v">{s["finalizate"]}</span><span class="l">Lucrări finalizate</span></div>'
        f'<div class="sk-stat"><span class="v" style="color:var(--sk-escrow)">{c.lei(s["blocat"])}</span>'
        f'<span class="l">Bani blocați acum</span></div>'
        f'<div class="sk-stat"><span class="v">{c.lei(s["comision"])}</span><span class="l">Comision încasat '
        f'({config.COMISION:.0%})</span></div>'
        f'<div class="sk-stat"><span class="v">{s["mesteri"]}</span><span class="l">Meșteri</span></div>'
        f'<div class="sk-stat"><span class="v">{s["utilizatori"]}</span><span class="l">Clienți</span></div></div>')

    deschise = logica.rapoarte("deschis")
    c.h(f'<div class="sk-label">Rapoarte de rezolvat ({len(deschise)})</div>')
    if not deschise:
        c.gol("Niciun raport deschis.", "check")
    for r in deschise:
        disp = '<span class="sk-badge danger">Dispută, bani blocați</span>' if r["disputa"] else ""
        with st.container(key=f"card_r{r['id']}"):
            c.h(f'<div class="sk-between"><div class="sk-h">{c.esc(r["motiv"])}</div>{disp}</div>'
                f'<div class="sk-cap">{c.esc(r["autor"])} → {c.esc(r["vizat"])} · {timp.de_cand(r["creat_la"])}'
                f'{" · " + c.esc(r["titlu"]) if r["titlu"] else ""}</div><div class="sk-b">{c.esc(r["detalii"])}</div>')
            rez = st.text_input("Decizia (o vede și utilizatorul)", key=f"rez_{r['id']}")
            with st.container(horizontal=True):
                et_ok = "Dă dreptate clientului" if r["disputa"] else "Confirmă raportul"
                et_no = "Dă dreptate meșterului" if r["disputa"] else "Respinge"
                if st.button(et_no, key=f"r_no{r['id']}", width="stretch"):
                    logica.rezolva_raport(r["id"], False, rez)
                    st.rerun()
                if st.button(et_ok, type="primary", key=f"r_ok{r['id']}", width="stretch"):
                    logica.rezolva_raport(r["id"], True, rez)
                    st.rerun()
            if r["lucrare_id"] and st.button("Vezi lucrarea", key=f"link_rl{r['id']}", type="tertiary"):
                c.go("lucrare", r["lucrare_id"])

    acte = db.q("SELECT * FROM utilizatori WHERE act_status = 'in_asteptare'")
    if acte:
        c.h(f'<div class="sk-label">Documente de verificat ({len(acte)})</div>')
        for m in acte:
            with st.container(key=f"card_act{m['id']}"):
                c.h(f'<div class="sk-row">{c.avatar(m)}<b class="sk-b">{c.esc(m["nume"])}</b></div>')
                if m["act_poza"] and not m["act_poza"].endswith(".pdf"):
                    st.image(m["act_poza"])
                if st.button("Marchează verificat", key=f"act_ok{m['id']}", type="primary", width="stretch"):
                    logica.actualizeaza_profil(m["id"], act_status="verificat")
                    st.rerun()

    with st.expander("Controale pentru prezentare", expanded=True):
        st.markdown(f"Ceasul aplicației: **{timp.data_ora(timp.acum())}** (decalaj {timp.decalaj_zile()} zile)")
        st.caption("Dă timpul înainte ca să apară întrebările „după o zi / o săptămână / o lună”.")
        with st.container(horizontal=True):
            for zile, et in ((1, "+1 zi"), (6, "+6 zile"), (23, "+23 zile")):
                if st.button(et, key=f"t_{zile}", width="stretch"):
                    db.pune_setare("decalaj_zile", timp.decalaj_zile() + zile)
                    st.rerun()
            if st.button("Ceas real", key="t_0", width="stretch"):
                db.pune_setare("decalaj_zile", 0)
                st.rerun()
        ionel = logica.user_dupa_telefon("+40722000101")
        if ionel:
            departe = st.toggle("Simulează că Ionel e departe de adresă (sosirea va fi respinsă)",
                                value=bool(ionel["departe_demo"]), key="t_departe")
            if departe != bool(ionel["departe_demo"]):
                logica.actualizeaza_profil(ionel["id"], departe_demo=int(departe))
                st.rerun()
        st.markdown(f"Gemini: **{'conectat' if ai.activ() else 'mod offline (reguli)'}** · "
                    f"Nokia: **{'conectat' if nokia.activ() else 'mod simulat'}**")
        st.caption("Cheile se pun în fișierul .env (vezi README).")
        if st.button("Resetează datele demo", key="danger_reset"):
            st.session_state["_confirm_reset"] = True
        if st.session_state.get("_confirm_reset"):
            st.warning("Se șterg toate lucrările și conturile noi, apoi se pun la loc datele demo.")
            with st.container(horizontal=True):
                if st.button("Renunță", key="reset_no", width="stretch"):
                    st.session_state.pop("_confirm_reset")
                    st.rerun()
                if st.button("Da, resetează", type="primary", key="reset_yes", width="stretch"):
                    st.session_state.pop("_confirm_reset")
                    db.reseteaza()
                    st.query_params.clear()
                    st.rerun()

    with st.expander("Toate lucrările"):
        for l in db.q("SELECT l.*, a.nume AS cn, b.nume AS mn FROM lucrari l JOIN utilizatori a ON a.id = l.client_id "
                      "LEFT JOIN utilizatori b ON b.id = l.mester_id WHERE l.status != 'finalizata' OR "
                      "l.confirmat_la >= ? ORDER BY l.id DESC LIMIT 40",
                      (timp.iso(timp.acum().replace(hour=0)),)):
            st.markdown(f"**#{l['id']} {l['titlu']}** · {logica.STATUS[l['status']][0]} · {l['cn']}"
                        f"{' → ' + l['mn'] if l['mn'] else ''}")
