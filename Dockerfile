FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=app.main:create_app \
    FLASK_ENV=development

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretório de uploads
RUN mkdir -p uploads

# Expõe porta
EXPOSE 5000

# Comando para iniciar a aplicação com Flask
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]