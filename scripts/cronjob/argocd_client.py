import requests

# Define the ArgoCD API endpoint and headers
ARGOCD_API = "https://192.168.49.2:30759"  # Solo la URL base del API
ARGOCD_APPLICATIONS_ENDPOINT = "/api/v1/applications"  # Endpoint correcto

def fetch_applications(token):
    """Fetch the list of applications from the ArgoCD API."""
    headers = {
        "Authorization": f"Bearer {token}"  # Autenticación con el token de ArgoCD
    }
    try:
        # Realiza una solicitud GET al endpoint de aplicaciones
        response = requests.get(f"{ARGOCD_API}{ARGOCD_APPLICATIONS_ENDPOINT}", headers=headers, verify=False)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un código de error HTTP
        return response.json()  # Devuelve la respuesta en formato JSON
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"❌ Other error occurred: {err}")
    return None
