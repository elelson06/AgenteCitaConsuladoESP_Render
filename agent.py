"""
Agente de citas — Consulado General de España en Córdoba

Cómo funciona:
  1. Consulta la API de citaconsular.es (proxy de bookitit) para obtener servicios
  2. Para cada servicio, consulta si hay slots libres en los próximos días
  3. Si encuentra disponibilidad → notifica por Telegram
  4. Si no hay nada → espera el intervalo y reintenta
"""

import time
import random
import re
import json
import requests
from datetime import datetime, timedelta
from config import BOOKITIT_PUBLIC_KEY, WIDGET_URL, CHECK_INTERVAL_MIN
from notifier import send_telegram

# ── URL base real (descubierta via DevTools) ──────────────────────────────────
# El widget NO llama a app.bookitit.com sino al proxy de citaconsular.es
API_BASE = "https://www.citaconsular.es/onlinebookings"

# Parámetros fijos que el widget siempre manda
WIDGET_SRC = f"https://www.citaconsular.es/es/hosteds/widgetdefault/{BOOKITIT_PUBLIC_KEY}/"
COMMON_PARAMS = {
    "type":      "default",
    "publickey": BOOKITIT_PUBLIC_KEY,
    "lang":      "es",
    "version":   "4",
    "src":       WIDGET_SRC,
    "srvsrc":    "https://www.citaconsular.es",
}

# Headers que imitan exactamente al browser (copiados de DevTools)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
    "Accept":           "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
    "Accept-Language":  "es-US,es-419;q=0.9,es;q=0.8",
    "Referer":          WIDGET_SRC,
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest":   "empty",
    "Sec-Fetch-Mode":   "cors",
    "Sec-Fetch-Site":   "same-origin",
}

# Cuántos días hacia adelante buscar slots disponibles
DAYS_AHEAD = 60


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _callback_name():
    """Genera un nombre de callback JSONP aleatorio igual que jQuery."""
    ts = int(time.time() * 1000)
    rnd = random.randint(10000000, 99999999)
    return f"jQuery{ts}{rnd}"


def _parse_jsonp(text):
    """
    Extrae el JSON del wrapper JSONP.
    Ejemplo: jQuery123({...}) → devuelve el dict {...}
    """
    match = re.search(r'\((\{.*\})\)\s*;?\s*$', text, re.DOTALL)
    if not match:
        raise ValueError(f"Respuesta JSONP inesperada: {text[:200]}")
    return json.loads(match.group(1))


def _get(endpoint, extra_params=None):
    """Helper genérico para llamadas JSONP a la API."""
    params = dict(COMMON_PARAMS)
    params["callback"] = _callback_name()
    params["_"] = int(time.time() * 1000)
    if extra_params:
        params.update(extra_params)

    url = f"{API_BASE}/{endpoint}/"
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return _parse_jsonp(r.text)


def get_services():
    """Obtiene la lista de servicios del consulado."""
    try:
        data = _get("getservices")
        services = data.get("getservices", {}).get("services", [])
        if isinstance(services, dict):
            services = [services]
        return services
    except Exception as e:
        print(f"[{_now()}] ⚠️  Error obteniendo servicios: {e}")
        return []


def get_agendas(service_id):
    """Obtiene las agendas (ventanillas) para un servicio."""
    try:
        data = _get("getagendas", {"service": service_id})
        agendas = data.get("getagendas", {}).get("agendas", [])
        if isinstance(agendas, dict):
            agendas = [agendas]
        return agendas
    except Exception as e:
        print(f"[{_now()}] ⚠️  Error obteniendo agendas: {e}")
        return []


def get_free_slots(service_id, agenda_id, date_str):
    """
    Consulta slots libres para un servicio/agenda en una fecha concreta.
    date_str formato: YYYY-MM-DD
    """
    try:
        data = _get("getfreeslots", {
            "service": service_id,
            "agenda":  agenda_id,
            "date":    date_str,
        })
        slots = data.get("getfreeslots", {}).get("freeslots", [])
        if isinstance(slots, dict):
            slots = [slots]
        return slots
    except Exception as e:
        print(f"[{_now()}] ⚠️  Error consultando slots ({date_str}): {e}")
        return []


def check_availability():
    """
    Recorre servicios → agendas → fechas buscando cualquier slot libre.
    Retorna (True, detalle) si hay disponibilidad, (False, "") si no.
    """
    services = get_services()
    if not services:
        print(f"[{_now()}] ⚠️  No se pudieron obtener los servicios. Reintentando en el próximo ciclo.")
        return False, ""

    print(f"[{_now()}] Servicios encontrados: {len(services)}")

    today = datetime.today()
    dates = [
        (today + timedelta(days=d)).strftime("%Y-%m-%d")
        for d in range(DAYS_AHEAD)
    ]

    for service in services:
        service_id   = service.get("id", "")
        service_name = service.get("name", service_id)
        print(f"[{_now()}] Revisando servicio: {service_name} ({service_id})")

        agendas = get_agendas(service_id)
        if not agendas:
            print(f"[{_now()}]   Sin agendas para este servicio.")
            continue

        for agenda in agendas:
            agenda_id   = agenda.get("id", "")
            agenda_name = agenda.get("name", agenda_id)

            for date_str in dates:
                slots = get_free_slots(service_id, agenda_id, date_str)
                if slots:
                    detalle = (
                        f"📅 Fecha: {date_str}\n"
                        f"🗂️ Servicio: {service_name}\n"
                        f"👤 Agenda: {agenda_name}\n"
                        f"🕐 Slots disponibles: {len(slots)}"
                    )
                    print(f"[{_now()}] ✅ DISPONIBILIDAD ENCONTRADA — {detalle}")
                    return True, detalle

                time.sleep(0.3)

    return False, ""


def main():
    print(f"[{_now()}] 🤖 Agente de citas iniciado (modo API, sin browser)")
    print(f"[{_now()}] Consulado: España - Córdoba | Intervalo: ~{CHECK_INTERVAL_MIN} min")
    print("─" * 60)

    while True:
        print(f"[{_now()}] Iniciando consulta a la API de citaconsular...")
        hay_cita, detalle = check_availability()

        if hay_cita:
            send_telegram(
                f"🚨 *HAY CITAS DISPONIBLES*\n\n"
                f"{detalle}\n\n"
                f"🔗 {WIDGET_URL}\n"
                f"⏰ {_now()}\n\n"
                f"¡Entrá cuanto antes a reservar!"
            )
        else:
            print(f"[{_now()}] ❌ Sin disponibilidad. Siguiente ciclo en ~{CHECK_INTERVAL_MIN} min.")

        wait_sec = CHECK_INTERVAL_MIN * 60 + random.uniform(-30, 30)
        print(f"[{_now()}] Próxima consulta en {wait_sec / 60:.1f} min")
        print("─" * 60)
        time.sleep(wait_sec)


if __name__ == "__main__":
    main()
