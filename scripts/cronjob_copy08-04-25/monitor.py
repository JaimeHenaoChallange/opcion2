import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 El script monitor.py se está ejecutando...")  # Mensaje de depuración

from argocd_client import ArgoCDClient  # Cambiar a importación relativa
from slack_notifier import SlackNotifier  # Cambiar a importación relativa
import time

# Configurar un tiempo de espera global para las solicitudes HTTP
REQUEST_TIMEOUT = 10  # Tiempo de espera en segundos

def main():
    print("🔧 Entrando en la función principal...")  # Mensaje de depuración
    attempts = {}
    notified = set()
    paused_apps = set()
    problematic_apps = set()

    while True:
        try:
            print("🔍 Iniciando monitoreo de aplicaciones...")
            apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)

            if not apps:
                print("⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.")
                time.sleep(30)
                continue

            print("\n📋 Estado actual de las aplicaciones:")
            print("-" * 60)

            for app in apps:
                app_name = app.get("metadata", {}).get("name", "Desconocido")
                print(f"🔄 Procesando la aplicación: {app_name}")  # Mensaje de depuración
                ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)
                health_status, sync_status = ArgoCDClient.get_application_status(app_name, timeout=REQUEST_TIMEOUT)

                # Mostrar información de la aplicación en un recuadro
                print("+" + "-" * 58 + "+")
                print(f"| {'Aplicación':<20} | {'Estado':<15} | {'Intentos':<10} |")
                print("+" + "-" * 58 + "+")
                print(f"| {app_name:<20} | {health_status:<15} | {attempts.get(app_name, 0):<10} |")
                print("+" + "-" * 58 + "+")
                print()  # Agregar un espacio entre recuadros

                if app_name not in attempts:
                    attempts[app_name] = 0

                if health_status == "Healthy" and sync_status == "Synced":
                    print(f"✅ '{app_name}' está en estado Healthy y Synced.")
                    print()  # Agregar un espacio en blanco
                    if app_name in notified or app_name in paused_apps or app_name in problematic_apps:
                        print(f"📩 Notificando que '{app_name}' volvió a Healthy.")
                        SlackNotifier.send_notification(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
                        notified.discard(app_name)
                        paused_apps.discard(app_name)
                        problematic_apps.discard(app_name)
                    attempts[app_name] = 0
                elif app_name in paused_apps:
                    print(f"⏸️ '{app_name}' está pausada. Monitoreando su estado...")
                elif sync_status == "OutOfSync":
                    print(f"⚠️ '{app_name}' está OutOfSync. Intentando sincronizar...")
                    ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                    attempts[app_name] += 1
                elif health_status in ["Degraded", "Error"]:
                    problematic_apps.add(app_name)
                    if attempts[app_name] < 3:
                        print(f"🔄 Intentando recuperar '{app_name}' (Intento {attempts[app_name] + 1}/3)...")
                        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                        attempts[app_name] += 1
                    else:
                        if app_name not in notified:
                            print(f"⏸️ '{app_name}' no se pudo recuperar después de 3 intentos. Notificando y pausando...")
                            SlackNotifier.send_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
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