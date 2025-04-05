from argocd_client import fetch_applications  # Importa la función desde argocd_client.py

# Define el token de ArgoCD
ARGOCD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDM4MTYyMjEsImlhdCI6MTc0MzgxNjIyMSwianRpIjoiMjk1Y2NjNTItOTNhMS00ZDRjLWEzZmMtMGU2YjUxYmEyYjJjIn0.sI19G2ixaP9u9yAr0HupxeZC-ALGAWwVLnfp7eDorfU"  # Reemplaza con el nuevo token

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
