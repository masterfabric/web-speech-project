/* Basit i18n — TR · EN · FR · CN · JP · AR (varsayılan EN). Statik arayüz metinleri. */
const LOCALES = ["en", "tr", "fr", "zh", "ja", "ar"];
const LOCALE_NAMES = { en: "EN", tr: "TR", fr: "FR", zh: "CN", ja: "JP", ar: "AR" };
const I18N = {
en: { kurumsal: "<b>Turkish Statistical Institute</b> · Household Labour Force Survey (HIA) · Alo124 Quality Audit",
kurumsal_right: "Educational prototype", brand_sub: "Audio → text + emotion score (service-based)",
nav_work: "Workspace", nav_reports: "Reports", net_off: "No internet — model downloads and service calls may fail. Saved results remain viewable.",
hero_h1: "Drop your audio, the service returns transcript + scores",
hero_p: "Processing runs on the Python backend (faster-whisper); records live in SQLite on the service. The browser is just a client.",
step1: "Upload", step2: "Send to service", step3: "Score + download", step1d: "wav · mp3 · m4a · aac + more", step2d: "faster-whisper tiny→medium, language detect", step3d: "T1–T13 audit, LaTeX PDF + archive",
c1: "1. Audio file", drop_t: "Drop the file here", drop_s: "or click to browse · wav · mp3 · m4a · aac · ogg · flac · mp4",
c2: "2. Run on service", f_model: "Model (service)", f_lang: "Language", f_ref: "Reference week (e.g. 3–9 June)", ref_ph: "optional", btn_run: "Send to Service + Score",
c3: "3. Transcript", c4: "4. Scores", c5: "5. Records (service)", rec_note: "Every job is saved automatically (SQLite).", btn_refresh: "Refresh", back: "← Back to Reports",
c6: "6. Audit — TÜİK compliance (T1–T13)", pdf_view: "Preview PDF", pdf_down: "Download PDF",
rep_h: "Archived Reports (LaTeX)", rep_note: "Every finished job is stored server-side as .tex + .pdf.",
th_file: "File", th_ver: "Ver.", th_date: "Date", th_score: "Score", th_model: "Model", th_lang: "Language", th_dur: "Duration", th_ops: "Actions",
foot_a: "built for TÜİK training by", foot_b: "", foot_sub: "HIA Alo124 quality-audit prototype ·", tech_label: "Stack:",
op_inspect: "Inspect", op_rescore: "Re-score", op_del: "Delete",
st_ready: "Ready.", empty_transcript: "No output yet. Select a file and send it to the service.",
kvkk: "Educational use only — no personal data under KVKK is processed. Samples come from public Common Voice data.", doc_title: "web-speech-project — Service-Based Audio Analysis" },
tr: { kurumsal: "<b>Türkiye İstatistik Kurumu</b> · Hanehalkı İşgücü Araştırması (HİA) · Alo124 Kalite Denetim",
kurumsal_right: "Eğitim amaçlı prototip", brand_sub: "Ses → metin + duygu skoru (servis bazlı)",
nav_work: "Çalışma", nav_reports: "Raporlar", net_off: "İnternet bağlantısı yok — model indirme ve servis çağrıları çalışmayabilir. Kayıtlı sonuçlar görüntülenebilir.",
hero_h1: "Ses dosyanı bırak, servis transkript + skor üretsin",
hero_p: "İşlem Python backend'de (faster-whisper), kayıtlar servis tarafında SQLite'da. Tarayıcı sadece istemci.",
step1: "Yükle", step2: "Servise gönder", step3: "Skorla + indir", step1d: "wav · mp3 · m4a · aac ve dahası", step2d: "faster-whisper tiny→medium, dil tespiti", step3d: "T1–T13 denetim, LaTeX PDF + arşiv",
c1: "1. Ses dosyası", drop_t: "Dosyayı buraya bırak", drop_s: "veya seçmek için tıkla · wav · mp3 · m4a · aac · ogg · flac · mp4",
c2: "2. Servisle çalıştır", f_model: "Model (servis)", f_lang: "Dil", f_ref: "Referans hafta (örn: 3-9 Haziran)", ref_ph: "boş bırakılabilir", btn_run: "Servise Gönder + Skorla",
c3: "3. Transkript", c4: "4. Skorlar", c5: "5. Kayıtlar (servis)", rec_note: "Her işlem otomatik kaydedilir (SQLite).", btn_refresh: "Yenile", back: "← Raporlara Dön",
c6: "6. Denetim — TÜİK uyum (T1-T13)", pdf_view: "PDF Önizle", pdf_down: "PDF İndir",
rep_h: "Arşivlenmiş Raporlar (LaTeX)", rep_note: "Her biten işin .tex + .pdf hali servis tarafında saklanır.",
th_file: "Dosya", th_ver: "Ver.", th_date: "Tarih", th_score: "Skor", th_model: "Model", th_lang: "Dil", th_dur: "Süre", th_ops: "İşlemler",
foot_a: "TÜİK eğitimi kapsamında", foot_b: "tarafından geliştirilmiştir", foot_sub: "HİA Alo124 Kalite Denetim prototipi ·", tech_label: "Altyapı:",
op_inspect: "İncele", op_rescore: "Tekrar Skorla", op_del: "Sil",
st_ready: "Hazır.", empty_transcript: "Henüz çıktı yok. Dosya seçip servise gönder.",
kvkk: "Yalnızca eğitim amaçlıdır — KVKK kapsamına giren hiçbir kişisel veri işlenmez. Örnekler herkese açık Common Voice verilerindendir.", doc_title: "web-speech-project — Servis Bazlı Ses Analizi" },
fr: { kurumsal: "<b>Institut statistique de Turquie</b> · Enquête population active (HİA) · Audit qualité Alo124",
kurumsal_right: "Prototype pédagogique", brand_sub: "Audio → texte + score d'émotion (via service)",
nav_work: "Espace de travail", nav_reports: "Rapports", net_off: "Pas d'internet — téléchargements et appels au service indisponibles. Les résultats enregistrés restent visibles.",
hero_h1: "Déposez votre audio, le service renvoie transcription + scores",
hero_p: "Traitement sur le backend Python (faster-whisper), enregistrements en SQLite côté service. Le navigateur n'est qu'un client.",
step1: "Téléverser", step2: "Envoyer au service", step3: "Noter + télécharger", step1d: "wav · mp3 · m4a · aac et plus", step2d: "faster-whisper tiny→medium, détection de langue", step3d: "audit T1–T13, PDF LaTeX + archive",
c1: "1. Fichier audio", drop_t: "Déposez le fichier ici", drop_s: "ou cliquez pour parcourir · wav · mp3 · m4a · aac · ogg · flac · mp4",
c2: "2. Exécuter sur le service", f_model: "Modèle (service)", f_lang: "Langue", f_ref: "Semaine de référence (ex. 3-9 juin)", ref_ph: "facultatif", btn_run: "Envoyer au service + noter",
c3: "3. Transcription", c4: "4. Scores", c5: "5. Enregistrements (service)", rec_note: "Chaque tâche est enregistrée automatiquement (SQLite).", btn_refresh: "Actualiser", back: "← Retour aux rapports",
c6: "6. Audit — conformité TÜİK (T1-T13)", pdf_view: "Aperçu PDF", pdf_down: "Télécharger le PDF",
rep_h: "Rapports archivés (LaTeX)", rep_note: "Chaque tâche terminée est stockée côté service en .tex + .pdf.",
th_file: "Fichier", th_ver: "Ver.", th_date: "Date", th_score: "Score", th_model: "Modèle", th_lang: "Langue", th_dur: "Durée", th_ops: "Actions",
foot_a: "développé pour la formation TÜİK par", foot_b: "", foot_sub: "Prototype d'audit qualité HİA Alo124 ·", tech_label: "Pile :",
op_inspect: "Inspecter", op_rescore: "Noter à nouveau", op_del: "Supprimer",
st_ready: "Prêt.", empty_transcript: "Aucune sortie. Sélectionnez un fichier et envoyez-le au service.",
kvkk: "Usage pédagogique uniquement — aucune donnée personnelle (KVKK) n'est traitée. Échantillons issus des données publiques Common Voice.", doc_title: "web-speech-project — Analyse audio via service" },
zh: { kurumsal: "<b>土耳其统计局</b>·家庭劳动力调查（HİA）·Alo124质量审核",
kurumsal_right: "教学原型", brand_sub: "音频 → 文本 + 情感评分（服务端）",
nav_work: "工作区", nav_reports: "报告", net_off: "无网络 — 模型下载和服务调用可能失败。已保存结果仍可查看。",
hero_h1: "放入音频，服务返回转录 + 评分",
hero_p: "处理在 Python 后端运行（faster-whisper），记录保存在服务端 SQLite。浏览器只是客户端。",
step1: "上传", step2: "发送到服务", step3: "评分 + 下载", step1d: "wav · mp3 · m4a · aac 等", step2d: "faster-whisper tiny→medium，语言检测", step3d: "T1–T13 审核，LaTeX PDF + 归档",
c1: "1. 音频文件", drop_t: "将文件拖到此处", drop_s: "或点击选择 · wav · mp3 · m4a · aac · ogg · flac · mp4",
c2: "2. 在服务端运行", f_model: "模型（服务端）", f_lang: "语言", f_ref: "参考周（例如6月3–9日）", ref_ph: "可选", btn_run: "发送到服务 + 评分",
c3: "3. 转录", c4: "4. 评分", c5: "5. 记录（服务端）", rec_note: "每个任务自动保存（SQLite）。", btn_refresh: "刷新", back: "← 返回报告",
c6: "6. 审核 — TÜİK 合规（T1-T13）", pdf_view: "预览 PDF", pdf_down: "下载 PDF",
rep_h: "已归档报告（LaTeX）", rep_note: "每个已完成任务以 .tex + .pdf 保存在服务端。",
th_file: "文件", th_ver: "版本", th_date: "日期", th_score: "评分", th_model: "模型", th_lang: "语言", th_dur: "时长", th_ops: "操作",
foot_a: "由", foot_b: "为 TÜİK 培训开发", foot_sub: "HİA Alo124 质量审核原型 ·", tech_label: "技术栈：",
op_inspect: "查看", op_rescore: "重新评分", op_del: "删除",
st_ready: "就绪。", empty_transcript: "暂无输出。选择文件并发送到服务。",
kvkk: "仅限教学 — 不处理 KVKK 范围内的个人数据。样本来自公开的 Common Voice 数据。", doc_title: "web-speech-project — 基于服务的音频分析" },
ja: { kurumsal: "<b>トルコ統計局</b>·家計労働力調査（HİA）·Alo124品質監査",
kurumsal_right: "教育用プロトタイプ", brand_sub: "音声 → テキスト + 感情スコア（サービス型）",
nav_work: "ワークスペース", nav_reports: "レポート", net_off: "オフライン — モデル取得やサービス呼び出しができません。保存済み結果は閲覧できます。",
hero_h1: "音声を置けば、転写 + スコアを返します",
hero_p: "処理はPythonバックエンド（faster-whisper）で実行、記録はサービスのSQLiteに保存。ブラウザはクライアントです。",
step1: "アップロード", step2: "サービスへ送信", step3: "採点 + ダウンロード", step1d: "wav · mp3 · m4a · aac 他", step2d: "faster-whisper tiny→medium、言語検出", step3d: "T1–T13 監査、LaTeX PDF + 保存",
c1: "1. 音声ファイル", drop_t: "ここにファイルをドロップ", drop_s: "またはクリックして選択 · wav · mp3 · m4a · aac · ogg · flac · mp4",
c2: "2. サービスで実行", f_model: "モデル（サービス）", f_lang: "言語", f_ref: "参照週（例：6月3〜9日）", ref_ph: "任意", btn_run: "サービスへ送信 + 採点",
c3: "3. 転写", c4: "4. スコア", c5: "5. 記録（サービス）", rec_note: "各ジョブは自動保存されます（SQLite）。", btn_refresh: "更新", back: "← レポートに戻る",
c6: "6. 監査 — TÜİK準拠（T1-T13）", pdf_view: "PDFプレビュー", pdf_down: "PDFダウンロード",
rep_h: "アーカイブ済みレポート（LaTeX）", rep_note: "完了ジョブは.tex + .pdfでサーバー側に保存されます。",
th_file: "ファイル", th_ver: "Ver.", th_date: "日時", th_score: "スコア", th_model: "モデル", th_lang: "言語", th_dur: "長さ", th_ops: "操作",
foot_a: "", foot_b: "がTÜİK研修用に開発", foot_sub: "HİA Alo124品質監査プロトタイプ ·", tech_label: "スタック：",
op_inspect: "開く", op_rescore: "再採点", op_del: "削除",
st_ready: "準備完了。", empty_transcript: "出力はまだありません。ファイルを選んでサービスへ送信してください。",
kvkk: "教育目的のみ — KVKKの個人データは扱いません。サンプルは公開Common Voiceデータです。", doc_title: "web-speech-project — サービス型音声分析" },
ar: { kurumsal: "<b>المعهد الإحصائي التركي</b>· مسح القوى العاملة الأسرية (HİA) · تدقيق جودة Alo124",
kurumsal_right: "نموذج تعليمي", brand_sub: "تحويل الصوت إلى نص + درجة المشاعر (عبر الخدمة)",
nav_work: "مساحة العمل", nav_reports: "التقارير", net_off: "لا يوجد اتصال — قد تتعذر التنزيلات ونداءات الخدمة. النتائج المحفوظة قابلة للعرض.",
hero_h1: "أفلت ملف الصوت، وستعيد الخدمة النص + الدرجات",
hero_p: "تتم المعالجة على الواجهة الخلفية Python ‏(faster-whisper)، وتُحفظ السجلات في SQLite على الخدمة. المتصفح مجرد عميل.",
step1: "رفع", step2: "إرسال إلى الخدمة", step3: "تقييم + تنزيل", step1d: "wav · mp3 · m4a · aac وغيرها", step2d: "faster-whisper tiny←medium، كشف اللغة", step3d: "تدقيق T1-T13‏، PDF ‏LaTeX + أرشيف",
c1: "1. ملف الصوت", drop_t: "أفلت الملف هنا", drop_s: "أو انقر للاختيار · wav · mp3 · m4a · aac · ogg · flac · mp4",
c2: "2. التشغيل على الخدمة", f_model: "النموذج (الخدمة)", f_lang: "اللغة", f_ref: "الأسبوع المرجعي (مثال: 3-9 يونيو)", ref_ph: "اختياري", btn_run: "إرسال إلى الخدمة + تقييم",
c3: "3. النص", c4: "4. الدرجات", c5: "5. السجلات (الخدمة)", rec_note: "يُحفظ كل مهمة تلقائيًا (SQLite).", btn_refresh: "تحديث", back: "→ العودة إلى التقارير",
c6: "6. التدقيق — الامتثال لـTÜİK ‏(T1-T13)", pdf_view: "معاينة PDF", pdf_down: "تنزيل PDF",
rep_h: "التقارير المؤرشفة (LaTeX)", rep_note: "تُحفظ كل مهمة مكتملة على الخدمة بصيغة .tex + .pdf.",
th_file: "الملف", th_ver: "الإصدار", th_date: "التاريخ", th_score: "الدرجة", th_model: "النموذج", th_lang: "اللغة", th_dur: "المدة", th_ops: "إجراءات",
foot_a: "طُوِّر لتدريب TÜİK بواسطة", foot_b: "", foot_sub: "نموذج تدقيق جودة HİA Alo124 ·", tech_label: "البنية:",
op_inspect: "فحص", op_rescore: "إعادة التقييم", op_del: "حذف",
st_ready: "جاهز.", empty_transcript: "لا مخرجات بعد. اختر ملفًا وأرسله إلى الخدمة.",
kvkk: "للتعليم فقط — لا تُعالج أي بيانات شخصية ضمن KVKK. العينات من بيانات Common Voice العامة.", doc_title: "web-speech-project — تحليل صوتي عبر الخدمة" },
};

let LOCALE = localStorage.getItem("wsp-locale") || "en";
if (!I18N[LOCALE]) LOCALE = "en";
function t(k) { return (I18N[LOCALE] && I18N[LOCALE][k]) || I18N.en[k] || k; }

function setLocale(loc) {
  if (!I18N[loc]) return;
  LOCALE = loc;
  localStorage.setItem("wsp-locale", loc);
  document.documentElement.lang = loc === "zh" ? "zh-CN" : loc;
  document.documentElement.dir = loc === "ar" ? "rtl" : "ltr";
  document.title = t("doc_title");
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll("#localeBar button").forEach((b) =>
    b.classList.toggle("active", b.dataset.loc === loc));
  if (window.__onLocale) window.__onLocale();
}
