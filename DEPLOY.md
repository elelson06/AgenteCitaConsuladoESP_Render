# 🚀 Deploy del Agente de Citas en Render (Gratis)

## Estructura de archivos necesaria en tu repo

```
tu-repo/
├── agent.py          ← tu agente (sin cambios)
├── server.py         ← wrapper HTTP (nuevo)
├── notifier.py       ← tu notificador de Telegram
├── config.py         ← tu config (sin hardcodear secretos)
├── requirements.txt  ← solo "requests"
└── render.yaml       ← configuración de Render
```

---

## Paso 1 — Subir a GitHub

```bash
git init
git add .
git commit -m "Agente de citas Render"
git remote add origin https://github.com/elelson06/AgenteCitaConsuladoESP_Render.git
git push -u origin main
```

---

## Paso 2 — Crear cuenta y servicio en Render

1. Entrá a https://render.com y creá una cuenta gratuita
2. **New → Web Service**
3. Conectá tu repositorio de GitHub
4. Render detecta el `render.yaml` automáticamente

---

## Paso 3 — Configurar variables de entorno

En el dashboard de Render → tu servicio → **Environment**,
agregá estas variables (las que tienen `sync: false` en el yaml):

| Variable             | Valor                          |
|---------------------|--------------------------------|
| `BOOKITIT_PUBLIC_KEY` | Tu clave pública de bookitit |
| `WIDGET_URL`         | URL del widget del consulado   |
| `CHECK_INTERVAL_MIN` | `5` (o el intervalo que uses)  |
| `TELEGRAM_TOKEN`     | Token de tu bot de Telegram    |
| `TELEGRAM_CHAT_ID`   | Tu chat ID de Telegram         |

⚠️ **Nunca pongas estos valores en el código ni en el repo.**

---

## Paso 4 — Adaptar config.py para leer variables de entorno

Tu `config.py` debería leer así:

```python
import os

BOOKITIT_PUBLIC_KEY  = os.environ["BOOKITIT_PUBLIC_KEY"]
WIDGET_URL           = os.environ["WIDGET_URL"]
CHECK_INTERVAL_MIN   = int(os.environ.get("CHECK_INTERVAL_MIN", "5"))
TELEGRAM_TOKEN       = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID     = os.environ["TELEGRAM_CHAT_ID"]
```

---

## Paso 5 — Deploy

Render hace el deploy automáticamente al detectar el push.
Podés verlo en: **Dashboard → tu servicio → Logs**

---

## Paso 6 — Evitar el sleep (¡IMPORTANTE!)

El free tier de Render duerme el servicio si no recibe
tráfico por 15 minutos. Para evitarlo:

1. Entrá a https://uptimerobot.com (gratis)
2. **Add New Monitor**:
   - Monitor Type: **HTTP(s)**
   - URL: `https://agente-citas-espana.onrender.com/`
   - Monitoring Interval: **5 minutes**
3. ¡Listo! UptimeRobot pingea tu servicio cada 5 min
   y nunca se duerme.

Tu URL de Render es visible en: Dashboard → tu servicio →
el link que aparece arriba a la derecha (termina en `.onrender.com`)

---

## ✅ Verificar que funciona

En los **Logs** de Render deberías ver:
```
✅ Agente iniciado en hilo de fondo
✅ Health server escuchando en puerto 10000
[2026-04-08 10:00:00] 🤖 Agente de citas iniciado (modo API, sin browser)
[2026-04-08 10:00:00] Iniciando consulta a la API de bookitit...
```

---

## ❓ Preguntas frecuentes

**¿El free tier tiene límite de horas?**
Sí, 750 horas/mes. Con UptimeRobot manteniéndolo activo,
un mes tiene ~720 horas → entra justo. Si hay problemas,
el servicio se puede suspender unos días a fin de mes.

**¿Puedo usar variables de entorno localmente?**
Sí, creá un archivo `.env` (NO lo subas al repo) y usá
`python-dotenv` para cargarlo en desarrollo:
```bash
pip install python-dotenv
```
```python
# Al inicio de config.py, solo para desarrollo local:
from dotenv import load_dotenv
load_dotenv()
```

**¿Qué pasa si Render reinicia el servicio?**
El agente arranca solo nuevamente. No pierde estado
porque no guarda nada localmente.
