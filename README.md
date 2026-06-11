# 🎬 CineFísico — Sistema Experto de Atención y Ventas con Agentes Inteligentes

Sistema experto moderno basado en **agentes inteligentes** para una tienda de
películas en **formato físico** (estilo *Blockbuster* moderno): renta, compra,
consulta de catálogo y soporte. Combina un **motor de reglas** (sistema experto
clásico) con **IA moderna** (Ollama o Gemini) y ofrece **explicabilidad** del
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
| **Pruebas automatizadas** | ✅ 16 pruebas (motor, agentes, persistencia, flujo) |
| **Panel web de administración (REBOBINA)** | ✅ Pedidos por validar, stock, clientes, ingresos, alertas |

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
- **LLM** (`core/llm_client.py`): **Ollama** (local, sin límites) o **Gemini**
  (nube). Mejora la comprensión y responde consultas libres (recomendaciones,
  precios, cine…). Si no está disponible, el sistema **degrada elegantemente**
  a solo-reglas sin caerse.

---

## 🧰 Stack tecnológico

- **Python 3.11+** (probado en 3.13)
- **SQLite** — base de datos local
- **IA / LLM** — Ollama (local, sin límites) · Google Gemini (nube, alternativa)
- **FastAPI + Uvicorn** — webhook de WhatsApp y panel de administración
- **React** (vía FastAPI) — panel web REBOBINA con datos de SQLite
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
│   ├── llm_client.py         # Cliente LLM (Ollama/Gemini) con degradación
│   ├── inference_engine.py   # Motor de inferencia (forward chaining)
│   ├── business_rules.py     # Reglas de negocio (descuentos, stock)
│   └── console.py            # Utilidad de salida UTF-8 (Windows)
├── database/
│   ├── db.py                 # Conexión y esquema SQLite
│   ├── repository.py         # Consultas (catálogo, clientes)
│   └── seed.py               # Datos de ejemplo (catálogo, clientes, rentas)
├── channels/
│   └── whatsapp_twilio.py    # Adaptador del canal WhatsApp (Twilio)
├── api/
│   └── main.py               # Servidor FastAPI + webhook de WhatsApp
├── ui/
│   └── app.py                # Interfaz web de chat (Streamlit, simulador cliente)
├── webpanel/                 # Panel de administración REBOBINA (React + FastAPI)
│   ├── data.py               # Genera los datos del panel desde la BD real
│   └── static/               # Diseño del panel (HTML, CSS, React)
├── orchestrator.py           # Orquestador conversacional de los 3 agentes
├── tests/                    # Pruebas automatizadas (unittest)
├── run_cli.py                # Prueba local del Agente 1 por terminal
├── run_inference.py          # Demo del motor de inferencia (IF/THEN)
├── run_orders.py             # Demo del Agente 2 (generación de pedido)
├── run_persist.py            # Demo de persistencia (guardar pedido en BD)
├── run_supervisor.py         # Demo del flujo completo 1 -> 2 -> 3
├── run_orchestrator.py       # Demo conversacional (pedido + confirmación)
├── requirements.txt
├── .env.example              # Plantilla de variables (copiar a .env)
├── WHATSAPP_SETUP.md         # Guía para conectar WhatsApp
├── OLLAMA_SETUP.md           # Guía para IA local con Ollama
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
El sistema usa **IA local con Ollama** por defecto (sin límites de cuota).
Instálalo siguiendo **[OLLAMA_SETUP.md](OLLAMA_SETUP.md)** (resumen: instala
Ollama y ejecuta `ollama pull llama3.2`).

¿Prefieres **Gemini** (nube)? En `.env` pon `LLM_PROVIDER=gemini` y tu
`GEMINI_API_KEY` (gratis en <https://aistudio.google.com/apikey>).

> 💡 Sin ningún proveedor disponible, el sistema **igual funciona** en modo solo-reglas.

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

### 7. Panel de administración REBOBINA (para el dueño/empleados)
```powershell
python -m database.seed          # carga datos de demostración (recomendado)
uvicorn api.main:app --port 8000
```
Abre **http://localhost:8000/panel/** — un dashboard de escritorio con: pedidos
**por validar** (llegan del bot de WhatsApp), alertas (agotados, rentas vencidas,
stock bajo, títulos solicitados), catálogo/stock, clientes, descuentos, historial
e ingresos. El personal **valida o rechaza** los pedidos; no realiza la venta
(eso lo hacen los 3 agentes).

### 8. Conectar a WhatsApp (opcional)
Levanta el servidor del webhook:
```powershell
uvicorn api.main:app --reload --port 8000
```
Abre <http://127.0.0.1:8000/> para ver el estado. Para enlazarlo con WhatsApp
(cuenta de Twilio + ngrok) sigue la guía paso a paso:
**[WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)**.

---

## 🧪 Pruebas

Ejecuta la suite de pruebas automatizadas (16 pruebas, sin dependencias externas):
```powershell
python -m unittest discover -s tests
```
Cubren el motor de inferencia, los agentes, la persistencia y el flujo completo.

---

## 🔐 Seguridad

- El archivo **`.env` NUNCA se sube a GitHub** (está en `.gitignore`).
- Si expones una API key por accidente, **regenérala** de inmediato.
- La base de datos (`*.db`) tampoco se versiona: se regenera con `seed.py`.

---

## 📄 Documentación

El **registro del proyecto** y el **manual de usuario** completo están en
**[docs/GG_registro_Proy.md](docs/GG_registro_Proy.md)** — base del PDF entregable
`GG_registro_Proy.pdf` (objetivo, arquitectura, base de conocimiento, inferencias,
agentes, base de datos, herramientas y manual de instalación/uso).

---

## 📝 Licencia

Proyecto con fines educativos.
