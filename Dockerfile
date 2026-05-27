FROM python:3.11-slim

WORKDIR /app

# 1. Le decimos a Docker que entre en la subcarpeta para copiar el requirements
COPY segundo-cerebro/requirements.txt .

# 2. Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiamos el resto de los archivos (app.py, templates, etc.) dentro del contenedor
COPY segundo-cerebro/ .

EXPOSE 10000

# 4. Arrancamos la app. Como tu archivo es app.py, cambiamos "main:app" por "app:app"
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]