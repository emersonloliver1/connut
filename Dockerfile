# Use uma imagem base oficial do Python
FROM python:3.11-slim-bullseye

# Define o diretório de trabalho no container
WORKDIR /app

# Instala as dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro
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

# Comando para rodar a aplicação
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 120 main:app
