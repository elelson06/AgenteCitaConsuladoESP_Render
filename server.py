"""
server.py — Wrapper HTTP mínimo para Render Free Tier
------------------------------------------------------
Render necesita que el proceso escuche en un puerto HTTP.
Este archivo lanza el agente en un hilo separado y expone
un endpoint /health para que UptimeRobot lo pingee cada
5 minutos y evite el sleep de 15 min del free tier.
"""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from agent import main as agent_main
import asyncio


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Agente corriendo")

    def log_message(self, format, *args):
        # Silenciar logs del HTTP server para no ensuciar los del agente
        pass


def run_agent():
    """Corre el agente en su propio event loop (hilo separado)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(agent_main())


if __name__ == "__main__":
    # ── 1. Lanzar el agente en un hilo de fondo ──────────────────
    agent_thread = threading.Thread(target=run_agent, daemon=True)
    agent_thread.start()
    print("✅ Agente iniciado en hilo de fondo")

    # ── 2. Levantar el servidor HTTP en el puerto que indica Render ─
    import os
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ Health server escuchando en puerto {port}")
    httpd.serve_forever()
