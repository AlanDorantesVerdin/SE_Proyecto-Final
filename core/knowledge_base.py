"""
Base de conocimiento del Agente 1 (Atención al Cliente).

Contiene las REGLAS EXPLÍCITAS (palabras clave) que permiten clasificar la
intención del cliente sin depender de un LLM. Esta es la parte de "sistema
experto" basada en reglas: es determinista, editable y explicable.

Para añadir vocabulario nuevo basta con editar estos diccionarios; no se
necesita reentrenar ningún modelo.
"""
from core.schemas import Intent

# Cada intención se asocia a un conjunto de disparadores (palabras o frases).
# La detección busca estos disparadores dentro del mensaje normalizado.
INTENT_KEYWORDS: dict[Intent, list[str]] = {
    Intent.GREETING: [
        "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
        "que tal", "saludos", "hey", "buen dia", "que onda",
    ],
    Intent.GOODBYE: [
        "adios", "hasta luego", "nos vemos", "bye", "chao",
        "eso es todo", "muchas gracias", "gracias por tu ayuda",
    ],
    Intent.RENT: [
        "rentar", "renta", "rento", "alquilar", "alquiler", "prestar",
        "quiero ver", "para el fin de semana", "por unos dias",
    ],
    Intent.BUY: [
        "comprar", "compra", "compro", "adquirir", "quedarme con",
        "me llevo", "llevarme", "quiero comprar",
    ],
    Intent.CHECK_AVAILABILITY: [
        "tienen", "disponible", "disponibilidad", "hay", "stock",
        "existencia", "cuentan con", "queda", "quedan", "tendran",
    ],
    Intent.RETURN: [
        "devolver", "devolucion", "regresar pelicula", "entregar pelicula",
    ],
    Intent.BROWSE: [
        "catalogo", "que peliculas", "recomienda", "recomendacion",
        "novedades", "generos", "lista de peliculas", "que tienen",
    ],
    Intent.SUPPORT: [
        "problema", "ayuda con", "no funciona", "reclamo", "queja",
        "soporte", "factura", "error", "cobro", "me cobraron",
    ],
}

# Intenciones "accionables": tienen prioridad sobre saludo/despedida cuando
# aparecen en el mismo mensaje (ej. "Hola, quiero rentar Matrix" -> RENT).
ACTION_INTENTS: list[Intent] = [
    Intent.RENT,
    Intent.BUY,
    Intent.CHECK_AVAILABILITY,
    Intent.RETURN,
    Intent.BROWSE,
    Intent.SUPPORT,
]

# Números escritos con letra (español) para detectar cantidades.
NUMBER_WORDS: dict[str, int] = {
    "un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
}

# Palabras vacías ignoradas al hacer coincidir títulos del catálogo.
STOPWORDS: set[str] = {
    "the", "el", "la", "los", "las", "de", "del", "y", "un", "una", "a",
}
