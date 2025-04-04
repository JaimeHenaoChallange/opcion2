# ArgoCD Monitor

## Overview

The ArgoCD Monitor is a Kubernetes CronJob designed to monitor ArgoCD applications, synchronize their states, and send notifications to a Slack channel in case of issues. It uses the ArgoCD API to fetch application statuses and the Slack Webhook API to send alerts.

---

## Project Structure

Below is the structure of the project:

```
/workspaces/monitor-2/
├── scripts/
│   ├── cronjob/
│   │   ├── argocd-application.yaml       # ArgoCD Application resource
│   │   ├── clusterrole.yaml              # Role for permissions
│   │   ├── clusterrolebinding.yaml       # RoleBinding for ServiceAccount
│   │   ├── argocd-monitor-cronjob.yaml   # CronJob definition
│   │   ├── argocd-token-secret.yaml      # Kubernetes Secret for ArgoCD token
│   └── docker-compose.yml                # Docker Compose configuration
├── README.md                              # Documentation
```

---

## Solution Architecture

Below is a high-level diagram of the solution:

```
+-------------------+       +-------------------+
|                   |       |                   |
|  Kubernetes Cron  |       |   ArgoCD Server   |
|      Job          |       |                   |
|                   |       |                   |
|  +-------------+  |       |  +-------------+  |
|  | monitor.py  |  |       |  | ArgoCD API  |  |
|  +-------------+  |       |  +-------------+  |
|                   |       |                   |
+-------------------+       +-------------------+
          |                           |
          |                           |
          +---------------------------+
                      HTTPS
                       |
                       v
+------------------------------------------------+
|                                                |
|                Slack Webhook                   |
|                                                |
+------------------------------------------------+
```

### Explanation

1. **Kubernetes CronJob**:
   - Periodically executes the `monitor.py` script.
   - Fetches application statuses from the ArgoCD API.

2. **ArgoCD Server**:
   - Provides the API endpoint for fetching application statuses.
   - Requires authentication using the token stored in the Kubernetes Secret.

3. **Slack Webhook**:
   - Receives notifications from the `monitor.py` script.
   - Alerts are sent to a configured Slack channel.

---

## Features

- Monitors ArgoCD applications for health and synchronization status.
- Automatically synchronizes applications that are out of sync.
- Sends Slack notifications for degraded or error states.
- Configurable via environment variables and Kubernetes secrets.

---

## Prerequisites

- A running Kubernetes cluster with ArgoCD installed.
- `kubectl` and `argocd` CLI tools installed locally.
- A Slack Webhook URL for notifications.
- A valid ArgoCD API token stored in a Kubernetes secret.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JaimeHenaoChallange/opcion2.git
   cd opcion2
   ```

2. Apply the Kubernetes manifests:
   ```bash
   kubectl apply -f /workspaces/monitor-2/scripts/cronjob/
   ```

3. Verify that the CronJob is running:
   ```bash
   kubectl get cronjob -n poc
   ```

---

## Configuration

### Environment Variables

The following environment variables are used to configure the monitor:

- `ARGOCD_API`: The ArgoCD API endpoint (e.g., `https://argocd-server.argocd.svc.cluster.local:443`).
- `ARGOCD_TOKEN`: The ArgoCD API token stored in the Kubernetes secret `argocd-token-secret`.
- `SLACK_WEBHOOK_URL`: The Slack Webhook URL for sending notifications.

### Secrets

The ArgoCD API token must be stored in a Kubernetes secret named `argocd-token-secret` in the `poc` namespace. Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: argocd-token-secret
  namespace: poc
type: Opaque
data:
  token: <base64-encoded-token>
```

---

## Usage

1. Monitor logs of the CronJob:
   ```bash
   kubectl logs -l app.kubernetes.io/name=argocd-monitor -n poc
   ```

2. Test connectivity to the ArgoCD API:
   ```bash
   kubectl run -it --rm debug --image=alpine --restart=Never -n poc -- sh
   apk add curl
   curl -k https://argocd-server.argocd.svc.cluster.local:443/api/v1/applications
   ```

3. Sync the application in ArgoCD:
   ```bash
   argocd app sync argocd-monitor
   ```

---

## Troubleshooting

- **Connection Refused**: Ensure the `ARGOCD_API` URL is correct and accessible from the namespace `poc`.
- **Invalid Token**: Verify the `argocd-token-secret` contains a valid token.
- **Slack Notifications Not Sent**: Check the `SLACK_WEBHOOK_URL` for correctness.

---

## License

This project is licensed under the MIT License.
