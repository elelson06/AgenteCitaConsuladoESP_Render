# ══════════════════════════════════════════════════════════════
#  config.py  —  Todos los parámetros del agente
#  Editá solo este archivo para personalizar el comportamiento
# ══════════════════════════════════════════════════════════════

# ── Clave pública del widget de bookitit ─────────────────────
# Extraída de la URL: /widgetdefault/298f7f17f58c0836448a99edecf16e66a
BOOKITIT_PUBLIC_KEY = "298f7f17f58c0836448a99edecf16e66a"

# ── URL del widget (solo para incluir en las notificaciones) ──
WIDGET_URL = (
    "https://www.citaconsular.es/es/hosteds/widgetdefault/"
    "298f7f17f58c0836448a99edecf16e66a"
)

# ── Intervalo entre checks (en minutos) ───────────────────────
CHECK_INTERVAL_MIN = 10

# ── Telegram ──────────────────────────────────────────────────
# Paso 1: Buscá @BotFather en Telegram → /newbot → copiá el token
# Paso 2: Escribile /start a tu bot, luego visitá:
#   https://api.telegram.org/bot<TU_TOKEN>/getUpdates
#   y copiá el "id" que aparece dentro de "chat"
TELEGRAM_BOT_TOKEN = "6003653629:AAFu0epzzZMIFlHfcUg2lbwjuZMXyrLQLtY"  # <-- reemplazá
TELEGRAM_CHAT_ID   = "2125808164"                                          # <-- reemplazá
