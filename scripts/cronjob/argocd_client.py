import requests

# Define the ArgoCD API endpoint and headers
ARGOCD_API = "https://argocd-server.argocd.svc.cluster.local:443"
ARGOCD_APPLICATIONS_ENDPOINT = "/api/v1/applications"

def fetch_applications(token):
    """Fetch the list of applications from the ArgoCD API."""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(f"{ARGOCD_API}{ARGOCD_APPLICATIONS_ENDPOINT}", headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"❌ Other error occurred: {err}")
    return None
