# backend — Python + FastAPI, modeller içeride, kayıtlı işlem

## Çalıştır (v1)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# faster-whisper ilk çalışta modeli indirir (~75MB tiny, ~145MB base)
uvicorn app:app --port 8001 --reload
# sağlık: http://localhost:8001/health
```

Web istemci: `http://localhost:8000` (ayrı terminalde `python3 -m http.server 8000`).

Not: `ffmpeg` yoksa ilk sürüm sadece `.wav` kabul eder. mp3/m4a için:
`brew install ffmpeg`
