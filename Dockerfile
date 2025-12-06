# Usa una imagen base de Python oficial
FROM python:3.10-slim

# Configuraciones de entorno (mejora el rendimiento y evita buffers)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 1. Instala dependencias del sistema necesarias para Chromium y ChromeDriver
RUN apt-get update \
    && apt-get install -y \
    chromium-driver \
    chromium \
    # Elimina el caché para mantener la imagen pequeña
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Copia los requisitos e instálalos en la ruta principal del sistema Python
#    ESTO SOLUCIONA EL ERROR 'No module named gunicorn'
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 3. Establece el directorio de trabajo para tu aplicación
WORKDIR /usr/src/app

# 4. Copia el resto del código (tu app.py) al directorio de trabajo
COPY . .

# 5. Comando de inicio (Ejecuta gunicorn como un módulo de Python)
#    Nota: Se corrige el objeto Flask a 'app:app'
CMD python -m gunicorn --bind 0.0.0.0:$PORT app:app