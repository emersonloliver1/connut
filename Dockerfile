# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

# Configurações do Cloud SQL
ENV CLOUD_SQL_CONNECTION_NAME="connut-7b628:us-central1:sqlconnut"
ENV DB_USER="postgres"
ENV DB_PASS="E98a#@.connut.e"
ENV DB_NAME="postgres"

# Instala as dependências do sistema e o cliente PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Instala o Cloud SQL Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy \
    && chmod +x /usr/local/bin/cloud_sql_proxy

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY CONNUT/requirements.txt .

# Atualiza o pip e instala as dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação
COPY CONNUT/ .

# Cria um usuário não-root para executar a aplicação
RUN adduser --disabled-password --gecos '' appuser

# Muda a propriedade dos arquivos da aplicação para o novo usuário
RUN chown -R appuser:appuser /app

# Muda para o usuário não-root
USER appuser

# Expõe a porta que a aplicação vai usar
EXPOSE 8080

# Comando para executar a aplicação com o Cloud SQL Proxy
CMD cloud_sql_proxy -instances=${CLOUD_SQL_CONNECTION_NAME}=tcp:5432 & \
    gunicorn --bind :$PORT main:app