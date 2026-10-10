#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
valida_flusso.py — validatore deterministico per flussi DSL "Modalita Sviluppatore"
di ThinkAI WorkForce Studio (skill workforce-flow-builder).

Uso:
    python valida_flusso.py <flusso.js> [--strict]
    python valida_flusso.py --self-test

Controlli (le sigle Rn rimandano alle Regole d'oro di SKILL.md):
  [ERRORE] literal non quotato in condizione DSL: if ($.x == ordine)                  (R7)
  [ERRORE] idempotencyKey fissa, senza alcun {placeholder}                             (R10)
  [ERRORE] FileWrite con contenuto/percorso binario (PDF, base64, immagini)            (R12)
  [ERRORE] MailDisposition annidato o ripetuto                                         (R14)
  [ERRORE] GestionaleSend con credentialName contenente un {placeholder}              (R19)
  [AVVISO] String()/Number() nel codice CodeJs: non esistono nel sandbox              (R18)
  [AVVISO] timeoutSeconds oltre il tetto di piattaforma (300 s)                        (R19)
  [AVVISO] FileWrite su percorso assoluto: scrive nella sandbox interna               (R12)
  [AVVISO] dato cliente cablato in uno step (percorso, email, P.IVA): va in M00        (R20)
  [AVVISO] nome-blocco DSL non confermato                     (dsl/nomi-blocchi.md)
  [AVVISO] responseFormat "report"                                                     (R1)
  [AVVISO] throw new Error dentro un ciclo for                                         (R2)
  [AVVISO] idempotencyKey su una lettura o su FileMove overwrite:true                  (R10)
  [AVVISO] assegnazione di una chiave last* del motore dentro CodeJs                   (R11)
  [AVVISO] placeholder {chiave} dentro il codice JS di CodeJs (non viene sostituito)   (R-08)
  [AVVISO] FileWrite con path = intera variabile "{x}"                       (erp/gotchas §1)
  [AVVISO] JsonToFile con path assoluto Windows                              (erp/gotchas §3)
  [AVVISO] GestionaleSend endpoint "lookup" (deprecato v1.5.0)                         (R-11)
  [AVVISO] @continueOnFail su un costrutto (if/for/switch) invece che su uno step       (B)
  [AVVISO] ForEach su lastEmails insieme a MailDisposition                             (R14)
  [AVVISO] placeholder {TBD:...} non risolto                                           (B8)
  [AVVISO] intestazione mancante
  [NOTA]   placeholder di chiavi mai scritte nel file (verifica R8)
  [NOTA]   ciclo il cui primo step non e' un cleanup                                   (R5)
  [NOTA]   FileMove senza allowedRoot con target dinamico
  [NOTA]   commenti non funzionali da rimuovere prima della consegna                  (R17)

Le righe dentro il corpo di CodeJs/CodePython (arrow function `=> { ... }`) sono JS reale:
i controlli DSL le saltano, ma vengono usate per R11/R-08 e per raccogliere le chiavi scritte.

Exit code: 1 se ci sono ERRORI (con --strict anche se ci sono AVVISI), 0 altrimenti.
"""
import re
import sys

CONFERMATI = {
    "CodeJs", "CodePython",
    "AiAnalysis", "RagSearch", "ClassifyText", "ExtractStructured", "RagEmbed", "GenerateReport",
    "SecureChatQuery", "FileDelete", "ExcelOnlineAppend", "ExcelOnlineRead", "FileList",
    "SqlInsert", "JsonToFile", "JsonFromFile", "JsonParse", "FileMove", "Query", "FileRead",
    "GoogleSheetsAppend", "GoogleSheetsRead", "SqlUpdate", "FileWrite",
    "GoogleDriveDownload", "GoogleDriveList", "GoogleDriveUpload", "OcrImage", "PdfExtract",
    "SharePointDownload", "SharePointList", "SharePointUpload", "WordExtract", "XlsxExtract",
    "Aggregate", "Filter", "InboundParse", "Limit", "Merge", "RemoveDuplicates", "RenameKeys",
    "SetFields", "Sort", "SubWorkflow", "Wait", "WebhookRespond",
    "HttpCall", "GestionaleSend",
    "MailRead", "MailDisposition", "TelegramRead",
    "SendEmail", "SendAndWait", "SendSlack", "SendTeams", "SendTelegram", "SendWhatsApp",
    "Markdown", "PublishDashboard",
}
IGNORA = {"Object", "Array", "JSON", "Math", "Number", "String", "Boolean", "Date", "Error",
          "Promise", "RegExp"}
BLOCCHI_LETTURA = {"Query", "FileRead", "FileList", "JsonFromFile", "JsonParse", "PdfExtract",
                   "WordExtract", "XlsxExtract", "OcrImage", "RagSearch", "GoogleSheetsRead",
                   "ExcelOnlineRead", "GoogleDriveList", "SharePointList", "MailRead"}
ENDPOINT_LETTURA = {"test", "clienti", "fornitori", "contatti", "articoli", "documenti",
                    "lookup", "prezzo"}
# chiavi popolate da trigger o motore: non vanno segnalate come "mai scritte"
CHIAVI_SISTEMA = {
    "webhookBody", "webhookContentType", "formData", "formSubmittedAt", "inboundMailId",
    "inboundMailKey", "inboundEmlPath", "lastEmail", "lastEmailAttachments", "lastEventRows",
    "failedAgentId", "failedAgentName", "failedExecutionId", "failedAt", "errorMessage", "now",
}
CHIAVE_MOTORE = re.compile(
    r"\blast(Ai|Gestionale|TargetCross|Query|FileList|FileWritten|FileBytes|Insert|Update|Markdown|"
    r"Extracted|Rag|Emails?|Moved|Chat|MailDisposition|ForEach|SubWorkflow|Wait)\w*")

HEADER = "Modalità Sviluppatore"
BLOCK_CALL = re.compile(r'^\s*([A-Z][A-Za-z0-9]+)\s*\(')
COND = re.compile(r'\$\.[\w.]+\s*(==|!=)\s*([^\s)]+)')
TBD = re.compile(r'\{TBD:[^}]*\}')
THROW = re.compile(r'\bthrow\s+new\s+Error\s*\(')
ARROW_OPEN = re.compile(r'=>\s*\{')
PLACEHOLDER = re.compile(r'\{([A-Za-z_]\w*)(?:[.\[][^}]*)?\}')
FOR_LINE = re.compile(r'^\s*for\s*\(\s*const\s+\w+\s+of\s+([\w.]+)\s*\)')
COSTRUTTO = re.compile(r'^\s*(if|for|switch|try)\b')


def strip_comment(line):
    """Rimuove un commento // ... solo se fuori da una stringa (protegge 'https://')."""
    out, q, i, n = [], None, 0, len(line)
    while i < n:
        c = line[i]
        if q:
            out.append(c)
            if c == q and line[i - 1] != "\\":
                q = None
        elif c in "\"'`":
            q = c
            out.append(c)
        elif c == "/" and i + 1 < n and line[i + 1] == "/":
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def graffe(code):
    """Sequenza di '{' e '}' fuori dalle stringhe."""
    res, q = [], None
    for i, c in enumerate(code):
        if q:
            if c == q and code[i - 1] != "\\":
                q = None
        elif c in "\"'`":
            q = c
        elif c in "{}":
            res.append(c)
    return res


def parentesi(code):
    """Saldo di parentesi tonde fuori dalle stringhe."""
    s, q = 0, None
    for i, c in enumerate(code):
        if q:
            if c == q and code[i - 1] != "\\":
                q = None
        elif c in "\"'`":
            q = c
        elif c == "(":
            s += 1
        elif c == ")":
            s -= 1
    return s


def chiamate(righe):
    """Raggruppa ogni chiamata-blocco DSL nel suo testo completo (fino a chiusura parentesi o '=>')."""
    out, i = [], 0
    while i < len(righe):
        code = strip_comment(righe[i])
        m = BLOCK_CALL.match(code)
        if m and m.group(1) not in IGNORA:
            testo, saldo, j = [], 0, i
            while j < len(righe):
                c = strip_comment(righe[j])
                if "=>" in c:
                    testo.append(c[:c.index("=>")])
                    break
                testo.append(c)
                saldo += parentesi(c)
                if saldo <= 0:
                    break
                j += 1
            out.append((i + 1, m.group(1), " ".join(testo)))
        i += 1
    return out


def analizza(testo):
    righe = testo.splitlines()
    errori, avvisi, note = [], [], []
    blocchi = {}
    scritte, usate = set(), []
    js_depth = 0
    stack = []                       # contenitori DSL aperti: 'for' / 'x'
    attesa_cleanup = None            # riga del for di cui verificare il primo step
    continue_pendente = None
    commenti = 0
    mail_disp = []                   # (riga, profondita')
    for_lastemails = False

    if HEADER not in testo:
        avvisi.append("Intestazione mancante: la prima riga dovrebbe essere "
                      "'// Flusso in codice (Modalità Sviluppatore). Proiezione fedele del grafo.'")

    for i, riga in enumerate(righe, 1):
        s = riga.strip()
        if s.startswith("//"):
            if "@continueOnFail" in s:
                continue_pendente = i
            elif not s.startswith("// @") and HEADER not in s and js_depth == 0:
                commenti += 1
            continue
        code = strip_comment(riga)
        if not code.strip():
            continue

        # ---------------- JS reale dentro CodeJs/CodePython ----------------
        if js_depth > 0:
            for m in re.finditer(r'stepData\.([A-Za-z_]\w*)\s*=(?!=)', code):
                scritte.add(m.group(1))
                if CHIAVE_MOTORE.match(m.group(1)):
                    avvisi.append(f"riga {i}: CodeJs assegna la chiave del motore '{m.group(1)}': "
                                  f"le last* sono output, non sovrascriverle (R11).")
            for m in re.finditer(r'stepData\[\s*["\'](\w+)["\']\s*\]\s*=(?!=)', code):
                scritte.add(m.group(1))
            for m in re.finditer(r'(?:^\s*|[{,]\s*)["\']?([A-Za-z_]\w*)["\']?\s*:(?!:)', code):
                scritte.add(m.group(1))
            for m in re.finditer(r'(?<![\w.$])(String|Number)\s*[.(]', code):
                avvisi.append(f"riga {i}: {m.group(1)}() usato in CodeJs: nel sandbox non esiste, "
                              f"usa '' + v (stringa) o +v (numero) (R18).")
            for m in re.finditer(r'(["\'])[^"\']*?\{([A-Za-z_]\w*)\}[^"\']*?\1', code):
                avvisi.append(f"riga {i}: placeholder '{{{m.group(2)}}}' dentro il codice JS: in CodeJs "
                              f"non viene sostituito, leggi stepData.{m.group(2)} (R-08).")
            js_depth += code.count("{") - code.count("}")
            js_depth = max(js_depth, 0)
            continue

        # ---------------- livello DSL ----------------
        dsl = code[:code.index("=>")] if ARROW_OPEN.search(code) else code

        if continue_pendente is not None:
            if COSTRUTTO.match(dsl):
                avvisi.append(f"riga {continue_pendente}: @continueOnFail sopra un costrutto "
                              f"'{COSTRUTTO.match(dsl).group(1)}': va sopra uno step (blocco).")
            continue_pendente = None

        m = BLOCK_CALL.match(dsl)
        if m and m.group(1) not in IGNORA:
            nome = m.group(1)
            blocchi.setdefault(nome, []).append(i)
            if nome not in CONFERMATI:
                avvisi.append(f"riga {i}: nome-blocco DSL non confermato '{nome}(' "
                              f"-> verifica in references/dsl/nomi-blocchi.md.")
            if nome == "MailDisposition":
                mail_disp.append((i, len(stack)))
            if attesa_cleanup is not None:
                if nome not in ("CodeJs", "SetFields"):
                    note.append(f"riga {attesa_cleanup}: il ciclo non inizia con un cleanup "
                                f"anti-bleed (CodeJs con delete delle chiavi del giro) (R5).")
                attesa_cleanup = None

        fm = FOR_LINE.match(dsl)
        if fm:
            if fm.group(1) == "lastEmails":
                for_lastemails = True
            if fm.group(1) not in ("rilettureQueue",):
                attesa_cleanup = i
        elif attesa_cleanup is not None and COSTRUTTO.match(dsl):
            attesa_cleanup = None

        for mm in COND.finditer(dsl):
            rhs = mm.group(2).strip().rstrip(")")
            if rhs and not (rhs[0] in "\"'" or rhs in ("true", "false", "null")
                            or re.fullmatch(r"-?\d+(\.\d+)?", rhs)):
                errori.append(f"riga {i}: literal non quotato in condizione '{mm.group(0)}' "
                              f"-> usa \"{rhs}\" (R7).")

        for mm in TBD.finditer(dsl):
            avvisi.append(f"riga {i}: placeholder da compilare {mm.group(0)} (B8).")

        if THROW.search(dsl) and "for" in stack:
            avvisi.append(f"riga {i}: throw new Error dentro un ciclo: interrompe l'INTERA run "
                          f"salvo itemErrorSteps configurati; preferisci un Branch (R2).")

        for mm in re.finditer(r'(?:outputKey|outputItemsKey|failedItemsKey)\s*:\s*"(\w+)"', dsl):
            scritte.add(mm.group(1))
        for mm in re.finditer(r'"key"\s*:\s*"(\w+)"', dsl):
            scritte.add(mm.group(1))
        for mm in PLACEHOLDER.finditer(TBD.sub("", dsl)):
            usate.append((i, mm.group(1)))

        for g in graffe(dsl):
            if g == "{":
                stack.append("for" if fm else "x")
                fm = None
            elif stack:
                stack.pop()

        if ARROW_OPEN.search(code):
            dopo = code[code.index("=>"):]
            js_depth += dopo.count("{") - dopo.count("}")

    # ---------------- controlli sulle chiamate complete ----------------
    for riga, nome, t in chiamate(righe):
        if re.search(r'responseFormat\s*:\s*"report"', t):
            avvisi.append(f"riga {riga}: {nome} con responseFormat \"report\": ammesso solo se "
                          f"l'output e' letto da una persona, mai se alimenta logica (R1).")
        ik = re.search(r'idempotencyKey\s*:\s*"([^"]*)"', t)
        if ik:
            if "{" not in ik.group(1):
                errori.append(f"riga {riga}: idempotencyKey fissa '{ik.group(1)}': vale per tutta "
                              f"la vita dell'agente, dal 2o giro lo step non gira piu' (R10).")
            ep = re.search(r'endpoint\s*:\s*"([\w-]+)"', t)
            lettura = nome in BLOCCHI_LETTURA or (nome == "GestionaleSend" and ep
                                                   and ep.group(1) in ENDPOINT_LETTURA)
            if lettura:
                avvisi.append(f"riga {riga}: idempotencyKey su una LETTURA ({nome}"
                              f"{' ' + ep.group(1) if ep else ''}): in replay gli output non "
                              f"vengono ripristinati (R10).")
            if nome == "FileMove" and re.search(r'overwrite\s*:\s*true', t):
                avvisi.append(f"riga {riga}: idempotencyKey su FileMove overwrite:true, gia' "
                              f"idempotente: rischio replay senza spostamento (R10).")
        if nome != "SetFields":
            for lit in re.findall(r'"([^"]*)"', t):
                motivo = None
                if re.search(r'(?<![<{\w])[A-Za-z]:\\', lit):
                    motivo = "percorso"
                elif re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', lit) and "{" not in lit:
                    motivo = "email"
                elif re.search(r'(?<!\d)\d{11}(?!\d)', lit):
                    motivo = "P.IVA"
                if motivo:
                    avvisi.append(f"riga {riga}: {motivo} cablato in {nome} ('{lit[:40]}'): "
                                  f"spostalo in configurazione M00 o in un <SEGNAPOSTO> (R20).")
        cred = re.search(r'credentialName\s*:\s*"([^"]*)"', t)
        if nome == "GestionaleSend" and cred and "{" in cred.group(1):
            errori.append(f"riga {riga}: credentialName '{cred.group(1)}' con placeholder: non viene "
                          f"interpolato, scrivi il nome credenziale letterale (R19).")
        to = re.search(r'timeoutSeconds\s*:\s*(\d+)', t)
        if to and int(to.group(1)) > 300:
            avvisi.append(f"riga {riga}: timeoutSeconds {to.group(1)} oltre il tetto di 300 s (R19).")
        if nome == "FileWrite":
            cont = re.search(r'content\s*:\s*"([^"]*)"', t)
            path = re.search(r'path\s*:\s*"([^"]*)"', t)
            if (cont and re.search(r'(?i)pdf|base64', cont.group(1))) or \
               (path and re.search(r'(?i)\.(pdf|png|jpe?g|docx?|xlsx?)$', path.group(1))):
                errori.append(f"riga {riga}: FileWrite usato per contenuto binario: scrive solo "
                              f"testo, il file non si aprira'. Stampa ERP -> lastGestionalePdfPath (R12).")
            if path and re.match(r'([A-Za-z]:\\|\\\\)', path.group(1)):
                avvisi.append(f"riga {riga}: FileWrite su percorso assoluto '{path.group(1)}': scrive "
                              f"nella sandbox interna, non sul filesystem del cliente (R12).")
            if path and re.fullmatch(r'\{[^}]+\}', path.group(1)):
                avvisi.append(f"riga {riga}: FileWrite con path = intera variabile "
                              f"'{path.group(1)}': non viene sostituita (erp/gotchas §1).")
        if nome == "JsonToFile" and re.search(r'path\s*:\s*"[A-Za-z]:\\', t):
            avvisi.append(f"riga {riga}: JsonToFile rifiuta i path assoluti Windows "
                          f"(erp/gotchas §3): usa CodeJs + FileWrite.")
        if nome == "GestionaleSend" and re.search(r'endpoint\s*:\s*"lookup"', t):
            avvisi.append(f"riga {riga}: endpoint \"lookup\" deprecato in TcRestAPI v1.5.0 (R-11).")
        if nome == "FileMove" and "allowedRoot" not in t and \
                re.search(r'target\s*:\s*"[^"]*\{', t):
            note.append(f"riga {riga}: FileMove con target dinamico senza allowedRoot.")

    # ---------------- controlli globali ----------------
    for r, prof in mail_disp:
        if prof > 0:
            errori.append(f"riga {r}: MailDisposition annidato in un contenitore: deve essere "
                          f"top-level (R14).")
    if len(mail_disp) > 1:
        errori.append(f"MailDisposition presente {len(mail_disp)} volte (righe "
                      f"{', '.join(str(r) for r, _ in mail_disp)}): ne serve UNO solo (R14).")
    if mail_disp and for_lastemails:
        avvisi.append("ForEach su lastEmails insieme a MailDisposition: con MailPolling durevole "
                      "la run riguarda UNA mail, non iterare le mail (R14).")

    viste = set()
    for r, k in usate:
        if k in scritte or k in CHIAVI_SISTEMA or k.startswith("__") or k.startswith("last") \
                or k in viste:
            continue
        viste.add(k)
        note.append(f"riga {r}: placeholder '{{{k}}}' di una chiave mai scritta in questo file: "
                    f"se non arriva dal trigger restera' testo letterale (R8).")

    if commenti:
        note.append(f"{commenti} righe di commento non funzionali: rimuovile prima della consegna "
                    f"(restano solo // @alias, // @continueOnFail, // @foreach) (R17).")
    return errori, avvisi, note, blocchi


def report(errori, avvisi, note, blocchi, strict=False):
    print("=== VALIDAZIONE FLUSSO DSL ===")
    print(f"blocchi DSL trovati: {sum(len(v) for v in blocchi.values())} "
          f"({len(blocchi)} tipi) -> {', '.join(sorted(blocchi)) or '(nessuno)'}")
    for etichetta, lista in (("ERRORE", errori), ("AVVISO", avvisi), ("NOTA", note)):
        for msg in lista:
            print(f"[{etichetta}] {msg}")
    print(f"--- {len(errori)} errori, {len(avvisi)} avvisi, {len(note)} note ---")
    return 1 if errori or (strict and avvisi) else 0


CAMPIONE = '''// Flusso in codice (Modalità Sviluppatore). Proiezione fedele del grafo.
// commento esplicativo da togliere
FileList({ pattern: "*", directory: "f:\\\\x" });
for (const item of lastFileList) {
  AiAnalysis({ prompt: "estrai", responseFormat: "report", attachFilePath: "{__loopItem}" });
  CodeJs({ outputKey: "n" }, () => {
    const x = Number(stepData.q || 0);
    if (x == 5) { return String(x); }
    stepData.lastGestionalePdfPath = "E:\\\\x.pdf";
    stepData.dest = '{cartellaProcessing}' + "\\\\a";
    return x;
  });
  if ($.isOrdine == ordine) {
    Sfornaordine({ x: 1 });
    SendEmail({ to: ["{TBD:dest}"], subject: "Doc {codiceMaiScritto}", body: "{n}" });
    throw new Error("stop");
  }
  Query({ sql: "SELECT 1", idempotencyKey: "q-{n}" });
  SqlInsert({ table: "T", values: {"A":"{n}"}, idempotencyKey: "fissa" });
  FileWrite({ path: "E:\\\\out\\\\{n}.pdf", content: "{lastGestionalePdf}" });
  GestionaleSend({ credentialName: "{cred}", endpoint: "test", timeoutSeconds: 600 });
  SendEmail({ to: ["mario@azienda.it"], subject: "x", body: "P.IVA 01234567890" });
  // @continueOnFail
  if ($.n == "1") {
    MailDisposition({ outcome: "processed" });
  }
}
MailDisposition({ outcome: "review" });
'''


def self_test():
    e, a, n, b = analizza(CAMPIONE)
    def has(lista, txt):
        return any(txt in x for x in lista)
    checks = [
        (has(e, "literal non quotato"), "R7 literal"),
        (has(e, "idempotencyKey fissa"), "R10 chiave fissa"),
        (has(e, "contenuto binario"), "R12 FileWrite binario"),
        (has(e, "annidato"), "R14 MailDisposition annidato"),
        (has(e, "ne serve UNO"), "R14 MailDisposition doppio"),
        (has(a, "Sfornaordine"), "nome non confermato"),
        (not has(a, "'Number("), "Number() in CodeJs non e' un blocco"),
        (has(a, "\"report\""), "R1 report"),
        (has(a, "dentro un ciclo"), "R2 throw nel for"),
        (has(a, "LETTURA (Query"), "R10 lettura"),
        (has(a, "lastGestionalePdfPath"), "R11 last*"),
        (has(a, "{cartellaProcessing}"), "R-08 placeholder in JS"),
        (has(a, "costrutto 'if'"), "continueOnFail su costrutto"),
        (len([x for x in a if "TBD" in x]) == 1, "un solo TBD"),
        (has(n, "{codiceMaiScritto}"), "R8 chiave mai scritta"),
        (not has(n, "'{n}'"), "outputKey conta come scritta"),
        (has(n, "cleanup"), "R5 cleanup"),
        (has(n, "righe di commento"), "R17 commenti"),
        (has(e, "credentialName '{cred}'"), "R19 credenziale"),
        (has(a, "600 oltre"), "R19 timeout"),
        (has(a, "Number() usato in CodeJs"), "R18 Number"),
        (has(a, "String() usato in CodeJs"), "R18 String"),
        (has(a, "percorso assoluto"), "R12 FileWrite assoluto"),
        (has(a, "email cablato"), "R20 email"),
        (has(a, "percorso cablato in FileWrite"), "R20 percorso"),
        (not any("x == 5" in x for x in e), "if JS in CodeJs ignorato"),
    ]
    falliti = [nome for ok, nome in checks if not ok]
    if falliti:
        print("self-test FALLITO:", ", ".join(falliti))
        report(e, a, n, b)
        return 1
    print(f"self-test OK ({len(checks)} controlli)")
    return 0


def main(argv):
    args = [x for x in argv[1:] if not x.startswith("--")]
    if "--self-test" in argv:
        return self_test()
    if len(args) != 1:
        print(__doc__)
        return 2
    with open(args[0], encoding="utf-8") as f:
        testo = f.read()
    return report(*analizza(testo), strict="--strict" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
