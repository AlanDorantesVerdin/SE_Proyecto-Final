<!--
  Documento de registro del proyecto (fuente en Markdown).
  Exportar a PDF como: GG_registro_Proy.pdf
  Las CAPTURAS marcadas con [ … ] se insertan al exportar.
-->

# REBOBINA — Sistema Experto de Atención y Ventas con Agentes Inteligentes

**Materia:** Sistemas Expertos
**Proyecto:** Tienda de películas en formato físico (renta y venta) — "REBOBINA / CineFísico"
**Autor:** Alan Dorantes Verdín
**Repositorio:** <https://github.com/AlanDorantesVerdin/SE_Proyecto-Final>
**Video demostrativo:** _[pegar enlace de YouTube aquí]_
**Fecha:** junio 2026

---

## 1. Objetivo

Desarrollar un **sistema experto moderno basado en agentes inteligentes** capaz de
atender clientes, realizar inferencias y automatizar el proceso de venta y renta de
películas en formato físico (estilo Blockbuster moderno). El sistema integra
ingeniería del conocimiento, un motor de inferencia, base de datos, agentes
inteligentes, IA moderna (LLM), explicabilidad del razonamiento y una arquitectura
cliente-servidor, ejecutándose de manera **local** en una computadora personal.

El cliente realiza sus pedidos por **WhatsApp**, conversando con un chat inteligente;
los **tres agentes** procesan la venta de forma automática; y el dueño o los empleados
supervisan todo desde un **panel web de administración** (REBOBINA), donde validan
pedidos y controlan stock, clientes, ingresos y alertas.

---

## 2. Descripción del sistema

REBOBINA automatiza la atención y la venta de una tienda de películas:

1. **El cliente escribe por WhatsApp** (p. ej. *"Hola, quiero rentar 2 Matrix"*).
2. El **Agente 1 (Atención al Cliente)** interpreta la intención y las películas.
3. El **Agente 2 (Generador de Pedido)** valida contra el catálogo, ejecuta el
   **motor de inferencia** (descuentos, stock, reabastecimiento, rentas vencidas) y
   arma el pedido.
4. El **Agente 3 (Supervisor / Explicador)** resume la venta, **explica las
   inferencias** realizadas y pide la confirmación del cliente.
5. El pedido queda **"por validar"** y aparece en el **panel web**, donde el personal
   lo **valida o rechaza**. Toda la operación (ventas, stock, reabastecimiento) se
   refleja en tiempo real para la administración.

El personal **no realiza la venta**: esta ocurre entre los tres agentes. El personal
solo **supervisa y valida**.

---

## 3. Arquitectura

```
        CLIENTE                          NEGOCIO (dueño / empleados)
          │                                        │
     WhatsApp (Twilio)                     Panel web REBOBINA
          │                                  (navegador, /panel/)
          ▼                                        ▲
   ┌──────────────┐                                │
   │  FastAPI     │  webhook  ───────────►  datos en vivo (JSON)
   │  (servidor)  │◄───────────────────────  validar / rechazar
   └──────┬───────┘
          │ orquestador (estado de conversación)
          ▼
   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐
   │  Agente 1   │──►│  Agente 2   │──►│  Agente 3    │
   │ Atención    │   │ Pedido +    │   │ Supervisor / │
   │ al cliente  │   │ inferencias │   │ Explicador   │
   └─────────────┘   └──────┬──────┘   └──────────────┘
          │                 │ guarda
          ▼                 ▼
   ┌───────────────────────────────────┐
   │   Base de datos  SQLite            │
   │ (películas, clientes, pedidos,     │
   │  rentas, reabastecimiento)         │
   └───────────────────────────────────┘
```

- **Arquitectura cliente-servidor local:** un servidor **FastAPI** expone el webhook
  de WhatsApp y el panel web; ambos comparten la misma base de datos SQLite.
- **Enfoque híbrido:** motor de reglas (sistema experto clásico, determinista y
  explicable) + **IA moderna** (LLM) para la comprensión del lenguaje natural, con
  **degradación elegante** (si el LLM no está disponible, el sistema sigue funcionando
  solo con reglas).

---

## 4. Base de conocimiento

El conocimiento del sistema es **explícito y editable** (no una "caja negra"):

- **Reconocimiento de intención** (`core/knowledge_base.py`): diccionarios de palabras
  clave por intención (saludar, rentar, comprar, consultar disponibilidad, explorar
  catálogo, soporte, despedida). Permite clasificar el mensaje del cliente sin depender
  de Internet.
- **Reglas de negocio** (`core/business_rules.py`): la política comercial codificada
  como reglas IF/THEN con prioridades, descritas en lenguaje natural y con parámetros
  ajustables (porcentajes, umbrales, tope).
- **Catálogo y clientes** (base de datos): hechos sobre películas (stock, precios,
  género, formato) y clientes (frecuencia, rentas) que alimentan las inferencias.

---

## 5. Inferencias utilizadas

El **motor de inferencia** (`core/inference_engine.py`) aplica **encadenamiento hacia
adelante** (forward chaining) sobre los hechos de cada pedido, disparando reglas por
prioridad y registrando una **traza del razonamiento** para la explicabilidad.

Reglas IF/THEN implementadas:

| Regla | Condición (IF) | Acción (THEN) |
|---|---|---|
| Reabastecimiento | `stock < cantidad solicitada` | Sugerir reabastecimiento del título |
| Rentas vencidas | El cliente tiene rentas sin devolver | Advertir antes de una nueva renta |
| Descuento cliente frecuente | `is_frequent = 1` | +10 % de descuento |
| Descuento por volumen | `unidades ≥ 5` | +8 % de descuento |
| Descuento por monto | `subtotal ≥ $300` | +10 % de descuento |
| Tope de descuento | `descuento acumulado > 25 %` | Limitar a 25 % |
| Cliente no registrado | `cliente = null` | Invitar a registrarse |
| Cálculo de total | siempre | Aplicar el descuento final al subtotal |

**Ejemplo de encadenamiento:** un cliente frecuente compra 5 títulos por $845 →
se disparan *frecuente (+10 %)*, *volumen (+8 %)* y *monto (+10 %)* = 28 %, lo que a su
vez dispara la regla de *tope* que lo limita a **25 %** → total $634. Cada paso queda
explicado.

---

## 6. Explicación de los agentes

### Agente 1 — Atención al Cliente (`agents/agent_customer.py`)
Lee el mensaje, **detecta la intención** y **extrae las entidades** (películas,
cantidades, acción). Combina reglas (deterministas) con un **LLM** (Ollama o Gemini)
para entender lenguaje natural y responder cualquier consulta (recomendaciones,
precios, formatos). Consulta el catálogo y responde automáticamente.

### Agente 2 — Generador de Pedido (`agents/agent_orders.py`)
**Procesa** la interpretación del Agente 1, **valida** contra el catálogo, ejecuta el
**motor de inferencia** (descuentos, reabastecimiento, rentas vencidas), **arma el
pedido** y lo **guarda en la base de datos** (estado `por_validar`), conservando el
razonamiento.

### Agente 3 — Supervisor / Explicador (`agents/agent_supervisor.py`)
Genera el **resumen de la venta**, **explica las decisiones e inferencias** (de forma
fiel a las reglas que realmente se dispararon) y **solicita la validación** final.

Un **orquestador** (`orchestrator.py`) coordina el flujo 1 → 2 → 3 con estado de
conversación (confirmar con *SÍ* / cancelar con *NO*).

---

## 7. Base de datos utilizada

**SQLite** (archivo local `database/store.db`, regenerable con `python -m database.seed`).
Esquema (`database/db.py`):

- **movies** — catálogo (título, género, año, formato, precio de venta/renta, stock, rating).
- **customers** — clientes (nombre, teléfono, frecuente, rentas acumuladas).
- **orders** / **order_items** — pedidos y sus líneas (con snapshot e historial).
- **rentals** — rentas con fecha de vencimiento (para detectar rentas vencidas).
- **restock_suggestions** — sugerencias de reabastecimiento generadas por las inferencias.

El acceso a datos se centraliza en `database/repository.py`.

[ CAPTURA 7.1 — diagrama o vista de las tablas de la base de datos ]

---

## 8. Herramientas utilizadas

| Herramienta | Uso |
|---|---|
| **Python 3.13** | Lenguaje principal |
| **SQLite** | Base de datos local |
| **FastAPI + Uvicorn** | Servidor: webhook de WhatsApp y panel web |
| **Twilio** | Canal de WhatsApp (sandbox) |
| **Ollama** / **Google Gemini** (`google-genai`) | IA / LLM (local o nube) |
| **React** (servido por FastAPI) | Panel de administración REBOBINA |
| **Streamlit** | Chat web (simulador de cliente) |
| **httpx / python-dotenv** | Llamadas HTTP y manejo de credenciales |
| **unittest** | Pruebas automatizadas |
| **Git / GitHub** | Control de versiones e historial de desarrollo |

---

## 9. Capturas del sistema

> Insertar al exportar a PDF:

- [ CAPTURA 9.1 — Panel REBOBINA: vista *Resumen* (ingresos, por validar, alertas) ]
- [ CAPTURA 9.2 — Panel: *Por validar* con el cajón de detalle y el razonamiento ]
- [ CAPTURA 9.3 — Panel: *Catálogo* con stock y *Alertas* ]
- [ CAPTURA 9.4 — Conversación del bot por WhatsApp (o el simulador de chat) ]
- [ CAPTURA 9.5 — Terminal: `python run_supervisor.py` (flujo de los 3 agentes) ]
- [ CAPTURA 9.6 — Terminal: `python run_inference.py` (razonamiento IF/THEN) ]

---

## 10. Conclusiones

El proyecto cumple los requisitos técnicos de un sistema experto moderno: integra
**ingeniería del conocimiento** (reglas explícitas), un **motor de inferencia** con
encadenamiento hacia adelante, **base de datos** relacional, **tres agentes
inteligentes** que cooperan, **IA moderna** (LLM) con degradación elegante,
**explicabilidad** del razonamiento y una **arquitectura cliente-servidor** local.

El enfoque híbrido (reglas + LLM) resultó clave: las reglas garantizan decisiones
**deterministas y explicables** —indispensables en un sistema experto— mientras que el
LLM aporta naturalidad en la conversación. La separación entre la **venta automática
(agentes)** y la **supervisión humana (panel)** refleja un caso de uso realista y
demuestra automatización de procesos de negocio de principio a fin.

Como trabajo futuro: notificaciones proactivas (avisar al cliente cuando llega un
título), reportes históricos en el panel y autenticación de usuarios del panel.

---

# Manual de Usuario

Guía para instalar, configurar y ejecutar REBOBINA **desde cero**.

## A. Requisitos
- **Python 3.11 o superior** (probado en 3.13).
- **Git** (para clonar el repositorio).
- *(Opcional)* **Ollama** para IA local, o una **API key de Gemini** para IA en la nube.
- *(Opcional)* Cuenta de **Twilio** y **ngrok** para WhatsApp.

## B. Instalación

```powershell
git clone https://github.com/AlanDorantesVerdin/SE_Proyecto-Final.git
cd SE_Proyecto-Final
py -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate en Linux/macOS)
pip install -r requirements.txt
```

## C. Configurar dependencias / variables

```powershell
copy .env.example .env            # cp en Linux/macOS
```
Elige el proveedor de IA en `.env`:
- **Ollama (local, recomendado, sin límites):** instala Ollama, ejecuta
  `ollama pull llama3.2` y deja `LLM_PROVIDER=ollama` (ver `OLLAMA_SETUP.md`).
- **Gemini (nube):** pon `LLM_PROVIDER=gemini` y tu `GEMINI_API_KEY`.
- Sin ningún proveedor, el sistema **igual funciona** en modo solo-reglas.

## D. Conectar / poblar la base de datos

```powershell
python -m database.seed           # crea las tablas y carga datos de demostración
```

## E. Ejecutar los agentes y las inferencias

```powershell
python run_cli.py --demo          # Agente 1 (atención al cliente)
python run_inference.py           # motor de inferencia (reglas IF/THEN)
python run_orders.py              # Agente 2 (genera el pedido)
python run_supervisor.py          # flujo completo de los 3 agentes
python run_orchestrator.py        # conversación con confirmación de pedido
```

## F. Abrir el panel de administración (dueño / empleados)

```powershell
uvicorn api.main:app --port 8000
```
Abre **http://localhost:8000/panel/** en el navegador. Verás pedidos por validar,
alertas, catálogo, clientes, descuentos, historial e ingresos. Haz clic en un pedido
para ver el detalle y **validarlo o rechazarlo**.

## G. Conectar WhatsApp (opcional)

Sigue la guía **`WHATSAPP_SETUP.md`** (cuenta de Twilio + `ngrok http 8000`, y
configurar la URL `https://XXXX.ngrok-free.app/webhook/whatsapp` en el sandbox).

## H. Ejecutar las pruebas

```powershell
python -m unittest discover -s tests
```

---

_Fin del documento._
