# Use uma imagem base oficial do Python
FROM python:3.9-slim-buster

# Define o diretório de trabalho no container
WORKDIR /app

# Instala as dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    python3-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação
COPY . .

# Cria a pasta instance se ela não existir
RUN mkdir -p instance

# Expõe a porta que a aplicação vai usar
EXPOSE 8080

# Define as variáveis de ambiente
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PORT=8080
ENV GOOGLE_CLOUD_RUN=True

# Comando para rodar a aplicação
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
