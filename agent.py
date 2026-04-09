"""
Agente de citas — Consulado General de España en Córdoba
Versión PythonAnywhere (sin browser, usa la API REST de bookitit)

Cómo funciona:
  1. Consulta la API de bookitit para obtener los servicios disponibles
  2. Para cada servicio, consulta si hay slots libres en los próximos días
  3. Si encuentra disponibilidad → notifica por Telegram
  4. Si no hay nada → espera el intervalo y reintenta
"""

import time
import random
import requests
from datetime import datetime, timedelta
from config import BOOKITIT_PUBLIC_KEY, WIDGET_URL, CHECK_INTERVAL_MIN
from notifier import send_telegram

API_BASE = "https://app.bookitit.com/api/11"

# Cuántos días hacia adelante buscar slots disponibles
DAYS_AHEAD = 60

# Headers para que la API no nos rechace
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "es-AR,es;q=0.9",
    "Referer": "https://www.citaconsular.es/",
    "Origin": "https://www.citaconsular.es",
    "X-Requested-With": "XMLHttpRequest",
}


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_services():
    """Obtiene la lista de servicios del consulado."""
    url = f"{API_BASE}/getservices/{BOOKITIT_PUBLIC_KEY}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"[DEBUG] Status: {r.status_code}")
        print(f"[DEBUG] Response: {r.text[:300]}")
        r.raise_for_status()
        data = r.json()
        services = data.get("getservices", {}).get("services", [])
        if isinstance(services, dict):
            # Cuando hay un solo servicio la API devuelve dict en vez de lista
            services = [services]
        return services
    except Exception as e:
        print(f"[{_now()}] ⚠️  Error obteniendo servicios: {e}")
        return []


def get_agendas(service_id):
    """Obtiene las agendas (funcionarios/ventanillas) para un servicio."""
    url = f"{API_BASE}/getagendas/{BOOKITIT_PUBLIC_KEY}/{service_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
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
    Retorna lista de slots o [] si no hay.
    """
    url = (
        f"{API_BASE}/getfreeslots/{BOOKITIT_PUBLIC_KEY}"
        f"/{service_id}/{agenda_id}/{date_str}/false"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
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

                # Pausa mínima entre requests para no saturar la API
                time.sleep(0.3)

    return False, ""


def main():
    print(f"[{_now()}] 🤖 Agente de citas iniciado (modo API, sin browser)")
    print(f"[{_now()}] Consulado: España - Córdoba | Intervalo: ~{CHECK_INTERVAL_MIN} min")
    print("─" * 60)

    while True:
        print(f"[{_now()}] Iniciando consulta a la API de bookitit...")
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

        # Espera con variación aleatoria ±30s
        wait_sec = CHECK_INTERVAL_MIN * 60 + random.uniform(-30, 30)
        print(f"[{_now()}] Próxima consulta en {wait_sec / 60:.1f} min")
        print("─" * 60)
        time.sleep(wait_sec)


if __name__ == "__main__":
    main()
