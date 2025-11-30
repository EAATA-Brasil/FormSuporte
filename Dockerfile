# Use a imagem oficial do Python como base
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /usr/src/app

# Define variáveis de ambiente para o Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema necessárias para algumas bibliotecas Python (como mysqlclient e pillow)
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

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Define o comando padrão para rodar a aplicação com Gunicorn (servidor de produção)
# O projeto parece usar Gunicorn (visto em requirements.txt) e o arquivo settings.py deve estar em Form_Suporte/settings.py
# Assumindo que o módulo WSGI é Form_Suporte.wsgi
CMD ["python", "manage.py","runserver", "0.0.0.0:8000"]
