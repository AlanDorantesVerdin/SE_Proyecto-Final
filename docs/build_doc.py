"""
Convierte el registro (Markdown) a un HTML imprimible para exportar a PDF.

Uso:
    pip install markdown
    python docs/build_doc.py

Luego abre `docs/GG_registro_Proy.html` en el navegador y elige
**Imprimir → Guardar como PDF** (tamaño A4). El archivo resultante es el
entregable `GG_registro_Proy.pdf`. Inserta las capturas donde aparece
`[ CAPTURA … ]` y pega el enlace del video antes de exportar.
"""
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
MD_FILE = HERE / "GG_registro_Proy.md"
OUT_FILE = HERE / "GG_registro_Proy.html"

CSS = """
@page { size: A4; margin: 2cm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; line-height: 1.55;
       color: #1f1b16; max-width: 820px; margin: 0 auto; padding: 0 16px; }
h1 { font-size: 22pt; color: #b9802b; border-bottom: 3px solid #b9802b;
     padding-bottom: 8px; margin-top: 0; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; font-size: 27pt; border: none; margin-top: 48px; }
h2 { font-size: 15pt; color: #2a2118; margin-top: 1.6em;
     border-bottom: 1px solid #e6dccb; padding-bottom: 4px; }
h3 { font-size: 12.5pt; color: #4a3d2c; }
a { color: #34648f; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
th, td { border: 1px solid #d8cdb8; padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: #f4ece0; }
code { font-family: 'Consolas', monospace; background: #f3f0ea; padding: 1px 4px;
       border-radius: 3px; font-size: 9.5pt; }
pre { background: #f6f4ef; border: 1px solid #e6dccb; padding: 12px 14px;
      border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid #e6dccb; margin: 1.5em 0; }
hr:first-of-type { page-break-after: always; border: none; margin: 0; }
blockquote { border-left: 3px solid #b9802b; margin: 1em 0; padding: 4px 14px;
             color: #5a4d3a; background: #faf6ef; }
@media print { body { max-width: none; } a { color: #1f1b16; text-decoration: none; } }
"""


def main() -> None:
    text = MD_FILE.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    html = ("<!DOCTYPE html>\n<html lang='es'>\n<head>\n<meta charset='utf-8'>\n"
            "<title>REBOBINA — Registro del proyecto</title>\n<style>"
            + CSS + "</style>\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generado: {OUT_FILE}")


if __name__ == "__main__":
    main()
