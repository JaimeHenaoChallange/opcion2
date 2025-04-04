FROM python:3.9

WORKDIR /app

COPY scripts/argocd_monitor.py /app/argocd_monitor.py
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

CMD ["python", "argocd_monitor.py"]
