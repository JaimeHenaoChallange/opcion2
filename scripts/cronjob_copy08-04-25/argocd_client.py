import requests

# Define the ArgoCD API endpoint and headers
ARGOCD_API = "https://argocd-server.argocd.svc.cluster.local:443"  # Base URL
ARGOCD_APPLICATIONS_ENDPOINT = "/api/v1/applications"  # Endpoint completo

def fetch_applications(token):
    """Fetch the list of applications from the ArgoCD API."""
    headers = {
        "Authorization": f"Bearer {token}"  # Autenticación con el token de ArgoCD
    }
    try:
        # Realiza una solicitud GET al endpoint de aplicaciones
        response = requests.get(f"{ARGOCD_API}{ARGOCD_APPLICATIONS_ENDPOINT}", headers=headers, verify=False, timeout=10)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un código de error HTTP
        return response.json()  # Devuelve la respuesta en formato JSON
    except requests.exceptions.Timeout:
        print("❌ Timeout: No se pudo conectar al API de ArgoCD.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    return None
