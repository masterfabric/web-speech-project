"""HİA Alo124 denetim raporu — PDF + HTML önizleme.
Tüm meta bilgiler raporda: dosya, tarih, modeller, süre, referans hafta,
T1-T13 bulguları (kanıt+yorum), transkript, duygu/akustik.
"""
from __future__ import annotations
import html
import json
from datetime import datetime

FONT_DIR = "/System/Library/Fonts/Supplemental/"
TITLES = {
    "t1": "T1 — Kurum + araştırma adı + kayıt bildirimi",
    "t2": "T2 — Kişinin kendisiyle görüşme",
    "t3": "T3 — S32: 1 saat bile olsa gelir getirici iş",
    "t4": "T4 — S33: ücretsiz aile işçisi",
    "t5": "T5 — S34+36: başında bulunulmayan iş + neden",
    "t6": "T6 — S35: küçük/düzensiz işler",
    "t7": "T7 — S40: ek iş",
    "t8": "T8 — S66: fiili çalışma saati",
    "t9": "T9 — S67: daha fazla çalışma isteği",
    "t10": "T10 — S75: son 4 haftada iş arama",
    "t11": "T11 — S89: çalışmak istememe / aramama nedeni",
    "t12": "T12 — Yönlendirme kontrolü",
    "t13": "T13 — Saygılı / nazik tutum",
}
DURUM_TR = {"evet": "EVET", "hayir": "HAYIR", "belirsiz": "—"}


def _j(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return None
    return v


def data(job: dict) -> dict:
    return {
        "id": job.get("id"), "filename": job.get("filename"),
        "created": (job.get("created_at") or "")[:19].replace("T", " "),
        "finished": (job.get("finished_at") or "")[:19].replace("T", " "),
        "meta": _j(job.get("meta")) or {}, "scores": _j(job.get("scores")) or {},
        "acoustic": _j(job.get("acoustic")) or {}, "analysis": _j(job.get("analysis")) or {},
        "transcript": job.get("transcript") or "",
        "segments": _j(job.get("segments")) or [],
    }


def _t1_subs(a: dict) -> list[tuple[str, dict]]:
    t1 = a.get("t1") or {}
    return [("Kurum adı", t1.get("kurum") or {}),
            (f"Araştırma adı ({(t1.get('arastirma') or {}).get('tespit_edilen_ad') or 'tespit edilemedi'})",
             t1.get("arastirma") or {}),
            ("Kayıt bildirimi", t1.get("kayit_bildirimi") or {})]


def render_pdf(job: dict) -> bytes:
    from fpdf import FPDF
    d = data(job)
    a = d["analysis"]
    pdf = FPDF(format="A4")
    pdf.add_font("Arial", "", FONT_DIR + "Arial.ttf")
    pdf.add_font("Arial", "B", FONT_DIR + "Arial Bold.ttf")
    pdf.add_font("Arial", "I", FONT_DIR + "Arial Italic.ttf")
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Hanehalkı İşgücü Araştırması — Alo124 Kalite Denetim Raporu", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Rapor: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Job: {d['id']}", new_x="LMARGIN", new_y="NEXT")

    def meta_row(k, v):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(48, 7, k)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 7, str(v), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    m = d["meta"]
    meta_row("Ses dosyası", d["filename"])
    meta_row("İşlem tarihi", f"{d['created']}  →  {d['finished']}")
    meta_row("STT model", m.get("model", "—"))
    meta_row("Analiz modeli", f"opencode · {a.get('model', '—')}")
    meta_row("Süre", f"{m.get('duration', '—')} sn · {m.get('chunks', '—')} segment")
    meta_row("Referans hafta", m.get("referans_hafta") or a.get("referans_hafta") or "—")
    meta_row("Genel skor", f"{a.get('genel_skor', 0)} / 100  ({a.get('degerlendirilen', '—')} kriter değerlendirildi)")
    meta_row("Transkript aktarımı", f"{a.get('transkript_karakter', '—')} karakter (tamamı: {'evet' if a.get('transkript_tamami') else 'hayır — kesildi'})")
    pdf.ln(1)
    pdf.set_font("Arial", "I", 10)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, "Özet: " + (a.get("ozet") or "—"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "T1–T13 Bulguları", new_x="LMARGIN", new_y="NEXT")
    for i in list(range(1, 14)):
        k = f"t{i}"
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, TITLES[k], new_x="LMARGIN", new_y="NEXT")
        if k == "t1":
            for label, sub in _t1_subs(a):
                _finding(pdf, label, sub)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, f"T1 sonuç: {DURUM_TR.get((a.get('t1') or {}).get('sonuc'), '—')}",
                     new_x="LMARGIN", new_y="NEXT")
        else:
            _finding(pdf, None, a.get(k) or {})
        if k == "t2" and (a.get("t2") or {}).get("proxy"):
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, "UYARI: proxy görüşme tespiti", new_x="LMARGIN", new_y="NEXT")
        if k == "t12" and (a.get("t12") or {}).get("yonlendirme_var"):
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, "UYARI: yönlendirme tespiti", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Transkript", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, d["transcript"] or "—", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Duygu / Akustik", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 10)
    sc, ac = d["scores"], d["acoustic"]
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, f"Duygu dağılımı: {json.dumps(sc.get('duyguDagilimi', {}), ensure_ascii=False)}"
                         f"  ·  Sentiment: {sc.get('sentiment', '—')}  ·  Kelime: {sc.get('kelimeSayisi', '—')}",
                 new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, f"Akustik: enerji={ac.get('ortalamaEnerji', '—')} tepe={ac.get('tepe', '—')} "
                         f"sessizlik={ac.get('sessizlikOrani', '—')}", new_x="LMARGIN", new_y="NEXT")
    if a.get("hata"):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, "Analiz notu: " + a["hata"], new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def _finding(pdf, label, sub):
    st = DURUM_TR.get(sub.get("durum"), "—")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f"[ {st} ] {sub.get('puan', 0)} puan" + (f" — {label}" if label else ""),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, "Kanıt: " + (sub.get("kanit") or "—"), new_x="LMARGIN", new_y="NEXT")
    if sub.get("yorum"):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, "Yorum: " + sub["yorum"], new_x="LMARGIN", new_y="NEXT")


def _badge_html(durum: str) -> str:
    d = DURUM_TR.get(durum, "—")
    c = {"evet": "#d3f9d8", "hayir": "#ffd6d6"}.get(durum, "#e9ecef")
    return f'<span style="background:{c};padding:2px 10px;border-radius:99px;font-weight:700">{d}</span>'


def render_html(job: dict) -> str:
    d = data(job)
    a = d["analysis"]
    m = d["meta"]
    skor = a.get("genel_skor", 0)
    parcalar = "".join(
        f"<li><b>{html.escape(str(p.get('etiket', '')))}</b> [{p.get('baslangic_sn', '?')} sn · dil: {html.escape(str(p.get('dil', '?')))}]<br>{html.escape(str(p.get('metin', '')))}</li>"
        for p in (m.get("parcalar") or []))
    rows = []
    t1 = a.get("t1") or {}
    subs = "".join(
        f"<tr><td>T1 · {lab}</td><td>{_badge_html(s.get('durum'))}</td><td>{s.get('puan', 0)}</td>"
        f"<td>{html.escape(str(s.get('kanit') or '—'))}</td><td>{html.escape(str(s.get('yorum') or '—'))}</td></tr>"
        for lab, s in [("Kurum", t1.get("kurum") or {}),
                       (f"Araştırma ({(t1.get('arastirma') or {}).get('tespit_edilen_ad') or '?'})", t1.get("arastirma") or {}),
                       ("Kayıt", t1.get("kayit_bildirimi") or {})])
    rows.append(subs + f"<tr><td colspan=5><b>T1 sonuç: {DURUM_TR.get(t1.get('sonuc'), '—')}</b></td></tr>")
    for i in list(range(2, 14)):
        k = f"t{i}"
        s = a.get(k) or {}
        flag = " <b>PROXY!</b>" if (k == "t2" and s.get("proxy")) else ""
        flag += " <b>YÖNLENDİRME!</b>" if (k == "t12" and s.get("yonlendirme_var")) else ""
        rows.append(f"<tr><td>{TITLES[k]}</td><td>{_badge_html(s.get('durum'))}</td><td>{s.get('puan', 0)}</td>"
                    f"<td>{html.escape(str(s.get('kanit') or '—'))}</td><td>{html.escape(str(s.get('yorum') or '—'))}{flag}</td></tr>")
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>Denetim Raporu {html.escape(str(d['id']))}</title>
<style>body{{font-family:system-ui;max-width:900px;margin:auto;padding:20px;color:#222}}
.hero{{background:#f1f3f5;border-radius:14px;padding:18px}}table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #dee2e6;padding:8px;vertical-align:top;font-size:14px}}.muted{{color:#666}}</style></head><body>
<div class=hero><h1 style="margin:0">HİA Alo124 Kalite Denetim Raporu</h1>
<p style="font-size:28px;margin:8px 0"><b>Genel skor: {skor} / 100</b></p>
<p>{html.escape(str(a.get('ozet') or ''))}</p>
<p class=muted>Dosya: <b>{html.escape(str(d['filename']))}</b> · Job: {html.escape(str(d['id']))}<br>
STT: {html.escape(str(m.get('model', '—')))} · Analiz: opencode · {html.escape(str(a.get('model', '—')))}<br>
Süre: {html.escape(str(m.get('duration', '—')))} sn · Diller: {html.escape(', '.join(m.get('diller') or a.get('diller') or []))} · Referans hafta: {html.escape(str(m.get('referans_hafta') or a.get('referans_hafta') or '—'))}<br>
Transkript: {a.get('transkript_karakter', '—')} karakter ({'tamamı' if a.get('transkript_tamami') else 'kesildi'})</p></div>
<h2>T1–T13 Bulguları</h2>
<table><tr><th>Kriter</th><th>Durum</th><th>Puan</th><th>Kanıt</th><th>Yorum</th></tr>{''.join(rows)}</table>
<h2>Örneklem Parçaları</h2><ol>{parcalar or '<li>—</li>'}</ol>
<h2>Transkript</h2><p>{html.escape(d['transcript'])}</p>
<h2>Duygu / Akustik</h2><p>{html.escape(json.dumps(d['scores'], ensure_ascii=False))}<br>{html.escape(json.dumps(d['acoustic'], ensure_ascii=False))}</p>
</body></html>"""
