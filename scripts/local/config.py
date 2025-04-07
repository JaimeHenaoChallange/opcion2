import os

class Config:
    ARGOCD_API = os.getenv("ARGOCD_API", "http://localhost:8080/api/v1")
    ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN", "your-default-token")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/default/webhook")

    @staticmethod
    def validate():
        if not Config.ARGOCD_API or not Config.ARGOCD_TOKEN or not Config.SLACK_WEBHOOK_URL:
            raise ValueError("Missing required configuration. Please set ARGOCD_API, ARGOCD_TOKEN, and SLACK_WEBHOOK_URL.")
