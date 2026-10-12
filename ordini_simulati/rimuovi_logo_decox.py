"""Rimuove l'intestazione immagine (logo, dati societari, QR) dagli ordini cartacei.
Uso: python rimuovi_logo_decox.py <cartella_input> <cartella_output>"""
import re, sys, pathlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, DictionaryObject

src, dst = map(pathlib.Path, sys.argv[1:3])
dst.mkdir(parents=True, exist_ok=True)
for f in sorted(src.glob("*.pdf")):
    r = PdfReader(f); w = PdfWriter()
    for p in r.pages:
        data = p.get_contents().get_data()
        new, n = re.subn(rb"q\r[\d. ]+ cm\r/Im\d+ Do\s*\rQ\r", b"", data)
        assert n == 1, (f.name, n)
        cs = ContentStream(None, r); cs.set_data(new)
        p[NameObject("/Contents")] = w._add_object(cs) if False else cs
        p["/Resources"][NameObject("/XObject")] = DictionaryObject()
        w.add_page(p)
    w.add_metadata({"/Title": "Ordine " + f.stem.split("-", 1)[-1]})
    name = re.search(r"(2026-1CEOF-\d+)", f.name).group(1) + ".pdf"
    with open(dst / name, "wb") as o: w.write(o)
    print("ok", name)
