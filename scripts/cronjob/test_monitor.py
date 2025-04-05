from argocd_client import fetch_applications  # Importa la función desde argocd_client.py

# Define el token de ArgoCD
ARGOCD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDM3MTcwMjUsImlhdCI6MTc0MzcxNzAyNSwianRpIjoiMDBjZjVhYzktYmRjMy00ZTE5LWE4NzEtMWNiOTUwODRiMDUwIn0.ZgZIsd-ktq1UJ-9IumqLNgXe_JFDKagyECyU91JGBd4"  # Reemplaza con el token válido

def monitor_applications():
    """Monitor the health and sync status of ArgoCD applications."""
    # Llama a la función fetch_applications para obtener la lista de aplicaciones
    applications = fetch_applications(ARGOCD_TOKEN)
    if applications:
        for app in applications.get("items", []):
            app_name = app["metadata"]["name"]
            app_status = app["status"]["health"]["status"]
            app_sync_status = app["status"]["sync"]["status"]
            print(f"🔍 Application: {app_name}, Health: {app_status}, Sync: {app_sync_status}")
            if app_status != "Healthy" or app_sync_status != "Synced":
                print(f"⚠️ Application {app_name} is not in a healthy or synced state!")
    else:
        print("❌ Failed to fetch applications.")

if __name__ == "__main__":
    print("🔧 Starting ArgoCD Monitor...")
    monitor_applications()
