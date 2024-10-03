# Use uma imagem base oficial do Python
FROM python:3.9-slim

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Atualiza o pip e instala as dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação
COPY . .

# Cria um usuário não-root para executar a aplicação
RUN adduser --disabled-password --gecos '' appuser

# Muda a propriedade dos arquivos da aplicação para o novo usuário
RUN chown -R appuser:appuser /app

# Muda para o usuário não-root
USER appuser

# Expõe a porta que a aplicação vai usar
EXPOSE 8080

# Comando para executar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]