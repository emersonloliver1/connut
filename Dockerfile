# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
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

# Inicializa o banco de dados
RUN flask db init
RUN flask db migrate
RUN flask db upgrade

# Comando para rodar a aplicação
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app