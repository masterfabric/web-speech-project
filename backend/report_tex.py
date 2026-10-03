"""LaTeX denetim raporu — .tex üretimi + tectonic ile PDF derleme.
Türkçe karakterler ASCII LaTeX komutlarına kaçırılır (her motorda derlenir).
"""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path

from report import data, TITLES, DURUM_TR

TECTONIC = "/opt/homebrew/bin/tectonic"

TRMAP = {"ğ": r"\u{g}", "Ğ": r"\u{G}", "ş": r"\c{s}", "Ş": r"\c{S}",
         "ı": r"{\i}", "İ": r"\.{I}", "ç": r"\c{c}", "Ç": r"\c{C}",
         "ö": r'\"o', "Ö": r'\"O', "ü": r'\"u', "Ü": r'\"U',
         "â": r"\^a", "ê": r"\^e", "î": r"\^i", "ô": r"\^o", "û": r"\^u",
         "—": "---", "–": "--", "“": "``", "”": "''", '"': "''",
         "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
         "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
         "\\": r"\textbackslash{}"}


def esc(s) -> str:
    out = []
    for ch in str(s or ""):
        if ch in TRMAP:
            out.append(TRMAP[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            out.append(f"\\char\"{ord(ch):04X}")
    return "".join(out).replace("\n", " ")


def badge(durum: str) -> str:
    d = esc(DURUM_TR.get(durum, "-"))
    if durum == "evet":
        return r"\colorbox{green!25}{\textbf{" + d + "}}"
    if durum == "hayir":
        return r"\colorbox{red!25}{\textbf{" + d + "}}"
    return r"\colorbox{gray!20}{\textbf{" + d + "}}"


def finding_rows(a: dict) -> str:
    rows = []
    t1 = a.get("t1") or {}
    subs = [("Kurum", t1.get("kurum") or {}),
            ("Arastirma", t1.get("arastirma") or {}),
            ("Kayit", t1.get("kayit_bildirimi") or {})]
    for label, s in subs:
        rows.append("T1-" + label + " & " + badge(s.get("durum")) + " & "
                    + str(s.get("puan", 0)) + " & " + esc(s.get("kanit")) + " & " + esc(s.get("yorum")) + r" \\ \hline")
    rows.append(r"\multicolumn{5}{|l|}{\textbf{T1 sonuc:} " + esc(DURUM_TR.get(t1.get("sonuc"), "-")) + r"} \\ \hline")
    for i in list(range(2, 14)):
        k = f"t{i}"
        s = a.get(k) or {}
        extra = ""
        if k == "t2" and s.get("proxy"):
            extra = " PROXY!"
        if k == "t12" and s.get("yonlendirme_var"):
            extra = " YONLENDIRME!"
        rows.append(f"T{i} & " + badge(s.get("durum")) + " & " + str(s.get("puan", 0))
                    + " & " + esc(s.get("kanit")) + " & " + esc(s.get("yorum")) + esc(extra) + r" \\ \hline")
    return "\n".join(rows)


def render_tex(job: dict) -> str:
    d = data(job)
    a = d["analysis"]
    m = d["meta"]
    parcalar = m.get("parcalar") or []
    parca_tex = "\n".join(
        r"\item \textbf{" + esc(p.get("etiket", "")) + "} "
        + f"[{p.get('baslangic_sn', '?')} sn, dil: {esc(p.get('dil', '?'))}] " + esc(p.get("metin", ""))
        for p in parcalar)
    return r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2cm]{geometry}
\usepackage{xcolor,colortbl,longtable,booktabs,hyperref,enumitem}
\hypersetup{colorlinks=true,linkcolor=blue}
\title{Hanehalki Isgucu Arastirmasi --- Alo124 Kalite Denetim Raporu}
\author{web-speech-project (otomatik)}
\date{""" + esc(d["finished"] or d["created"]) + r"""}
\begin{document}
\maketitle

\section*{Ozet}
\textbf{Genel skor: """ + str(a.get("genel_skor", 0)) + r"""/100} \quad (""" + str(a.get("degerlendirilen", "-")) + r""" kriter degerlendirildi)

""" + esc(a.get("ozet")) + r"""

\section*{Meta Bilgiler}
\begin{tabular}{ll}
\toprule
Ses dosyasi & """ + esc(d["filename"]) + r""" \\
Job & """ + esc(d["id"]) + r""" \\
Islem & """ + esc(d["created"]) + " $\\to$ " + esc(d["finished"]) + r""" \\
STT model & """ + esc(m.get("model", "-")) + r""" \\
Analiz & opencode $\cdot$ """ + esc(a.get("model", "-")) + r""" \\
Sure & """ + esc(m.get("duration", "-")) + r""" sn, """ + esc(m.get("chunks", "-")) + r""" segment \\
Diller & """ + esc(", ".join(m.get("diller") or a.get("diller") or [])) + r""" \\
Referans hafta & """ + esc(m.get("referans_hafta") or a.get("referans_hafta") or "-") + r""" \\
Orneklem & """ + esc(m.get("orneklem_sn", "-")) + r""" sn $\times$ 2 parcada (bas + orta) \\
Transkript aktarimi & """ + esc(a.get("transkript_karakter", "-")) + " karakter (tamami: " + ("evet" if a.get("transkript_tamami") else "hayir") + ")" + r""" \\
\bottomrule
\end{tabular}

\section*{T1--T13 Bulgulari}
\begin{longtable}{|l|l|c|p{4.5cm}|p{4.5cm}|}
\hline
\textbf{Kriter} & \textbf{Durum} & \textbf{Puan} & \textbf{Kanit} & \textbf{Yorum} \\ \hline
\endhead
""" + finding_rows(a) + r"""
\end{longtable}

\section*{Orneklem Parcalari}
\begin{enumerate}[leftmargin=*]
""" + parca_tex + r"""
\end{enumerate}

\section*{Transkript (tamam)}
""" + esc(d["transcript"]) + r"""

\section*{Duygu / Akustik}
Duygu: """ + esc(json.dumps((d["scores"] or {}).get("duyguDagilimi", {}), ensure_ascii=False)) + r""", sentiment: """ + esc((d["scores"] or {}).get("sentiment", "-")) + r""", kelime: """ + esc((d["scores"] or {}).get("kelimeSayisi", "-")) + r""".

Akustik: enerji=""" + esc((d["acoustic"] or {}).get("ortalamaEnerji", "-")) + r""", tepe=""" + esc((d["acoustic"] or {}).get("tepe", "-")) + r""", sessizlik=""" + esc((d["acoustic"] or {}).get("sessizlikOrani", "-")) + r""".
\end{document}
"""


def compile_pdf(tex: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "rapor.tex"
        src.write_text(tex, encoding="ascii")
        r = subprocess.run([TECTONIC, "-X", "compile", str(src), "--outdir", td],
                           capture_output=True, text=True, timeout=300)
        pdf = Path(td) / "rapor.pdf"
        if not pdf.exists():
            raise RuntimeError("tectonic derleyemedi: " + (r.stderr or r.stdout)[-500:])
        return pdf.read_bytes()
