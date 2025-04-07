import requests

ARGOCD_API = "https://localhost:8080/api/v1/applications"  # Usar localhost con port-forward
ARGOCD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NDM4MTYyMjEsImlhdCI6MTc0MzgxNjIyMSwianRpIjoiMjk1Y2NjNTItOTNhMS00ZDRjLWEzZmMtMGU2YjUxYmEyYjJjIn0.sI19G2ixaP9u9yAr0HupxeZC-ALGAWwVLnfp7eDorfU"

def test_connectivity():
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    try:
        response = requests.get(ARGOCD_API, headers=headers, verify=False)
        response.raise_for_status()
        print("✅ Successfully connected to ArgoCD API")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to ArgoCD API: {e}")

if __name__ == "__main__":
    test_connectivity()
