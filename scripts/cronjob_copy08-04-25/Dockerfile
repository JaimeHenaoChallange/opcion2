FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos necesarios
COPY . /app

# Copiar el archivo de entrada
COPY entrypoint.sh /app/entrypoint.sh

# Asegurarse de que el archivo de entrada sea ejecutable
RUN chmod +x /app/entrypoint.sh

# Instalar las dependencias
RUN pip install --no-cache-dir -r /app/requirements.txt

# Configurar Python para que no almacene en búfer la salida
ENV PYTHONUNBUFFERED=1

# Usar el archivo de entrada como comando de inicio
ENTRYPOINT ["/app/entrypoint.sh"]
