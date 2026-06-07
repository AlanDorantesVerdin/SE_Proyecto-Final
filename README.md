# 🎬 CineFísico — Sistema Experto de Atención y Ventas con Agentes Inteligentes

Sistema experto moderno basado en **agentes inteligentes** para una tienda de
películas en **formato físico** (estilo *Blockbuster* moderno): renta, compra,
consulta de catálogo y soporte. Combina un **motor de reglas** (sistema experto
clásico) con **IA moderna** (Gemini) y ofrece **explicabilidad** del
razonamiento en cada paso.

> Proyecto académico — *Sistemas Expertos*.

---

## 🧭 Estado del proyecto

| Componente | Estado |
|---|---|
| **Agente 1 — Atención al Cliente** | ✅ Funcional (intención + entidades + respuesta) |
| **Canal WhatsApp (Twilio)** | ✅ Flujo completo de 3 agentes por mensajes (requiere Twilio + ngrok) |
| **Motor de inferencia + reglas** | ✅ Forward chaining con explicabilidad |
| **Agente 2 — Generador de Pedido** | ✅ Valida, infiere descuentos/stock y arma el pedido |
| **Persistencia en BD** | ✅ Guarda pedidos y rentas, descuenta stock, registra reabastecimiento |
| **Agente 3 — Supervisor / Explicador** | ✅ Resume, explica inferencias y pide validación |
| **Orquestador conversacional** | ✅ Une 1→2→3 con confirmación (SÍ/NO) por WhatsApp |
| **Interfaz web (Streamlit)** | ✅ Chat con panel de inferencias en vivo |
| Interfaz de usuario (UI) | ⏳ Pendiente |

---

## 🏗️ Arquitectura

```
                 ┌──────────────────────────────┐
   Cliente  ───► │  Agente 1: Atención al Cliente│
  (WhatsApp/CLI) │  • Detecta intención          │
                 │  • Extrae entidades (películas)│
                 │  • Consulta catálogo (BD)      │
                 │  • Responde automáticamente    │
                 └───────────────┬──────────────┘
                                 │ Interpretation (handoff)
                                 ▼
                 ┌──────────────────────────────┐
                 │  Agente 2: Generador de Pedido │
                 │  • Valida e infiere (IF/THEN)  │
                 │  • Genera y guarda el pedido   │
                 └───────────────┬──────────────┘
                                 ▼
                 ┌──────────────────────────────┐
                 │  Agente 3: Supervisor/Explica  │
                 │  • Resume y explica decisiones │
                 └──────────────────────────────┘
```

### Enfoque híbrido (sistema experto + IA)
- **Reglas** (`core/knowledge_base.py`): clasificación determinista y
  explicable de la intención. **Siempre funciona**, incluso sin Internet.
- **LLM** (`core/llm_client.py`, Gemini): mejora la comprensión del lenguaje
  natural. Si no hay API key o falla, el sistema **degrada elegantemente** a
  solo-reglas sin caerse.

---

## 🧰 Stack tecnológico

- **Python 3.11+** (probado en 3.13)
- **SQLite** — base de datos local
- **Google Gemini** (`google-genai`) — IA / LLM
- **FastAPI + Uvicorn** — webhook para WhatsApp (etapa posterior)
- **python-dotenv** — manejo de credenciales

---

## 📁 Estructura del proyecto

```
SE_Proyecto-Final/
├── agents/
│   ├── agent_customer.py     # Agente 1 — Atención al Cliente
│   ├── agent_orders.py       # Agente 2 — Generador de Pedido
│   └── agent_supervisor.py   # Agente 3 — Supervisor / Explicador
├── core/
│   ├── schemas.py            # Objetos de dominio (Intent, Interpretation…)
│   ├── knowledge_base.py     # Reglas/keywords (base de conocimiento)
│   ├── llm_client.py         # Cliente Gemini con degradación elegante
│   ├── inference_engine.py   # Motor de inferencia (forward chaining)
│   ├── business_rules.py     # Reglas de negocio (descuentos, stock)
│   └── console.py            # Utilidad de salida UTF-8 (Windows)
├── database/
│   ├── db.py                 # Conexión y esquema SQLite
│   ├── repository.py         # Consultas (catálogo, clientes)
│   └── seed.py               # Datos de ejemplo (catálogo de películas)
├── channels/
│   └── whatsapp_twilio.py    # Adaptador del canal WhatsApp (Twilio)
├── api/
│   └── main.py               # Servidor FastAPI + webhook de WhatsApp
├── ui/
│   └── app.py                # Interfaz web de chat (Streamlit)
├── orchestrator.py           # Orquestador conversacional de los 3 agentes
├── run_cli.py                # Prueba local del Agente 1 por terminal
├── run_inference.py          # Demo del motor de inferencia (IF/THEN)
├── run_orders.py             # Demo del Agente 2 (generación de pedido)
├── run_persist.py            # Demo de persistencia (guardar pedido en BD)
├── run_supervisor.py         # Demo del flujo completo 1 -> 2 -> 3
├── run_orchestrator.py       # Demo conversacional (pedido + confirmación)
├── requirements.txt
├── .env.example              # Plantilla de variables (copiar a .env)
├── WHATSAPP_SETUP.md         # Guía para conectar WhatsApp
└── .gitignore
```

---

## 🚀 Instalación y ejecución

### 1. Clonar y crear entorno virtual
```powershell
git clone https://github.com/AlanDorantesVerdin/SE_Proyecto-Final.git
cd SE_Proyecto-Final
py -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
```

### 2. Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```powershell
copy .env.example .env          # Windows  (cp en Linux/macOS)
```
Edita `.env` y coloca tu **API key de Gemini** (gratis en
<https://aistudio.google.com/apikey>):
```env
GEMINI_API_KEY=tu_api_key_aqui
LLM_MODEL=gemini-2.5-flash
```
> 💡 Sin API key el sistema **igual funciona** en modo solo-reglas.

### 4. Poblar la base de datos
```powershell
python -m database.seed
```

### 5. Probar el Agente 1 y el motor de inferencia
```powershell
python run_cli.py --demo        # conversación de ejemplo del Agente 1
python run_cli.py               # modo interactivo (chateas tú)
python run_inference.py         # razonamiento del sistema experto (IF/THEN)
python run_orders.py            # genera un pedido con descuentos (Agente 2)
python run_persist.py           # guarda un pedido en la base de datos
python run_supervisor.py        # flujo completo de los 3 agentes (1 -> 2 -> 3)
python run_orchestrator.py      # conversación con confirmación de pedido
```

### 6. Interfaz web de chat (recomendada para la demo)
```powershell
streamlit run ui/app.py
```
Abre en el navegador (http://localhost:8501) un chat con el sistema y un panel
lateral que muestra las **inferencias en vivo**, el catálogo y el cliente simulado.

### 7. Conectar a WhatsApp (opcional)
Levanta el servidor del webhook:
```powershell
uvicorn api.main:app --reload --port 8000
```
Abre <http://127.0.0.1:8000/> para ver el estado. Para enlazarlo con WhatsApp
(cuenta de Twilio + ngrok) sigue la guía paso a paso:
**[WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)**.

---

## 🔐 Seguridad

- El archivo **`.env` NUNCA se sube a GitHub** (está en `.gitignore`).
- Si expones una API key por accidente, **regenérala** de inmediato.
- La base de datos (`*.db`) tampoco se versiona: se regenera con `seed.py`.

---

## 📝 Licencia

Proyecto con fines educativos.
