"""web-speech-project backend — FastAPI, modeller içeride, işlem + kayıt.
Calistir: uvicorn app:app --port 8001 --reload (backend/ icinden)
"""
from __future__ import annotations
import json
import shutil
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
DATA = BASE / "data"
REPORTS = DATA / "reports"
DB = DATA / "app.db"
UPLOADS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

FFMPEG = shutil.which("ffmpeg")
SAMPLE_SEC = int(__import__("os").environ.get("ORNEKLEM_SN", "60"))
ALLOWED_WAV_ONLY = FFMPEG is None
ALLOWED_EXT = {".wav"} if ALLOWED_WAV_ONLY else {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".mp4"}

MODEL_MAP = {"tiny": "tiny", "base": "base", "small": "small", "medium": "medium"}
_model_cache: dict[str, object] = {}

app = FastAPI(title="web-speech-project backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def db() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute(
        """CREATE TABLE IF NOT EXISTS jobs(
        id TEXT PRIMARY KEY, filename TEXT, status TEXT, progress REAL,
        created_at TEXT, finished_at TEXT, transcript TEXT,
        segments TEXT, scores TEXT, acoustic TEXT, meta TEXT, error TEXT)"""
    )
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN analysis TEXT")
    except sqlite3.OperationalError:
        pass  # kolon zaten var
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN stage TEXT")
    except sqlite3.OperationalError:
        pass  # kolon zaten var
    for col, typ in (("parent", "TEXT"), ("version", "INTEGER")):
        try:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass  # kolon zaten var
    return c


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_job(row: dict) -> None:
    c = db()
    c.execute(
        """INSERT OR REPLACE INTO jobs
        (id,filename,status,progress,created_at,finished_at,transcript,segments,scores,acoustic,meta,error,analysis,stage,parent,version)
        VALUES (:id,:filename,:status,:progress,:created_at,:finished_at,:transcript,:segments,:scores,:acoustic,:meta,:error,:analysis,:stage,:parent,:version)""",
        {**row, "analysis": row.get("analysis"), "stage": row.get("stage"),
         "parent": row.get("parent"), "version": row.get("version", 1)},
    )
    c.commit()
    c.close()


def get_job(job_id: str) -> dict | None:
    c = db()
    r = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    c.close()
    return dict(r) if r else None


LEX = {
    "mutluluk": ["harika", "güzel", "mutlu", "sev", "teşekkür", "süper", "mükemmel", "iyi"],
    "ofke": ["sinir", "kızgın", "rezalet", "berbat", "lanet", "saçma", "kötü"],
    "uzuntu": ["üzgün", "üzücü", "ağla", "kaybett", "yazık", "mutsuz"],
    "kaygi": ["korku", "endişe", "kaygı", "stres", "panik", "gergin", "korkuyorum"],
}


def rule_scores(text: str) -> dict:
    t = text.lower()
    pct: dict[str, int] = {}
    total = 0
    counts = {k: sum(t.count(w) for w in v) for k, v in LEX.items()}
    total = sum(counts.values())
    for k in LEX:
        pct[k] = round(counts[k] / total * 100) if total else 0
    pct["notr"] = 0 if total else 100
    sentiment = (pct["mutluluk"] - pct["ofke"] - pct["uzuntu"] - pct["kaygi"]) / 100
    return {"duyguDagilimi": pct, "sentiment": round(sentiment, 2),
            "kelimeSayisi": len(t.split())}


def acoustic_of(path: Path) -> dict:
    import soundfile as sf
    data, sr = sf.read(str(path), always_2d=False)
    if getattr(data, "ndim", 1) > 1:
        data = np.mean(data, axis=1)
    # 16k'ya basit decimation yok — sadece istatistik
    flat = np.abs(np.asarray(data, dtype=np.float64)[::10])
    return {"ortalamaEnerji": round(float(np.mean(flat)), 4),
            "tepe": round(float(np.max(flat)), 4),
            "sessizlikOrani": round(float(np.mean(flat < 0.01)), 3),
            "orneklemeHz": int(sr), "sureSn": round(float(len(data) / sr), 2)}


def get_model(size: str):
    if size not in _model_cache:
        from faster_whisper import WhisperModel
        _model_cache[size] = WhisperModel(size, device="cpu", compute_type="int8")
    return _model_cache[size]


def wav_duration(path: Path) -> float:
    import soundfile as sf
    info = sf.info(str(path))
    return info.frames / info.samplerate if info.samplerate else 0.0


def make_parts(wav: Path, sec: int = SAMPLE_SEC) -> list[tuple[str, Path, float]]:
    """2 parça: baştan + ortadan. Kısa dosyada yarı/yarı. (etiket, yol, offset_sn)"""
    import subprocess
    dur = wav_duration(wav)
    if dur <= 2 * sec:
        spans = [("1. bölüm (baş)", 0.0, dur / 2), ("2. bölüm (orta)", dur / 2, dur / 2)]
    else:
        mid = dur / 2
        spans = [("1. bölüm (baş)", 0.0, float(sec)), ("2. bölüm (orta)", max(0.0, mid - sec / 2), float(sec))]
    out = []
    for label, start, length in spans:
        dst = wav.with_name(f"{wav.stem}.{label.split()[0]}-{int(start)}s.wav")
        subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", str(round(start, 1)),
                        "-i", str(wav), "-t", str(round(length, 1)),
                        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)], check=True)
        out.append((label, dst, start))
    return out


def ensure_wav(src: Path) -> Path:
    """mp3/m4a/ogg/flac/mp4 -> 16k mono wav (ffmpeg). wav ise aynen döner."""
    if src.suffix.lower() == ".wav":
        return src
    if not FFMPEG:
        raise RuntimeError("ffmpeg yok, sadece .wav destekleniyor")
    dst = src.with_suffix(".conv16k.wav")
    import subprocess
    r = subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)],
        capture_output=True, text=True,
    )
    if not dst.exists():
        raise RuntimeError("ffmpeg dönüşümü başarısız: " + (r.stderr or "")[:200])
    return dst


def process_job(job_id: str, fpath: Path, model_size: str, language: str | None, refhafta: str = ""):
    job = get_job(job_id)
    if not job:
        return
    try:
        job.update(status="processing", progress=10.0, stage="ses hazırlanıyor (format dönüşümü)")
        save_job(job)
        wav = ensure_wav(fpath)
        job.update(progress=20.0, stage="transkript yazılıyor (faster-whisper)")
        save_job(job)
        model = get_model(model_size)
        job.update(progress=30.0, stage="örneklem alınıyor (baş + orta)")
        save_job(job)
        parts = make_parts(wav)
        timed, texts, part_info, diller = [], [], [], []
        for idx, (label, ppath, offset) in enumerate(parts):
            job.update(progress=30.0 + idx * 20.0,
                       stage=f"transkript yazılıyor: {label} (faster-whisper)")
            save_job(job)
            # dil tespiti: auto ise modelin bulduğu dil, değilse seçili dil
            segs, info = model.transcribe(str(ppath), language=language, task="transcribe",
                                          vad_filter=True, word_timestamps=False)
            det = (getattr(info, "language", None) or language or "tr").lower()
            diller.append(det)
            ptext = []
            for s in segs:
                timed.append({"start": round(s.start + offset, 2), "end": round(s.end + offset, 2),
                              "text": s.text.strip(), "part": idx + 1, "lang": det})
                ptext.append(s.text.strip())
            part_info.append({"etiket": label, "baslangic_sn": round(offset, 1),
                              "dil": det, "dil_olasilik": round(float(getattr(info, "language_probability", 0) or 0), 2),
                              "metin": " ".join(ptext).strip()})
            texts.append(" ".join(ptext).strip())
        full = " ".join(t for t in texts if t).strip() or "(boş — ses anlaşılamadı)"
        diller = sorted(set(diller))
        job.update(progress=80.0, stage="skorlar hesaplanıyor")
        save_job(job)
        acoustic = acoustic_of(wav)
        scores = rule_scores(full)
        meta = {"file": job["filename"], "model": f"faster-whisper-{model_size}",
                "duration": acoustic.get("sureSn"), "chunks": len(timed),
                "referans_hafta": refhafta or None, "language": language or "turkish",
                "orneklem_sn": SAMPLE_SEC, "parcalar": part_info, "diller": diller}
        job.update(progress=90.0, stage="opencode analiz ediyor (muse-spark 1.3)")
        save_job(job)
        try:
            from analyze import analyze_transcript
            analysis = analyze_transcript(full, refhafta=refhafta, segments=timed, diller=diller)
        except Exception as e:  # noqa: BLE001 - analiz işi düşürmesin
            analysis = {"hata": str(e), "genel_skor": 0, "ozet": "Analiz atlandı."}
        job.update(status="done", progress=100.0, stage="bitti", finished_at=now(), transcript=full,
                   segments=json.dumps(timed, ensure_ascii=False),
                   scores=json.dumps(scores, ensure_ascii=False),
                   acoustic=json.dumps(acoustic), meta=json.dumps(meta, ensure_ascii=False),
                   analysis=json.dumps(analysis, ensure_ascii=False))
        save_job(job)
        try:
            job.update(progress=100.0, stage="rapor arşivleniyor (LaTeX)")
            save_job(job)
            from report_tex import render_tex, compile_pdf
            tex = render_tex(dict(job))
            (REPORTS / f"{job_id}.tex").write_text(tex, encoding="ascii")
            (REPORTS / f"{job_id}.pdf").write_bytes(compile_pdf(tex))
            job.update(stage="bitti")
            save_job(job)
        except Exception as e:  # noqa: BLE001 - arşiv hatası işi bozmaz
            job.update(stage="bitti", error=None)
            save_job(job)
            (REPORTS / f"{job_id}.hata.txt").write_text(str(e)[:500])
    except Exception as e:  # noqa: BLE001
        job.update(status="error", stage="hata", finished_at=now(), error=str(e))
        save_job(job)


@app.get("/health")
def health():
    return {"ok": True, "ffmpeg": bool(FFMPEG), "wavOnly": ALLOWED_WAV_ONLY,
            "allowed": sorted(ALLOWED_EXT), "ts": now()}


@app.get("/api/models")
def models():
    return {"models": [{"id": k, "label": f"faster-whisper-{k}"} for k in MODEL_MAP],
            "ffmpeg": bool(FFMPEG)}


@app.post("/api/jobs")
async def create_job(background: BackgroundTasks, file: UploadFile = File(...),
                     model: str = Form("base"), language: str = Form("turkish"),
                     refhafta: str = Form("")):
    size = (model or "base").lower()
    if size not in MODEL_MAP:
        raise HTTPException(400, f"bilinmeyen model: {model}")
    ext = Path(file.filename or "audio.wav").suffix.lower() or ".wav"
    if ext not in ALLOWED_EXT:
        hint = "ffmpeg yok, sadece .wav yükle (`brew install ffmpeg` sonrası mp3/m4a açılır)" if ALLOWED_WAV_ONLY else None
        raise HTTPException(400, f".{ext} desteklenmiyor. {hint or ''}")
    job_id = uuid.uuid4().hex[:12]
    dest = UPLOADS / f"{job_id}{ext}"
    content = await file.read()
    if len(content) > 300 * 1024 * 1024:
        raise HTTPException(400, "dosya çok büyük (300MB limit)")
    dest.write_bytes(content)
    lang = None if language == "auto" else ({"turkish": "tr", "english": "en"}.get(language, language))
    row = {"id": job_id, "filename": file.filename, "status": "queued", "progress": 0.0,
           "created_at": now(), "finished_at": None, "transcript": None, "segments": None,
           "scores": None, "acoustic": None, "meta": None, "error": None,
           "analysis": None, "stage": "kuyrukta", "parent": None, "version": 1}
    save_job(row)
    background.add_task(process_job, job_id, dest, size, lang, refhafta.strip())
    return {"id": job_id, "status": "queued"}


def _out(job: dict) -> dict:
    j = dict(job)
    for k in ("segments", "scores", "acoustic", "meta", "analysis"):
        try:
            j[k] = json.loads(j[k]) if j[k] else None
        except Exception:
            pass
    return j


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "job yok")
    return _out(job)


@app.post("/api/records/{job_id}/rescore")
def rescore(job_id: str, background: BackgroundTasks, model: str = "base"):
    """Arşivden tekrar skorla: aynı dosya yeni versiyon (v+1) olarak işlenir, eski durur."""
    src = get_job(job_id)
    if not src:
        raise HTTPException(404, "job yok")
    root = src.get("parent") or src["id"]
    c = db()
    c.execute("UPDATE jobs SET version=1 WHERE version IS NULL")
    c.execute("UPDATE jobs SET parent=id WHERE parent IS NULL")
    mx = c.execute("SELECT MAX(version) FROM jobs WHERE id=? OR parent=?", (root, root)).fetchone()[0] or 1
    c.close()
    import shutil as _sh
    orig = next((p for p in UPLOADS.glob(f"{src['id']}.*") if ".conv" not in p.name and ".1-" not in p.name and ".2-" not in p.name), None)
    if not orig or not orig.exists():
        raise HTTPException(400, "kaynak ses dosyası bulunamadı")
    size = (model or "base").lower()
    if size not in MODEL_MAP:
        raise HTTPException(400, f"bilinmeyen model: {model}")
    new_id = uuid.uuid4().hex[:12]
    dest = UPLOADS / f"{new_id}{orig.suffix}"
    _sh.copy(orig, dest)
    meta = {}
    try:
        meta = json.loads(src.get("meta") or "{}")
    except Exception:
        pass
    lang = (meta.get("language") or "tr")
    lang = {"turkish": "tr", "english": "en"}.get(lang, lang)
    row = {"id": new_id, "filename": src.get("filename"), "status": "queued", "progress": 0.0,
           "created_at": now(), "finished_at": None, "transcript": None, "segments": None,
           "scores": None, "acoustic": None, "meta": None, "error": None,
           "analysis": None, "stage": "kuyrukta", "parent": root, "version": mx + 1}
    save_job(row)
    background.add_task(process_job, new_id, dest, size, lang, meta.get("referans_hafta") or "")
    return {"id": new_id, "version": mx + 1, "status": "queued"}


@app.get("/api/records")
def records(limit: int = 50):
    c = db()
    rows = c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [_out(dict(r)) for r in rows]


@app.get("/api/reports")
def reports(limit: int = 100):
    """Arşivlenmiş raporların tablo listesi (sadece bitmiş işler)."""
    c = db()
    rows = c.execute(
        "SELECT * FROM jobs WHERE status='done' ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    out = []
    for r in rows:
        j = _out(dict(r))
        a = j.get("analysis") or {}
        m = j.get("meta") or {}
        out.append({
            "id": j["id"], "filename": j.get("filename"), "created_at": j.get("created_at"),
            "genel_skor": a.get("genel_skor"), "degerlendirilen": a.get("degerlendirilen"),
            "model": (m.get("model") or ""), "diller": m.get("diller") or [],
            "duration": m.get("duration"),
            "version": j.get("version") or 1,
            "pdf": (REPORTS / f"{j['id']}.pdf").exists(),
            "tex": (REPORTS / f"{j['id']}.tex").exists(),
        })
    return out


@app.get("/api/records/{job_id}")
def record(job_id: str):
    return job_status(job_id)


@app.delete("/api/records/{job_id}")
def delete_record(job_id: str):
    c = db()
    c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    c.commit()
    c.close()
    for p in UPLOADS.glob(f"{job_id}.*"):
        try:
            p.unlink()
        except OSError:
            pass
    for p in (REPORTS / f"{job_id}.pdf", REPORTS / f"{job_id}.tex", REPORTS / f"{job_id}.hata.txt"):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
    return {"deleted": job_id}


@app.get("/")
def root():
    return {"service": "web-speech-project backend", "health": "/health", "time": time.time()}


@app.get("/api/records/{job_id}/report.html")
def report_html(job_id: str):
    from fastapi.responses import HTMLResponse
    from report import render_html
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "job yok")
    if (job.get("status") or "") != "done":
        raise HTTPException(409, "rapor için iş bitmeli (şu an: %s)" % job.get("status"))
    return HTMLResponse(render_html(dict(job)))


@app.get("/api/records/{job_id}/report.tex")
def report_tex_src(job_id: str):
    from fastapi.responses import Response
    from report_tex import render_tex
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "job yok")
    return Response(content=render_tex(dict(job)), media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="denetim-{job_id}.tex"'})

@app.get("/api/records/{job_id}/report.pdf")
def report_pdf(job_id: str):
    from fastapi.responses import Response
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "job yok")
    if (job.get("status") or "") != "done":
        raise HTTPException(409, "rapor için iş bitmeli (şu an: %s)" % job.get("status"))
    archived = REPORTS / f"{job_id}.pdf"
    if archived.exists():
        return Response(content=archived.read_bytes(), media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="denetim-{job_id}.pdf"'})
    try:
        from report_tex import render_tex, compile_pdf
        pdf = compile_pdf(render_tex(dict(job)))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, "PDF üretilemedi: " + str(e)[:300])
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="denetim-{job_id}.pdf"'})
