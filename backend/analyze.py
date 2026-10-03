"""TÜİK HİA Alo124 Kalite Denetim analizi (T1-T13 kriter havuzu).
Motor: makinedeki opencode CLI (muse-spark 1.3, free, API key yok).
Yedek: ANALYZE_PROVIDER=ollama.

Akış: normalize_asr (ASR hatalarını düzelt) -> meta-prompt -> strict JSON ->
şema doğrulama + anlamlandırma (yorum) + genel skor.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import urllib.request

PROVIDER = os.environ.get("ANALYZE_PROVIDER", "opencode")
OPENCODE_BIN = os.environ.get("OPENCODE_BIN", "/Users/gurkanfikretgunak/.opencode/bin/opencode")
OPENCODE_MODEL = os.environ.get("ANALYZE_MODEL", "opencode/muse-spark-1.3-contributor-free")
OPENCODE_TIMEOUT = int(os.environ.get("ANALYZE_TIMEOUT", "300"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
REFERANS_HAFTA = os.environ.get("REFERANS_HAFTA", "")
MAX_CHARS = int(os.environ.get("ANALYZE_MAX_CHARS", "30000"))

# --- ASR normalizasyon (analiz öncesi bilinen kaymalar) ---
NORMALIZE = [
    (r"\bhani\s+halkı\b", "hanehalkı"),
    (r"\bstatistik\b", "istatistik"),
    (r"\bteş[kq]\b", "test"),
    (r"\biş\s+gücü\s+araştırması\b", "hanehalkı işgücü araştırması"),
]


def normalize_asr(text: str) -> str:
    t = text or ""
    for pat, rep in NORMALIZE:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip()


SYSTEM_TEMPLATE = """Sen TÜİK Hanehalkı İşgücü Araştırması (HİA) Alo124 Kalite Denetim uzmanısın.
Bir telefon görüşmesinin transkriptini T1-T13 kriterlerine göre denetle.
Sadece transkripte dayan, varsayımda bulunma. Hiçbir araç kullanma, sadece JSON döndür.
REFERANS_HAFTA: {refhafta} (boşsa: transkriptte net tarih aranır, "geçen hafta" tek başına yetersizdir)

KRİTERLER:
T1: Üç bilgi de olmalı (biri eksikse sonuc=hayir): kurum adı (Türkiye İstatistik Kurumu/TÜİK),
  araştırma adı TAM ve DOĞRU ("Hanehalkı İşgücü Araştırması"; "işsizliğin belirlenmesi, istihdam araştırması" YANLIŞ),
  kayıt bildirimi (telefonda yasal zorunluluk).
T2: Görüşme kişinin kendisiyle mi (ad-soyad sorusu, S1)? Başkası cevaplıyorsa proxy=true.
T3 (S32): Referans haftası net tarihle + en az 1 saat çalışma vurgusu sorgulandı mı?
T4 (S33): Net tarih + aile işletmesi/tarımsal işletmede ücretsiz çalışma sorgulandı mı?
T5 (S34+S36): Net tarih + başında bulunulmayan iş + çalışmama nedeni sorgulandı mı?
T6 (S35): Net tarih + örnek kısa iş türleri (özel ders, tadilat, bloggerlık...) sorgulandı mı?
T7 (S40): Ek iş ("Başka bir işiniz var mı?") net soruldu mu?
T8 (S66a/b): Net tarih + FİİLİ çalışma saati (genellikle çalışılandan ayrı) sorgulandı mı?
T9 (S67): "Daha fazla gelir elde etmek" ifadesiyle daha fazla çalışma isteği sorgulandı mı?
T10 (S75): Referans haftasıyla biten son 4 haftada iş arama sorgulandı mı?
T11 (S89a/b): Çalışmak istememe/iş aramama ASIL nedeni sorgulandı mı, yönlendirme yapılmadı mı?
T12: Yönlendirme var mı? (yorumdan kaçınma; teyit ile yönlendirmeyi ayır)
T13: Saygılı, nazik, kurumsal tutum sergilendi mi?

DURUM: "evet" | "hayir" | "belirsiz" (transkriptte yoksa/kısaysa belirsiz — hayir basma).
Her kritere: durum, puan (0-100), kanit (kısa alıntı veya "bulunamadı"), yorum (tek cümle anlamlandırma).
T1 alt kırılımlı: kurum / arastirma (+tespit_edilen_ad) / kayit_bildirimi + sonuc.
T12: yonlendirme_var (true/false). T2: proxy (true/false).

SADECE şu JSON'u döndür:
{{"t1":{{"kurum":{{"durum":"evet","puan":0,"kanit":"...","yorum":"..."}},
"arastirma":{{"durum":"evet","puan":0,"kanit":"...","yorum":"...","tespit_edilen_ad":null}},
"kayit_bildirimi":{{"durum":"evet","puan":0,"kanit":"...","yorum":"..."}},
"sonuc":"evet"}},
"t2":{{"durum":"evet","puan":0,"kanit":"...","yorum":"...","proxy":false}},
"t3":{{"durum":"evet","puan":0,"kanit":"...","yorum":"..."}}, ... (t4..t11 aynı),
"t12":{{"durum":"evet","puan":0,"kanit":"...","yorum":"...","yonlendirme_var":false}},
"t13":{{"durum":"evet","puan":0,"kanit":"...","yorum":"..."}},
"genel_skor":0,"ozet":"..."}}"""


def _prompt(body: str, refhafta: str, tamami: bool, diller: list | None = None) -> str:
    note = "" if tamami else "\nNOT: Çok uzun görüşme; son bölüm özet dışı kalmış olabilir, sondaki sorular belirsiz işaretlenebilir."
    dilsatir = f"\nTESPİT EDİLEN DİLLER: {', '.join(diller or [])} — transkript bu dillerde oluşturuldu." if diller else ""
    return SYSTEM_TEMPLATE.format(refhafta=refhafta or "belirtilmedi") + dilsatir + "\n\nTRANSKRİPT (zaman damgalı [bölüm]):\n" + body + note


def _via_opencode(prompt: str) -> str:
    p = subprocess.run(
        [OPENCODE_BIN, "run", "--model", OPENCODE_MODEL],
        input=prompt.encode(), capture_output=True, timeout=OPENCODE_TIMEOUT,
    )
    out = p.stdout.decode(errors="replace")
    if p.returncode != 0:
        raise RuntimeError("opencode run hata: " + (p.stderr.decode(errors="replace") or out)[-300:])
    return out


def _via_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json", "stream": False,
        "options": {"temperature": 0.1, "num_predict": 2000},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL + "/api/chat", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["message"]["content"]


def _blank(neden: str) -> dict:
    def item():
        return {"durum": "belirsiz", "puan": 0, "kanit": neden, "yorum": neden}
    out = {f"t{i}": item() for i in range(2, 12)}
    out["t1"] = {"kurum": item(), "arastirma": {**item(), "tespit_edilen_ad": None},
                 "kayit_bildirimi": item(), "sonuc": "belirsiz"}
    out["t2"] = {**item(), "proxy": False}
    out["t12"] = {**item(), "yonlendirme_var": False}
    out["t13"] = item()
    out.update(genel_skor=0, ozet="Analiz yapılamadı: " + neden, hata=neden)
    return out


def _score_of(d: dict) -> int | None:
    if d.get("durum") == "evet":
        return 100
    if d.get("durum") == "hayir":
        return 0
    return None  # belirsiz -> ortalamaya katılmaz


def _validate(out: dict, model: str, refhafta: str) -> dict:
    def item():
        return {"durum": "belirsiz", "puan": 0, "kanit": "bulunamadı", "yorum": ""}
    t1 = out.get("t1") or {}
    for k in ("kurum", "arastirma", "kayit_bildirimi"):
        if not isinstance(t1.get(k), dict):
            t1[k] = item()
    t1["arastirma"].setdefault("tespit_edilen_ad", None)
    subs = [t1["kurum"].get("durum"), t1["arastirma"].get("durum"), t1["kayit_bildirimi"].get("durum")]
    t1["sonuc"] = "hayir" if "hayir" in subs else ("evet" if all(s == "evet" for s in subs) else "belirsiz")
    out["t1"] = t1
    scores: list[int] = []
    s = _score_of({"durum": t1["sonuc"]})
    if s is not None:
        scores.append(s)
    for i in list(range(2, 12)) + [12, 13]:
        k = f"t{i}"
        d = out.get(k)
        if not isinstance(d, dict):
            d = item()
            out[k] = d
        for f in ("durum", "puan", "kanit", "yorum"):
            d.setdefault(f, item()[f])
        if d.get("durum") not in ("evet", "hayir", "belirsiz"):
            d["durum"] = "belirsiz"
        sc = _score_of(d)
        if sc is not None:
            scores.append(sc)
    out.setdefault("t2", {}).setdefault("proxy", False)
    out.setdefault("t12", {}).setdefault("yonlendirme_var", False)
    out["genel_skor"] = round(sum(scores) / len(scores)) if scores else 0
    out["degerlendirilen"] = len(scores)
    out.setdefault("ozet", "")
    out["model"] = model
    out["referans_hafta"] = refhafta
    return out


def build_prompt_text(text: str, segments: list | None) -> tuple[str, bool]:
    """Segmentleri zaman damgalı satırlara döker. (metin, tamamı_mı) döner."""
    lines: list[str] = []
    for s in segments or []:
        try:
            tag = f"P{s.get('part', '?')} {float(s.get('start', 0)):.1f}-{float(s.get('end', 0)):.1f}"
            lines.append(f"[{tag}] {(s.get('text') or '').strip()}")
        except Exception:
            continue
    body = normalize_asr("\n".join(lines) if lines else (text or ""))
    if len(body) <= MAX_CHARS:
        return body, True
    cut = body[:MAX_CHARS]
    nl = cut.rfind("\n")
    return (cut[:nl] if nl > MAX_CHARS - 500 else cut), False


def analyze_transcript(text: str, model: str = OPENCODE_MODEL, refhafta: str = REFERANS_HAFTA,
                       segments: list | None = None, diller: list | None = None) -> dict:
    """T1-T13 denetimi. Hata durumunda is düşürmeyen blank dict."""
    body, tamami = build_prompt_text(text, segments)
    if not body.strip():
        return _blank("boş transkript")
    try:
        prompt = _prompt(body, refhafta, tamami, diller)
        raw = _via_opencode(prompt) if PROVIDER == "opencode" else _via_ollama(prompt)
    except Exception as e:  # noqa: BLE001
        return _blank(f"modele ulaşılamadı ({e})")
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return _blank("model geçerli JSON döndürmedi")
    try:
        out = _validate(json.loads(raw[start:end + 1]), model, refhafta)
    except Exception:
        return _blank("model çıktısı ayrıştırılamadı")
    out["transkript_tamami"] = tamami
    out["transkript_karakter"] = len(body)
    out["diller"] = diller or []
    return out
