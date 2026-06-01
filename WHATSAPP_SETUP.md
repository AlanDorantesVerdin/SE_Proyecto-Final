# 📱 Guía: conectar el Agente 1 a WhatsApp (Twilio Sandbox)

Esta guía explica, paso a paso, cómo poner a tu **Agente 1** a responder por
WhatsApp usando el **sandbox gratuito de Twilio**. No necesitas un número de
empresa ni verificación de Meta.

> **Idea general:** WhatsApp → Twilio → (túnel ngrok) → tu servidor FastAPI →
> Agente 1 → respuesta → Twilio → WhatsApp.

---

## Requisitos previos

- El proyecto instalado y funcionando en local (ver [README](README.md)).
- Una cuenta de **Twilio** (gratis): <https://www.twilio.com/try-twilio>
- **ngrok** (gratis) para exponer tu servidor local a Internet:
  <https://ngrok.com/download>

---

## Paso 1 — Credenciales de Twilio

1. Entra a la consola: <https://console.twilio.com>
2. En el panel principal copia tu **Account SID** y tu **Auth Token**.
3. Pégalos en tu archivo `.env`:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=tu_auth_token
   ```

---

## Paso 2 — Activar el Sandbox de WhatsApp

1. En la consola ve a **Messaging → Try it out → Send a WhatsApp message**.
2. Verás un número de sandbox (normalmente **+1 415 523 8886**) y una frase de
   conexión del tipo **`join algo-palabra`**.
3. Desde **tu** WhatsApp, envía ese mensaje `join algo-palabra` al número del
   sandbox. Recibirás una confirmación: ya estás conectado.

> Cualquier persona que quiera probar el bot debe enviar primero ese
> `join algo-palabra` al número del sandbox.

---

## Paso 3 — Levantar el servidor local

En una terminal, dentro del proyecto y con el entorno virtual activado:

```powershell
uvicorn api.main:app --reload --port 8000
```

Comprueba que responde abriendo <http://127.0.0.1:8000/> — deberías ver un JSON
con `"status": "ok"`.

---

## Paso 4 — Exponer el servidor con ngrok

En **otra** terminal:

```powershell
ngrok http 8000
```

ngrok te dará una URL pública HTTPS, por ejemplo:
```
https://a1b2-c3d4.ngrok-free.app
```

> La primera vez, ngrok pide registrar un *authtoken* (gratis): sigue las
> instrucciones que aparecen en pantalla o en tu panel de ngrok.

---

## Paso 5 — Conectar el webhook en Twilio

1. Vuelve a **Messaging → Try it out → Send a WhatsApp message**.
2. Abre la pestaña **Sandbox settings**.
3. En **"When a message comes in"** pega tu URL pública + la ruta del webhook,
   y elige el método **POST**:
   ```
   https://a1b2-c3d4.ngrok-free.app/webhook/whatsapp
   ```
4. Guarda los cambios.

---

## Paso 6 — ¡Probar!

Desde tu WhatsApp (ya unido al sandbox) escribe al número del sandbox, por
ejemplo:

> **Hola, ¿tienen Matrix? quiero rentar 2**

El Agente 1 debería contestarte con disponibilidad y precio. 🎬

---

## (Opcional) Que te reconozca como cliente frecuente

El agente identifica al cliente por su número. Para que tu número aparezca como
cliente frecuente, agrégalo en `database/seed.py` (lista `CUSTOMERS`) con
formato internacional y vuelve a poblar la base:

```python
CUSTOMERS = [
    ("Tu Nombre", "+52155XXXXXXXX", 1, 5),   # 1 = frecuente
    ...
]
```
```powershell
python -m database.seed
```

---

## (Opcional) Validar la firma de Twilio (seguridad)

Para asegurarte de que las peticiones provienen realmente de Twilio, en `.env`:

```env
TWILIO_VALIDATE=true
PUBLIC_BASE_URL=https://a1b2-c3d4.ngrok-free.app
```

Con esto, el webhook rechaza cualquier petición sin una firma válida.

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| No llega respuesta | URL del webhook mal puesta | Revisa que termine en `/webhook/whatsapp` y sea **POST** |
| `ngrok` cambia de URL | URL gratis es temporal | Actualiza la URL en Twilio cada vez que reinicies ngrok |
| 403 "Firma inválida" | `PUBLIC_BASE_URL` no coincide | Debe ser EXACTA la URL de ngrok, o pon `TWILIO_VALIDATE=false` |
| Responde "solo reglas" | Sin API key de Gemini | Normal; el bot funciona igual. Agrega `GEMINI_API_KEY` para IA |
