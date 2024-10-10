# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Instala as dependências do sistema necessárias para o Cairo e WeasyPrint
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libpq-dev \
    build-essential

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

# Remove os comandos de inicialização do banco de dados
# Estes comandos devem ser executados em tempo de execução, não durante a construção da imagem
# RUN flask db init
# RUN flask db migrate
# RUN flask db upgrade

# Comando para rodar a aplicação
CMD ["python", "main.py"]