import os
from dotenv import load_dotenv
import time
import json
import requests
import urllib3
from config import Config

# Validar configuración
Config.validate()

# Usar configuración
ARGOCD_API = Config.ARGOCD_API
ARGOCD_TOKEN = Config.ARGOCD_TOKEN
SLACK_WEBHOOK_URL = Config.SLACK_WEBHOOK_URL

# Deshabilitar advertencias de SSL para certificados autofirmados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Función para enviar notificación a Slack
def send_slack_notification(app_name, status, attempts, action=""):
    message_text = (
        f"```\n"
        f"{'Aplicación':<20} {'Estado':<15} {'Intentos':<10}\n"
        f"{'-' * 50}\n"
        f"{app_name:<20} {status:<15} {attempts:<10}\n"
        f"{'-' * 50}\n"
        f"{action}\n"
        f"```"
    )
    message = {
        "text": f"⚠️ *Estado de la aplicación:*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message_text
                }
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()
        print(f"📩 Notificación enviada a Slack: {app_name} - {status}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al enviar notificación a Slack: {e}")

# Función para obtener las aplicaciones desde la API de ArgoCD
def get_argocd_apps():
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    try:
        response = requests.get(f"{ARGOCD_API}/applications", headers=headers, verify=False)
        response.raise_for_status()
        apps = response.json().get("items", [])
        print(f"📋 Aplicaciones obtenidas: {len(apps)}")
        return apps
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener aplicaciones desde ArgoCD: {e}")
        return []

# Función para sincronizar una aplicación
def sync_app(app_name):
    headers = {
        "Authorization": f"Bearer {ARGOCD_TOKEN}",
        "Content-Type": "application/json"  # Asegura que el encabezado Content-Type sea correcto
    }
    try:
        response = requests.post(
            f"{ARGOCD_API}/applications/{app_name}/sync",
            headers=headers,
            verify=False,
            json={}  # Envía un cuerpo vacío como JSON
        )
        response.raise_for_status()
        print(f"🔄 Sincronización iniciada para {app_name}.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al sincronizar {app_name}: {e}")

# Función para obtener el estado de una aplicación
def get_application_status(app_name):
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    try:
        response = requests.get(f"{ARGOCD_API}/applications/{app_name}", headers=headers, verify=False)
        response.raise_for_status()
        app_info = response.json()
        health_status = app_info.get("status", {}).get("health", {}).get("status", "Unknown")
        sync_status = app_info.get("status", {}).get("sync", {}).get("status", "Unknown")
        return health_status, sync_status
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener el estado de {app_name}: {e}")
        return "Unknown", "Unknown"

# Función para refrescar el estado de una aplicación
def refresh_app(app_name):
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    try:
        response = requests.get(
            f"{ARGOCD_API}/applications/{app_name}?refresh=true",
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        print(f"🔄 Refrescando estado de la aplicación '{app_name}'.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al refrescar la aplicación '{app_name}': {e}")

# Función para pausar una aplicación (sin llamada a la API)
def pause_app(app_name):
    print(f"⏸️ La aplicación '{app_name}' ha sido marcada como pausada localmente después de 3 intentos fallidos.")

# Función principal para monitorear el estado de las aplicaciones
def main():
    attempts = {}
    notified = set()  # Almacena las aplicaciones que ya han sido notificadas
    paused_apps = set()  # Almacena las aplicaciones que han sido pausadas

    while True:
        apps = get_argocd_apps()
        print("\n📋 Estado actual de las aplicaciones:")
        print(f"{'Aplicación':<20} {'Estado':<15} {'Intentos':<10}")
        print("-" * 50)

        for app in apps:
            app_name = app.get("metadata", {}).get("name", "Desconocido")

            # Refrescar el estado de la aplicación antes de verificar
            refresh_app(app_name)

            health_status, sync_status = get_application_status(app_name)
            print(f"{app_name:<20} {health_status:<15} {attempts.get(app_name, 0):<10}")

            # Inicializa los intentos para cada aplicación si no existen
            if app_name not in attempts:
                attempts[app_name] = 0

            if health_status == "Healthy" and sync_status == "Synced":
                print(f"✅ '{app_name}' está en estado Healthy y Synced.")
                if app_name in notified:
                    print(f"📩 Notificando que '{app_name}' volvió a Healthy.")
                    send_slack_notification(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
                    notified.discard(app_name)  # Elimina de la lista de notificados
                attempts[app_name] = 0  # Reinicia los intentos
                paused_apps.discard(app_name)  # Elimina de la lista de pausadas
            elif app_name in paused_apps:
                print(f"⏸️ '{app_name}' está pausada. Monitoreando su estado...")
            elif sync_status == "OutOfSync":
                print(f"⚠️ '{app_name}' está OutOfSync. Intentando sincronizar...")
                sync_app(app_name)
                attempts[app_name] += 1
            elif health_status in ["Degraded", "Error"]:
                if attempts[app_name] < 3:
                    print(f"🔄 Intentando recuperar '{app_name}' (Intento {attempts[app_name] + 1}/3)...")
                    sync_app(app_name)
                    attempts[app_name] += 1
                else:
                    if app_name not in notified:
                        print(f"⏸️ '{app_name}' no se pudo recuperar después de 3 intentos. Notificando y pausando...")
                        send_slack_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
                        pause_app(app_name)  # Pausar la aplicación
                        notified.add(app_name)  # Marca como notificada
                        paused_apps.add(app_name)  # Marca como pausada
            else:
                print(f"ℹ️ '{app_name}' está en estado desconocido: {health_status}.")

        print("-" * 50)
        time.sleep(60)

if __name__ == "__main__":
    main()
