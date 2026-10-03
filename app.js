/* Servis bazlı istemci — tüm işlem backend'de, tarayıcı sadece UI.
   Backend: http://localhost:8001 (backend/app.py) */
const $ = (id) => document.getElementById(id);
const fileInput = $("fileInput"), dropZone = $("dropZone"), player = $("player");
const fileInfo = $("fileInfo"), statusEl = $("status"), progress = $("progress");
const transcriptEl = $("transcript"), scoresEl = $("scores"), recordsEl = $("records");
const backendDot = $("backendDot"), auditEl = $("audit"), auditScore = $("auditScore");

const API = "http://localhost:8001";
const bUrl = () => API;
let backendInfo = null;
let lastResult = null; // { text, chunks, scores, acoustic, meta, id }

function setStatus(s, p = null) {
  statusEl.textContent = s;
  const low = (s || "").toLocaleLowerCase("tr");
  const st = /hata|başarısız|ulaşılamadı|bulunamadı|yok|kaldırıldı/.test(low) ? "error"
    : /bitti|hazır|kaydedildi/.test(low) ? "done" : "working";
  statusEl.dataset.state = st;
  if (p !== null) progress.value = p;
}

// --- dosya ---
fileInput.addEventListener("change", (e) => setFile(e.target.files[0]));
dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") fileInput.click(); });
["dragover", "dragenter"].forEach((ev) => dropZone.addEventListener(ev, (e) => {
  e.preventDefault();
  dropZone.classList.add("over");
}));
["dragleave", "drop"].forEach((ev) => dropZone.addEventListener(ev, (e) => {
  e.preventDefault();
  dropZone.classList.remove("over");
}));
dropZone.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files?.[0];
  if (f) { fileInput.files = e.dataTransfer.files; setFile(f); }
});
function setFile(f) {
  if (!f) return;
  player.src = URL.createObjectURL(f);
  fileInfo.textContent = `${(f.size / 1024 / 1024).toFixed(2)} MB · ${f.type || "ses dosyası"}`;
  const chip = $("fileChip");
  chip.style.display = "flex";
  chip.innerHTML = `<span class="tchip lang">SES</span><span class="grow">${f.name}</span>`;
  const rm = document.createElement("button");
  rm.className = "btn danger";
  rm.style.padding = "2px 10px";
  rm.textContent = "Kaldır";
  rm.onclick = (e) => {
    e.stopPropagation();
    fileInput.value = "";
    player.removeAttribute("src");
    player.load();
    chip.style.display = "none";
    fileInfo.textContent = "";
    setStatus("Dosya kaldırıldı.");
    setStep(1);
  };
  chip.appendChild(rm);
  setStatus("Dosya hazır. Servise gönder.");
  setStep(2);
}

// --- servis sağlık ---
async function checkBackend() {
  const dot = $("backendDot"), txt = $("backendTxt");
  try {
    const j = await (await fetch(bUrl() + "/health")).json();
    backendInfo = j;
    dot.classList.remove("down");
    dot.classList.add("ok");
    txt.textContent = "servis çevrimiçi";
    dot.title = "Kabul edilen formatlar: " + (j.allowed || []).join(", ");
    if (!j.ok) setStatus("Servis hata.");
    return j.ok;
  } catch {
    backendInfo = null;
    dot.classList.remove("ok");
    dot.classList.add("down");
    txt.textContent = "servis çevrimdışı";
    dot.title = "Backend'e ulaşılamadı — backend/:8001'i başlat";
    setStatus("Servise ulaşılamadı — backend/:8001'i başlat (backend/README).");
    return false;
  }
}

// --- skor render ---
function renderScores(scores, acoustic, meta) {
  if (!scores) {
    scoresEl.innerHTML = `<div class="empty"><b>—</b><p>${t("empty_transcript")}</p></div>`;
    return;
  }
  scoresEl.innerHTML = "";
  const s = scores.sentiment ?? 0;
  const hero = document.createElement("div");
  hero.className = `audit-hero ${s > 0.2 ? "ok" : s < -0.2 ? "bad" : "warn"}`;
  hero.innerHTML = `<div class="audit-score">${s}<small>sentiment</small></div>` +
    `<div><span class="tchip">${scores.kelimeSayisi ?? 0} kelime</span></div>`;
  scoresEl.appendChild(hero);
  for (const [k, v] of Object.entries(scores.duyguDagilimi || {})) {
    const div = document.createElement("div");
    div.className = `crit ${v >= 50 ? "ok" : v > 0 ? "warn" : "na"}`;
    div.innerHTML = `<div class="crit-head"><b>${k}</b><span class="muted small">${v}</span></div>` +
      `<div class="bar"><i style="width:${v}%"></i></div>`;
    scoresEl.appendChild(div);
  }
  const a = document.createElement("div");
  a.className = "evidence";
  a.innerHTML = `<span>akustik + meta</span>enerji=${acoustic.ortalamaEnerji} · tepe=${acoustic.tepe} · sessizlik=${acoustic.sessizlikOrani} · süre=${Number(meta.duration || 0).toFixed(1)}sn · segment=${(lastResult?.chunks || []).length} · ${meta.model || ""}`;
  scoresEl.appendChild(a);
}

// --- denetim render (T1-T13 kriter havuzu) ---
const AUDIT_TITLES = {
  t1: "T1 — Kurum + araştırma adı + kayıt bildirimi",
  t2: "T2 — Kişinin kendisiyle görüşme",
  t3: "T3 — 1 saat bile olsa gelir getirici iş",
  t4: "T4 — Ücretsiz aile işçisi",
  t5: "T5 — Başında bulunulmayan iş + neden",
  t6: "T6 — Küçük/düzensiz işler",
  t7: "T7 — Ek iş",
  t8: "T8 — Fiili çalışma saati",
  t9: "T9 — Daha fazla çalışma isteği",
  t10: "T10 — Son 4 haftada iş arama",
  t11: "T11 — Çalışmak istememe / aramama nedeni",
  t12: "T12 — Yönlendirme kontrolü",
  t13: "T13 — Saygılı / nazik tutum",
};
const DURUM_TXT = { evet: "EVET", hayir: "HAYIR", belirsiz: "DEĞERLENDİRİLEMEDİ" };
function auditItem(title, sub, extra = "") {
  const st = sub.durum || "belirsiz";
  const div = document.createElement("div");
  div.className = `crit ${st === "evet" ? "ok" : st === "hayir" ? "bad" : "na"}`;
  div.innerHTML =
    `<div class="crit-head"><span class="st ${st}">${DURUM_TXT[st] || "—"}</span><b>${title}</b><span class="muted small">${sub.puan ?? 0} puan</span>${extra ? `<span class="warn-badge">${extra}</span>` : ""}</div>` +
    `<div class="bar"><i style="width:${sub.puan ?? 0}%"></i></div>` +
    `<div class="evidence"><span>kanıt</span>${sub.kanit || "—"}</div>` +
    (sub.yorum ? `<div class="evidence"><span>yorum (anlamlandırma)</span>${sub.yorum}</div>` : "");
  return div;
}
function renderAudit(analysis) {
  const frame = $("pdfFrame");
  frame.style.display = "none";
  if (!analysis || analysis.hata) {
    auditScore.textContent = "—";
    auditEl.innerHTML =
      `<div class="audit-empty"><div class="audit-empty-ico">◉</div>` +
      (analysis?.hata
        ? `<b>—</b><p>${analysis.hata}</p>`
        : `<b>—</b><p>${t("empty_transcript")}</p>`) +
      `</div>`;
    return;
  }
  const skor = analysis.genel_skor ?? 0;
  const cls = skor >= 70 ? "ok" : skor >= 40 ? "warn" : "bad";
  auditScore.textContent = `genel skor: ${skor} (${analysis.degerlendirilen ?? "—"} kriter)`;
  auditEl.innerHTML = "";
  const hero = document.createElement("div");
  hero.className = `audit-hero ${cls}`;
  hero.innerHTML = `<div class="audit-score">${skor}<small>/ 100</small></div><div>${analysis.ozet || ""}</div>`;
  auditEl.appendChild(hero);
  const t1 = analysis.t1 || {};
  const t1head = document.createElement("div");
  t1head.innerHTML = `<b>T1 — sonuç: ${(t1.sonuc || "belirsiz").toUpperCase()}</b>`;
  auditEl.appendChild(t1head);
  const subs = [["Kurum adı", t1.kurum || {}],
    [`Araştırma adı (${(t1.arastirma || {}).tespit_edilen_ad || "tespit edilemedi"})`, t1.arastirma || {}],
    ["Kayıt bildirimi", t1.kayit_bildirimi || {}]];
  subs.forEach(([label, s]) => auditEl.appendChild(auditItem(label, s)));
  ["t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10", "t11", "t12", "t13"].forEach((k) => {
    let extra = "";
    if (k === "t2" && analysis[k]?.proxy) extra = "PROXY GÖRÜŞME";
    if (k === "t12" && analysis[k]?.yonlendirme_var) extra = "YÖNLENDİRME";
    auditEl.appendChild(auditItem(AUDIT_TITLES[k], analysis[k] || { durum: "belirsiz" }, extra));
  });
  const oz = document.createElement("div");
  oz.className = "muted small";
  oz.textContent = (analysis.ozet || "") + ` · model: ${analysis.model || ""}` +
    (analysis.referans_hafta ? ` · referans hafta: ${analysis.referans_hafta}` : "") +
    (analysis.transkript_karakter != null
      ? ` · transkript: ${analysis.transkript_karakter} karakter (${analysis.transkript_tamami ? "tamamı" : "kesildi"})`
      : "");
  auditEl.appendChild(oz);
}
$("btnPdfView").onclick = () => {
  if (!lastResult?.id) return setStatus("Önce bir sonuç aç.");
  const f = $("pdfFrame");
  f.src = `${bUrl()}/api/records/${lastResult.id}/report.html`;
  f.style.display = "block";
  f.scrollIntoView({ behavior: "smooth", block: "nearest" });
};
$("btnPdfDown").onclick = () => {
  if (!lastResult?.id) return setStatus("Önce bir sonuç aç.");
  const a = document.createElement("a");
  a.href = `${bUrl()}/api/records/${lastResult.id}/report.pdf`;
  a.download = `denetim-${lastResult.id}.pdf`;
  a.click();
};

// --- çalıştır ---
$("btnRun").onclick = async () => {
  $("backBar").style.display = "none";
  const f = fileInput.files?.[0];
  if (!f) return setStatus("Önce dosya seç.");
  if (!(await checkBackend())) return;
  const ext = (f.name.split(".").pop() || "").toLowerCase();
  if (backendInfo?.wavOnly && ext !== "wav")
    return setStatus(`.${ext} yüklenemez (serviste ffmpeg yok, sadece .wav). Örn: samples/test-tr-16k.wav`);
  const model = $("asrModel").value;
  setStatus(model === "medium" ? "Yükleniyor… (medium ilk seferde modeli bekleyebilir)" : "Yükleniyor…", 5);
  const fd = new FormData();
  fd.append("file", f, f.name);
  fd.append("model", model);
  fd.append("language", $("lang").value);
  fd.append("refhafta", ($("refhafta")?.value || "").trim());
  let r;
  try {
    r = await fetch(bUrl() + "/api/jobs", { method: "POST", body: fd });
  } catch {
    return setStatus("Yükleme başarısız: servise erişilemiyor.");
  }
  if (!r.ok) return setStatus("Hata: " + (await r.text()).slice(0, 300));
  const { id } = await r.json();
  for (let i = 0; i < 180; i++) {
    await new Promise((res) => setTimeout(res, 2000));
    let jr;
    try {
      jr = await (await fetch(`${bUrl()}/api/jobs/${id}`)).json();
    } catch { continue; }
    const p = Math.round(jr.progress || 0);
    setStatus(`${jr.stage || jr.status} %${p} (faster-whisper-${model})`, p);
    if (jr.status === "done") {
      const pick = (v) => (typeof v === "string" ? JSON.parse(v) : v);
      lastResult = {
        id, text: jr.transcript, chunks: pick(jr.segments) || [],
        scores: pick(jr.scores), acoustic: pick(jr.acoustic), meta: pick(jr.meta),
        analysis: pick(jr.analysis),
      };
      transcriptEl.textContent = lastResult.text;
      renderScores(lastResult.scores, lastResult.acoustic, lastResult.meta);
      renderAudit(lastResult.analysis);
      renderParts(lastResult.meta);
      setStep(4);
      setStatus(`Bitti: ${lastResult.chunks.length} segment, ${lastResult.scores.kelimeSayisi} kelime. Kayıt serviste.`, 100);
      loadRecords();
      return;
    }
    if (jr.status === "error") return setStatus("Servis hata: " + (jr.error || "bilinmiyor"));
  }
  setStatus("Zaman aşımı — job id ile sonra bak: " + id);
};

// --- örneklem parça görünümü (rapor öncesi skor alanı) ---
function renderParts(meta) {
  const el = $("parts");
  const parts = meta?.parcalar || [];
  const diller = meta?.diller || [];
  if (!parts.length) { el.textContent = ""; return; }
  el.innerHTML = parts.map((p) => `<div>• <b>${p.etiket}</b> [${p.baslangic_sn} sn · ${p.dil}] ${p.metin || ""}</div>`).join("");
}
$("btnTex").onclick = () => {
  if (!lastResult?.id) return setStatus("Önce bir sonuç aç.");
  const a = document.createElement("a");
  a.href = `${bUrl()}/api/records/${lastResult.id}/report.tex`;
  a.download = `denetim-${lastResult.id}.tex`;
  a.click();
};
// --- export ---
function download(name, text, type = "text/plain") {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
}
const fmt = (s) => {
  s = Math.max(0, s || 0);
  const h = String(Math.floor(s / 3600)).padStart(2, "0"), m = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const sec = String(Math.floor(s % 60)).padStart(2, "0"), ms = String(Math.floor((s % 1) * 1000)).padStart(3, "0");
  return { srt: `${h}:${m}:${sec},${ms}`, vtt: `${h}:${m}:${sec}.${ms}` };
};
$("btnSrt").onclick = () => {
  if (!lastResult) return setStatus("İndirilecek sonuç yok.");
  download("transkript.srt", lastResult.chunks.map((c, i) => `${i + 1}\n${fmt(c.start).srt} --> ${fmt(c.end).srt}\n${(c.text || "").trim()}`).join("\n\n"));
};
$("btnVtt").onclick = () => {
  if (!lastResult) return setStatus("İndirilecek sonuç yok.");
  download("transkript.vtt", "WEBVTT\n\n" + lastResult.chunks.map((c) => `${fmt(c.start).vtt} --> ${fmt(c.end).vtt}\n${(c.text || "").trim()}`).join("\n\n"));
};
$("btnJson").onclick = () => {
  if (!lastResult) return setStatus("İndirilecek sonuç yok.");
  download("analiz.json", JSON.stringify(lastResult, null, 2), "application/json");
};

// --- görünümler: çalışma / raporlar ---
function showView(which) {
  $("workView").style.display = which === "work" ? "" : "none";
  $("reportsView").style.display = which === "reports" ? "" : "none";
  $("navWork").classList.toggle("active", which === "work");
  $("navReports").classList.toggle("active", which === "reports");
  if (which === "reports") loadReportsTable();
}
$("navWork").onclick = () => { $("backBar").style.display = "none"; showView("work"); };
$("navReports").onclick = () => showView("reports");
$("btnReportsReload").onclick = () => loadReportsTable();
$("btnBackReports").onclick = () => showView("reports");
async function loadReportsTable() {
  const tb = $("reportsBody");
  try {
    const arr = await (await fetch(bUrl() + "/api/reports")).json();
    tb.innerHTML = "";
    if (!arr.length) { tb.innerHTML = `<tr><td colspan="7">arşivde rapor yok</td></tr>`; return; }
    arr.forEach((r) => {
      const tr = document.createElement("tr");
      const skor = r.genel_skor ?? "—";
      tr.innerHTML = `<td>${r.filename}</td><td><span class="tchip lang">v${r.version || 1}</span></td><td>${(r.created_at || "").slice(0, 16).replace("T", " ")}</td>` +
        `<td><b>${skor}</b></td><td>${r.model || ""}</td><td>${(r.diller || []).join(", ")}</td><td>${r.duration ?? "—"} sn</td>`;
      const td = document.createElement("td");
      td.className = "row-btns";
      const mk = (label, fn, cls = "btn ghost") => {
        const b = document.createElement("button");
        b.className = cls; b.textContent = label; b.type = "button"; b.onclick = (e) => { e.stopPropagation(); fn(); };
        td.appendChild(b);
      };
      mk(t("op_inspect"), async () => {
        const full = await (await fetch(`${bUrl()}/api/records/${r.id}`)).json();
        const pick = (v) => (typeof v === "string" ? JSON.parse(v) : v);
        lastResult = { id: r.id, text: full.transcript, chunks: pick(full.segments) || [],
          scores: pick(full.scores), acoustic: pick(full.acoustic), meta: pick(full.meta),
          analysis: pick(full.analysis) };
        transcriptEl.textContent = lastResult.text;
        renderScores(lastResult.scores, lastResult.acoustic, lastResult.meta);
        renderAudit(lastResult.analysis);
        renderParts(lastResult.meta);
        setStep(4);
        $("backBar").style.display = "";
        showView("work");
      }, "btn");
      mk("HTML", () => window.open(`${bUrl()}/api/records/${r.id}/report.html`, "_blank"));
      if (r.pdf) mk("PDF", () => window.open(`${bUrl()}/api/records/${r.id}/report.pdf`, "_blank"));
      if (r.tex) mk("TEX", () => window.open(`${bUrl()}/api/records/${r.id}/report.tex`, "_blank"));
      mk(t("op_rescore"), async () => {
        const model = prompt("model? (tiny/base/small/medium)", "medium") || "medium";
        const res = await fetch(`${bUrl()}/api/records/${r.id}/rescore?model=${encodeURIComponent(model)}`, { method: "POST" });
        if (!res.ok) { alert("Hata: " + (await res.text()).slice(0, 200)); return; }
        const nj = await res.json();
        alert(`v${nj.version} işlemi başladı (id: ${nj.id}). Tablodan izleyebilirsin.`);
        loadReportsTable();
      });
      mk(t("op_del"), async () => {
        if (!confirm(`${r.filename} silinsin mi?`)) return;
        await fetch(`${bUrl()}/api/records/${r.id}`, { method: "DELETE" });
        loadReportsTable(); loadRecords();
      }, "btn danger");
      tr.appendChild(td);
      tb.appendChild(tr);
    });
  } catch {
    tb.innerHTML = `<tr><td colspan="7">servise ulaşılamadı</td></tr>`;
  }
}

// --- kayıtlar (servis) ---
async function loadRecords() {
  try {
    const arr = await (await fetch(bUrl() + "/api/records?limit=20")).json();
    recordsEl.innerHTML = "";
    arr.forEach((j) => {
      const li = document.createElement("li");
      const st = j.status === "error" ? `HATA: ${(j.error || "").slice(0, 60)}` : (j.transcript || "").slice(0, 60);
      li.innerHTML = `<span>${(j.created_at || "").slice(0, 19)} — ${j.filename} — ${j.status} — ${st}…</span> `;
      const del = document.createElement("button");
      del.textContent = t("op_del");
      del.className = "btn danger";
      del.style.padding = "2px 8px";
      del.onclick = async (e) => {
        e.stopPropagation();
        await fetch(`${bUrl()}/api/records/${j.id}`, { method: "DELETE" });
        loadRecords();
      };
      li.appendChild(del);
      li.style.cursor = "pointer";
      li.onclick = async () => {
        const full = await (await fetch(`${bUrl()}/api/records/${j.id}`)).json();
        if (full.status !== "done") return setStatus(`Job ${j.id}: ${full.status}`);
        const pick = (v) => (typeof v === "string" ? JSON.parse(v) : v);
        lastResult = {
          id: j.id, text: full.transcript, chunks: pick(full.segments) || [],
          scores: pick(full.scores), acoustic: pick(full.acoustic), meta: pick(full.meta),
          analysis: pick(full.analysis),
        };
        transcriptEl.textContent = lastResult.text;
        renderScores(lastResult.scores, lastResult.acoustic, lastResult.meta);
        renderAudit(lastResult.analysis);
        renderParts(lastResult.meta);
        setStep(4);
      };
      recordsEl.appendChild(li);
    });
    if (!arr.length) recordsEl.innerHTML = "<li>kayıt yok</li>";
  } catch {
    recordsEl.innerHTML = "<li>servise ulaşılamadı</li>";
  }
}
$("btnRecords").onclick = loadRecords;

// --- adımlar ---
function setStep(n) {
  [1, 2, 3].forEach((i) => {
    const el = $(`step${i}`);
    if (!el) return;
    el.classList.toggle("done", i < n || (n > 3));
    el.classList.toggle("active", i === Math.min(n, 3) && n <= 3);
  });
  if (n > 3) [1, 2, 3].forEach((i) => { $(`step${i}`)?.classList.add("done"); $(`step${i}`)?.classList.remove("active"); });
}

// --- internet durumu (sürekli bildirim) ---
const netDot = $("netDot"), netBanner = $("netBanner");
function setNet(ok) {
  netDot.textContent = ok ? "● çevrimiçi" : "● çevrimdışı";
  netDot.classList.toggle("off", !ok);
  netBanner.classList.toggle("show", !ok);
}
async function netCheck() {
  if (!navigator.onLine) return setNet(false);
  try {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), 8000);
    await fetch("https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.5.1/package.json",
      { mode: "no-cors", cache: "no-store", signal: c.signal });
    clearTimeout(t);
    setNet(true);
  } catch {
    setNet(false);
  }
}
window.addEventListener("online", netCheck);
window.addEventListener("offline", () => setNet(false));
setInterval(netCheck, 20000);

renderAudit(null);
setStep(1);
netCheck();
checkBackend();

// --- dil seçici ---
(function initLocale() {
  const bar = $("localeBar");
  LOCALES.forEach((loc) => {
    const b = document.createElement("button");
    b.className = "btn ghost";
    b.style.padding = "2px 9px";
    b.dataset.loc = loc;
    b.textContent = LOCALE_NAMES[loc];
    b.onclick = () => setLocale(loc);
    bar.appendChild(b);
  });
  window.__onLocale = () => {
    if (lastResult) {
      renderScores(lastResult.scores, lastResult.acoustic, lastResult.meta);
      renderAudit(lastResult.analysis);
      renderParts(lastResult.meta);
    } else {
      transcriptEl.textContent = t("empty_transcript");
      renderScores(null);
      renderAudit(null);
    }
    if ($("reportsView").style.display !== "none") loadReportsTable();
    setStatus(t("st_ready"), 0);
  };
  setLocale(LOCALE);
})();
