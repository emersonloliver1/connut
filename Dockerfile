# Use uma imagem base oficial do Python
FROM python:3.11-slim-bullseye

# Define o diretório de trabalho no container
WORKDIR /app

# Instala as dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    mime-support \
    pkg-config \
    libcairo2-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação
COPY . .

# Cria a pasta instance se ela não existir
RUN mkdir -p instance

# Configurações do Supabase como variáveis de ambiente
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_KEY=${SUPABASE_KEY}
ENV SUPABASE_DB_USER=${SUPABASE_DB_USER}
ENV SUPABASE_DB_PASSWORD=${SUPABASE_DB_PASSWORD}
ENV SUPABASE_DB_HOST=${SUPABASE_DB_HOST}
ENV SUPABASE_DB_NAME=${SUPABASE_DB_NAME}
ENV SUPABASE_DB_PORT=${SUPABASE_DB_PORT}

# Configurações do Flask
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PORT=8080
ENV SECRET_KEY=${SECRET_KEY}

# Configuração para o Cloud Run
ENV HOST=0.0.0.0

# Comando para rodar a aplicação
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "main:app"
