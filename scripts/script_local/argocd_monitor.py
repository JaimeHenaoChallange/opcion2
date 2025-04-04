import requests
import time
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Suprime las advertencias de SSL

ARGOCD_API = "https://localhost:8080/api/v1"
ARGOCD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDM3MTcwMjUsImlhdCI6MTc0MzcxNzAyNSwianRpIjoiMDBjZjVhYzktYmRjMy00ZTE5LWE4NzEtMWNiOTUwODRiMDUwIn0.ZgZIsd-ktq1UJ-9IumqLNgXe_JFDKagyECyU91JGBd4"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def get_applications():
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    print("\n🔍 Obteniendo aplicaciones desde ArgoCD...")
    response = requests.get(f"{ARGOCD_API}/applications", headers=headers, verify=False)
    print(f"📡 Código de respuesta: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error al obtener aplicaciones. Código de estado: {response.status_code}")
        print(f"Detalles: {response.text}")
        return []
    try:
        apps = response.json().get("items", [])
        print(f"✅ Aplicaciones obtenidas: {len(apps)}")
        return apps
    except json.JSONDecodeError:
        print("❌ Error al decodificar la respuesta JSON.")
        return []

def retry_deploy(app_name, attempts):
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    for attempt in range(3):
        print(f"🔄 Intentando desplegar '{app_name}' (Intento {attempt + 1}/3)...")
        requests.post(f"{ARGOCD_API}/applications/{app_name}/sync", headers=headers, verify=False)
        time.sleep(10)  # Espera para que la sincronización se estabilice
        app_status, sync_status = get_application_status(app_name)
        if app_status == "Healthy" and sync_status == "Synced":
            print(f"✅ La aplicación '{app_name}' ahora está en estado Healthy y Synced.")
            return True
    print(f"❌ La aplicación '{app_name}' no se pudo recuperar después de 3 intentos.")
    return False

def get_application_status(app_name):
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    response = requests.get(f"{ARGOCD_API}/applications/{app_name}", headers=headers, verify=False)
    app_info = response.json()
    health_status = app_info.get("status", {}).get("health", {}).get("status", "Unknown")
    sync_status = app_info.get("status", {}).get("sync", {}).get("status", "Unknown")
    return health_status, sync_status

def notify_slack(app_name, status, attempts):
    message = {
        "text": f"⚠️ *Estado crítico de la aplicación:*\n\n"
                f"Aplicación: `{app_name}`\n"
                f"Estado: `{status}`\n"
                f"Intentos fallidos: `{attempts}`\n\n"
                f"La aplicación no se pudo recuperar después de 3 intentos."
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()
        print(f"📩 Notificación enviada a Slack para '{app_name}' en estado '{status}'.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al enviar notificación a Slack: {e}")

def main():
    attempts = {}
    notified = set()  # Almacena las aplicaciones que ya han sido notificadas

    while True:
        apps = get_applications()
        print("\n📋 Estado actual de las aplicaciones:")
        print(f"{'Aplicación':<20} {'Estado':<15} {'Intentos':<10}")
        print("-" * 50)

        for app in apps:
            app_name = app["metadata"]["name"]
            health_status, sync_status = get_application_status(app_name)
            print(f"{app_name:<20} {health_status:<15} {attempts.get(app_name, 0):<10}")

            # Inicializa los intentos para cada aplicación si no existen
            if app_name not in attempts:
                attempts[app_name] = 0

            if health_status == "Healthy" and sync_status == "Synced":
                print(f"✅ '{app_name}' está en estado Healthy y Synced.")
                attempts[app_name] = 0  # Reinicia los intentos
                notified.discard(app_name)  # Elimina de la lista de notificados
            elif sync_status == "OutOfSync":
                print(f"⚠️ '{app_name}' está OutOfSync. Intentando sincronizar...")
                retry_deploy(app_name, attempts[app_name])
            elif health_status in ["Degraded", "Error"]:
                if attempts[app_name] < 3:
                    print(f"🔄 Intentando recuperar '{app_name}' (Intento {attempts[app_name] + 1}/3)...")
                    if retry_deploy(app_name, attempts[app_name]):
                        attempts[app_name] = 0  # Reinicia los intentos si se recupera
                        notified.discard(app_name)
                    else:
                        attempts[app_name] += 1
                else:
                    if app_name not in notified:
                        print(f"⏸️ '{app_name}' no se pudo recuperar después de 3 intentos. Notificando...")
                        notify_slack(app_name, health_status, attempts[app_name])
                        notified.add(app_name)  # Marca como notificada
            else:
                print(f"ℹ️ '{app_name}' está en estado desconocido: {health_status}.")

        print("-" * 50)
        time.sleep(60)

if __name__ == "__main__":
    main()
