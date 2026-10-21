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
    stepData.attReadKind = stepData.attKind === "eml" ? "txt" : stepData.attKind;
    return { nome: stepData.attName, tipo: stepData.attKind };
  });

  if ($.attReadKind == "txt") {
    // @alias Leggi txt/csv/eml
    // @continueOnFail
    FileRead({
      path: "{attPath}",
      maxBytes: 1048576
    });
  } else {
    if ($.attReadKind == "word") {
      // @alias Estrai testo Word
      // @continueOnFail
      WordExtract({
        filePath: "{attPath}"
      });
    } else {
      if ($.attReadKind == "xls") {
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
    const emlToText = (raw) => {
      const ASCII = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~";
      const cache = {};
      const chr = n => {
        if (n >= 32 && n < 127) return ASCII.charAt(n - 32);
        if (n === 10) return "\n"; if (n === 13) return "\r"; if (n === 9) return "\t";
        if (cache[n] !== undefined) return cache[n];
        let r = "";
        try { r = JSON.parse('"\\u' + ('0000' + n.toString(16)).slice(-4) + '"'); } catch (e) { r = " "; }
        cache[n] = r; return r;
      };
      const cp = n => n < 65536 ? chr(n) : chr(55296 + ((n - 65536) >> 10)) + chr(56320 + ((n - 65536) & 1023));
      const decBytes = (b, cs) => {
        let o = "";
        if (/utf-?8/i.test(cs || "utf-8")) {
          for (let i = 0; i < b.length; i++) {
            const c = b[i];
            if (c < 128) o += chr(c);
            else if (c >= 194 && c < 224 && i + 1 < b.length) { o += chr(((c & 31) << 6) | (b[i + 1] & 63)); i += 1; }
            else if (c >= 224 && c < 240 && i + 2 < b.length) { o += chr(((c & 15) << 12) | ((b[i + 1] & 63) << 6) | (b[i + 2] & 63)); i += 2; }
            else if (c >= 240 && c < 248 && i + 3 < b.length) { o += cp(((c & 7) << 18) | ((b[i + 1] & 63) << 12) | ((b[i + 2] & 63) << 6) | (b[i + 3] & 63)); i += 3; }
            else o += chr(c);
          }
        } else { for (let i = 0; i < b.length; i++) o += chr(b[i]); }
        return o;
      };
      const T64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
      const b64 = s => { const out = []; let acc = 0, bits = 0; for (let i = 0; i < s.length; i++) { const v = T64.indexOf(s.charAt(i)); if (v < 0) continue; acc = (acc << 6) | v; bits += 6; if (bits >= 8) { bits -= 8; out.push((acc >> bits) & 255); acc = acc & ((1 << bits) - 1); } } return out; };
      const qp = s => { const out = []; const t = s.replace(/=\r?\n/g, ""); for (let i = 0; i < t.length; i++) { const c = t.charAt(i); if (c === "=" && /^[0-9A-Fa-f]{2}$/.test(t.substr(i + 1, 2))) { out.push(+("0x" + t.substr(i + 1, 2))); i += 2; } else out.push(t.charCodeAt(i) & 255); } return out; };
      const words = v => T(v).replace(/=\?([^?]+)\?([bBqQ])\?([^?]*)\?=/g, (m0, cs, enc, txt) => { try { return /b/i.test(enc) ? decBytes(b64(txt), cs) : decBytes(qp(txt.replace(/_/g, " ")), cs); } catch (e) { return m0; } });
      const htmlToText = h => T(h).replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<br\s*\/?>/gi, "\n").replace(/<\/(p|div|tr|li|h\d)>/gi, "\n").replace(/<[^>]+>/g, "").replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&").replace(/&lt;/gi, "<").replace(/&gt;/gi, ">").replace(/&quot;/gi, '"').replace(/&#39;/g, "'");
      const parse = txt => {
        const sep = txt.search(/\r?\n\r?\n/);
        const head = sep >= 0 ? txt.substring(0, sep) : txt;
        const body = sep >= 0 ? txt.substring(sep).replace(/^\r?\n\r?\n/, "") : "";
        const hdr = {};
        head.replace(/\r?\n[ \t]+/g, " ").split(/\r?\n/).forEach(l => { const k = l.indexOf(":"); if (k > 0) { const n = l.substring(0, k).toLowerCase().trim(); if (hdr[n] === undefined) hdr[n] = l.substring(k + 1).trim(); } });
        return { hdr: hdr, body: body };
      };
      const textOf = (txt, depth) => {
        if (depth > 6) return { plain: "", html: "" };
        const p = parse(txt);
        const cth = T(p.hdr["content-type"]), ct = cth.toLowerCase(), cte = T(p.hdr["content-transfer-encoding"]).toLowerCase();
        const bm = /boundary="?([^";\r\n]+)"?/i.exec(cth);
        if (ct.indexOf("multipart/") === 0 && bm) {
          let plain = "", html = "";
          p.body.split("--" + bm[1]).slice(1).forEach(part => {
            if (/^--/.test(part)) return;
            const r = textOf(part.replace(/^\r?\n/, ""), depth + 1);
            if (r.plain) plain += (plain ? "\n" : "") + r.plain;
            if (r.html) html += (html ? "\n" : "") + r.html;
          });
          return { plain: plain, html: html };
        }
        if (ct.indexOf("message/rfc822") === 0) {
          const inn = parse(p.body), rr = textOf(p.body, depth + 1), ih = inn.hdr;
          const hb = [ih["from"] ? "Da: " + words(ih["from"]) : "", ih["to"] ? "A: " + words(ih["to"]) : "", ih["date"] ? "Data: " + ih["date"] : "", ih["subject"] ? "Oggetto: " + words(ih["subject"]) : ""].filter(x => x).join("\n");
          return { plain: rr.plain ? (hb ? "--- messaggio inoltrato ---\n" + hb + "\n\n" : "") + rr.plain : "", html: rr.html };
        }
        if (ct === "" || ct.indexOf("text/") === 0) {
          const cs = (/charset="?([^";\s]+)"?/i.exec(cth) || [])[1];
          let s = p.body;
          if (cte.indexOf("base64") >= 0) s = decBytes(b64(s), cs); else if (cte.indexOf("quoted-printable") >= 0) s = decBytes(qp(s), cs);
          return ct.indexOf("text/html") === 0 ? { plain: "", html: s } : { plain: s, html: "" };
        }
        return { plain: "", html: "" };
      };
      if (!/^(received|from|return-path|mime-version|content-type|date|subject|to|message-id|delivered-to|x-[a-z0-9-]+):/im.test(raw.substring(0, 3000))) return "";
      const m = parse(raw), r = textOf(raw, 0);
      let body = (r.plain || htmlToText(r.html)).replace(/\r\n?/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
      if (!body) return "";
      const h = m.hdr, out = ["[Messaggio inoltrato come allegato]"];
      if (h["from"]) out.push("Da: " + words(h["from"]));
      if (h["to"]) out.push("A: " + words(h["to"]));
      if (h["date"]) out.push("Data: " + h["date"]);
      if (h["subject"]) out.push("Oggetto: " + words(h["subject"]));
      out.push(""); out.push(body);
      return out.join("\n");
    };
    const kind = T(stepData.attKind), name = T(stepData.attName);
    let text = "";
    if (kind === "txt") {
      text = T(stepData.lastFileContent);
    } else if (kind === "eml") {
      text = emlToText(T(stepData.lastFileContent));
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
