// FRAMMENTO: lettura allegati testuali (txt, csv, word, excel).
// Da inserire DOPO lo step "Seleziona allegati utili" e PRIMA di "Componi prompt di estrazione".
// Richiede le modifiche agli step "Inizializza chiavi di giro", "Seleziona allegati utili", "Componi prompt di estrazione" e "Componi email di esito" (vedi NOTE).

// @alias Espone allegati testuali al ForEach
CodeJs({ outputKey: "attachTextItems" }, () => {
  let a = [];
  try { a = JSON.parse("" + (stepData.attachTextJson || "[]")); } catch (e) { a = []; }
  return Array.isArray(a) ? a : [];
});

// @alias Leggi allegati testuali (txt, csv, word, excel)
// @foreach maxIterations=10
for (const item of attachTextItems) {
  // @alias Azzera e imposta allegato testuale
  CodeJs({ outputKey: "attInit" }, () => {
    const T = v => ('' + (v == null ? "" : v));
    let it = stepData.__loopItem || $input.__loopItem || {};
    if (typeof it === "string") { try { it = JSON.parse(it); } catch (e) { it = {}; } }
    if (!it || typeof it !== "object") it = {};
    delete stepData.lastFileContent; delete stepData.lastFilePath; delete stepData.lastFileBytes;
    delete stepData.lastWordText; delete stepData.lastWordParagraphs; delete stepData.lastXlsxRows;
    stepData.attPath = T(it.path).trim();
    stepData.attName = T(it.name).trim();
    stepData.attKind = T(it.kind).trim();
    return { nome: stepData.attName, tipo: stepData.attKind };
  });

  if ($.attKind == "txt") {
    // @alias Leggi txt/csv
    // @continueOnFail
    FileRead({
      path: "{attPath}",
      maxBytes: 1048576
    });
  } else {
    if ($.attKind == "word") {
      // @alias Estrai testo Word
      // @continueOnFail
      WordExtract({
        filePath: "{attPath}"
      });
    } else {
      if ($.attKind == "xls") {
        // @alias Estrai righe Excel
        // @continueOnFail
        XlsxExtract({
          filePath: "{attPath}",
          sheet: "*",
          hasHeaders: true,
          headerRow: 1
        });
      }
    }
  }

  // @alias Accoda testo allegato
  CodeJs({ outputKey: "attAccoda" }, () => {
    const T = v => ('' + (v == null ? "" : v));
    const kind = T(stepData.attKind), name = T(stepData.attName);
    let text = "";
    if (kind === "txt") {
      text = T(stepData.lastFileContent);
    } else if (kind === "word") {
      text = T(stepData.lastWordText);
    } else if (kind === "xls") {
      let rows = stepData.lastXlsxRows;
      if (typeof rows === "string") { try { rows = JSON.parse(rows); } catch (e) { rows = null; } }
      if (rows && !Array.isArray(rows)) rows = rows.rows || rows.data || null;
      if (Array.isArray(rows) && rows.length) {
        const lines = []; let sheet = null;
        rows.slice(0, 400).forEach(r => {
          const o = (r && typeof r === "object") ? r : { v: r };
          const sh = T(o.__sheet);
          const keys = Object.keys(o).filter(k => k !== "__sheet");
          if (sheet === null || sh !== sheet) { sheet = sh; lines.push("[Foglio " + (sh || "1") + "]"); lines.push(keys.join(" | ")); }
          lines.push(keys.map(k => T(o[k]).replace(/\s+/g, " ").trim()).join(" | "));
        });
        text = lines.join("\n");
        if (rows.length > 400) text += "\n[... altre " + (rows.length - 400) + " righe non incluse]";
      }
    }
    text = text.replace(/\r\n?/g, "\n").trim();
    let lista = [];
    try { lista = JSON.parse(T(stepData.allegatiTestoJson) || "[]"); } catch (e) { lista = []; }
    if (!Array.isArray(lista)) lista = [];
    if (text) {
      if (text.length > 20000) text = text.substring(0, 20000) + "\n[... testo troncato]";
      lista.push({ name: name, kind: kind, text: text });
    } else {
      stepData.attachNonLetti = (T(stepData.attachNonLetti) ? T(stepData.attachNonLetti) + ", " : "") + name + " (nessun testo estratto)";
    }
    stepData.allegatiTestoJson = JSON.stringify(lista);
    return { nome: name, caratteri: text.length };
  });
}

// @alias Componi testo degli allegati
CodeJs({ outputKey: "allegatiTestoOut" }, () => {
  const T = v => ('' + (v == null ? "" : v));
  let lista = [];
  try { lista = JSON.parse(T(stepData.allegatiTestoJson) || "[]"); } catch (e) { lista = []; }
  if (!Array.isArray(lista)) lista = [];
  let tot = 0; const blocchi = [], nomi = [];
  lista.forEach(x => {
    let t = T(x && x.text);
    if (tot + t.length > 60000) t = t.substring(0, Math.max(0, 60000 - tot)) + "\n[... testo troncato]";
    if (!t) return;
    tot += t.length;
    blocchi.push("### ALLEGATO: " + T(x.name) + " (" + T(x.kind) + ")\n" + t);
    nomi.push(T(x.name));
  });
  stepData.allegatiTesto = blocchi.join("\n\n");
  stepData.attachTextCount = '' + nomi.length;
  if (nomi.length) stepData.attachNames = (T(stepData.attachNames) ? T(stepData.attachNames) + ", " : "") + nomi.join(", ");
  return { letti: nomi.length, caratteri: stepData.allegatiTesto.length };
});
