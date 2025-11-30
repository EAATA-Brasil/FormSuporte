# Usa imagem oficial Python
FROM python:3.11-slim

# Diretório base para dependências (não é montado pelo volume)
WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências de sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        mariadb-client \
        libgobject-2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libcairo2 \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Criar pasta para código-fonte (essa SIM será montada pelo volume)
RUN mkdir /usr/src/app/src

# Copiar seu código para dentro da pasta src
COPY . /usr/src/app/src

# Rodar Django
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
