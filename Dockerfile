# Usa una imagen base de Python oficial
FROM python:3.10-slim

# Configuraciones de entorno (mejora el rendimiento)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependencias del sistema necesarias para Chromium y Xvfb
RUN apt-get update \
    && apt-get install -y \
    chromium-driver \
    chromium \
    # Elimina el caché para mantener la imagen pequeña
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crea un directorio para la aplicación
WORKDIR /usr/src/app

# Copia los archivos de requisitos e instálalos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación (incluye app.py)
COPY . .

# Define el comando de inicio para Gunicorn (servidor de producción)
# 'app' es el módulo (app.py), y ':app' es el objeto Flask dentro del módulo
# LÍNEA ANTIGUA (que dio error)
# LÍNEA CORREGIDA (Ejecuta gunicorn como un módulo de Python)
CMD python -m gunicorn --bind 0.0.0.0:$PORT app:app