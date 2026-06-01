"""
Utilidad para forzar salida UTF-8 en la consola.

En Windows la consola suele usar la codificación cp1252, que no puede mostrar
emojis ni caracteres como '✓'. Llamar a `enable_utf8()` al inicio de cada
punto de entrada evita errores de codificación.
"""
import sys


def enable_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
