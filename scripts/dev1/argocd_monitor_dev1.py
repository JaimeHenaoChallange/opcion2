import os
import subprocess
import time
import json
import requests
import urllib3
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env_dev1
load_dotenv(dotenv_path="/workspaces/monitor-2/.env_dev1")

# Deshabilitar advertencias de SSL para certificados autofirmados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración desde variables de entorno
ARGOCD_API = os.getenv("ARGOCD_API")  # Endpoint actualizado
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Validar que las variables sensibles estén configuradas
if not ARGOCD_API or not SLACK_WEBHOOK_URL:
    raise ValueError("❌ Faltan variables de entorno requeridas: ARGOCD_API o SLACK_WEBHOOK_URL.")

# Función para obtener un token temporal mediante SSO
def get_sso_token():
    try:
        print("🔑 Obteniendo token SSO...")
        result = subprocess.run(
            ["argocd", "login", ARGOCD_API.replace("/api/v1", ""), "--sso", "--grpc-web"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"❌ Error al obtener el token SSO: {result.stderr}")
        print("✅ Token SSO obtenido exitosamente.")
        # Extraer el token del archivo de configuración de ArgoCD
        config_path = os.path.expanduser("~/.argocd/config")
        with open(config_path, "r") as config_file:
            config_data = json.load(config_file)
            token = config_data["users"][0]["auth-token"]
            return token
    except Exception as e:
        print(f"❌ Error al obtener el token SSO: {e}")
        raise

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
def get_argocd_apps(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{ARGOCD_API}/applications", headers=headers, verify=False)
        response.raise_for_status()
        apps = response.json().get("items", [])
        print(f"📋 Aplicaciones obtenidas: {len(apps)}")
        return apps
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener aplicaciones desde ArgoCD: {e}")
        return []

# Función para sincronizar una aplicación
def sync_app(app_name, token):
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(
            f"{ARGOCD_API}/applications/{app_name}/sync",
            headers=headers,
            verify=False,
            json={}
        )
        response.raise_for_status()
        print(f"🔄 Sincronización iniciada para {app_name}.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al sincronizar {app_name}: {e}")

# Función para obtener el estado de una aplicación
def get_application_status(app_name, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
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
def refresh_app(app_name, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{ARGOCD_API}/applications/{app_name}?refresh=true",
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        print(f"🔄 Refrescando estado de la aplicación '{app_name}'.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al refrescar la aplicación '{app_name}': {e}")

# Función para pausar una aplicación
def pause_app(app_name, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{ARGOCD_API}/applications/{app_name}/actions/pause",
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        print(f"⏸️ La aplicación '{app_name}' ha sido pausada después de 3 intentos fallidos.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al pausar la aplicación '{app_name}': {e}")

# Función principal para monitorear el estado de las aplicaciones
def main():
    attempts = {}
    notified = set()
    paused_apps = set()

    while True:
        try:
            # Obtener un token SSO antes de cada ciclo
            token = get_sso_token()
            apps = get_argocd_apps(token)

            print("\n📋 Estado actual de las aplicaciones:")
            print("-" * 60)

            for app in apps:
                app_name = app.get("metadata", {}).get("name", "Desconocido")

                # Refrescar el estado de la aplicación antes de verificar
                refresh_app(app_name, token)

                health_status, sync_status = get_application_status(app_name, token)

                # Mostrar información de la aplicación en un recuadro
                print("+" + "-" * 58 + "+")
                print(f"| {'Aplicación':<20} | {'Estado':<15} | {'Intentos':<10} |")
                print("+" + "-" * 58 + "+")
                print(f"| {app_name:<20} | {health_status:<15} | {attempts.get(app_name, 0):<10} |")
                print("+" + "-" * 58 + "+")

                if app_name not in attempts:
                    attempts[app_name] = 0

                if health_status == "Healthy" and sync_status == "Synced":
                    print(f"✅ '{app_name}' está en estado Healthy y Synced.")
                    if app_name in notified or app_name in paused_apps:
                        print(f"📩 Notificando que '{app_name}' volvió a Healthy.")
                        send_slack_notification(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
                        notified.discard(app_name)
                        paused_apps.discard(app_name)
                    attempts[app_name] = 0
                elif app_name in paused_apps:
                    print(f"⏸️ '{app_name}' está pausada. Monitoreando su estado...")
                elif sync_status == "OutOfSync":
                    print(f"⚠️ '{app_name}' está OutOfSync. Intentando sincronizar...")
                    sync_app(app_name, token)
                    attempts[app_name] += 1
                elif health_status in ["Degraded", "Error"]:
                    if attempts[app_name] < 3:
                        print(f"🔄 Intentando recuperar '{app_name}' (Intento {attempts[app_name] + 1}/3)...")
                        sync_app(app_name, token)
                        attempts[app_name] += 1
                    else:
                        if app_name not in notified:
                            print(f"⏸️ '{app_name}' no se pudo recuperar después de 3 intentos. Notificando y pausando...")
                            send_slack_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
                            paused_apps.add(app_name)
                            notified.add(app_name)
                else:
                    print(f"ℹ️ '{app_name}' está en estado desconocido: {health_status}.")

            print("-" * 60)
            time.sleep(60)

        except Exception as e:
            print(f"❌ Error en el ciclo principal: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()