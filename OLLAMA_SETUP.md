# 🦙 Guía: IA local con Ollama (sin límites de cuota)

Ollama ejecuta el modelo de lenguaje **en tu propia computadora**: sin cuotas,
sin internet y sin API keys. Es la opción recomendada para este proyecto y
permite que el bot responda **cualquier** mensaje con IA.

---

## Paso 1 — Instalar Ollama

Descarga e instala desde **<https://ollama.com/download>** (Windows, macOS o Linux).
Al terminar, Ollama queda corriendo en segundo plano (servidor en
`http://localhost:11434`).

Verifica en una terminal:
```powershell
ollama --version
```

## Paso 2 — Descargar un modelo

```powershell
ollama pull llama3.2
```
Pesa ~2 GB. Alternativas:
- `qwen2.5:3b` — mejor en español
- `llama3.2:1b` — más ligero y rápido (para equipos modestos)

Lista los modelos descargados:
```powershell
ollama list
```

## Paso 3 — Configurar el proyecto

En tu archivo `.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```
(Si descargaste otro modelo, escribe su nombre exacto en `OLLAMA_MODEL`.)

## Paso 4 — Probar

```powershell
streamlit run ui/app.py
```
En la barra lateral debe aparecer: **IA: 🟢 ollama (llama3.2)**.
Ahora el asistente responde con IA a recomendaciones, preguntas de cine,
precios, formatos… sin límites de uso.

---

## ¿Prefieres Gemini (nube)?

Cambia en `.env`:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_api_key
```

## Solución de problemas

| Síntoma | Solución |
|---|---|
| La UI dice "solo reglas" | Asegúrate de que Ollama esté corriendo (abre la app de Ollama o ejecuta `ollama serve`) |
| Respuestas lentas | Usa un modelo más pequeño: `ollama pull llama3.2:1b` |
| A veces falla el JSON | Usa un modelo de 3B o más (estructuran mejor que los de 1B) |
| `OLLAMA_MODEL` no coincide | El nombre debe ser idéntico al de `ollama list` |
