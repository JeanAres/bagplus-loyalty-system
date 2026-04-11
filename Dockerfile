FROM python:3.11-slim

# Metadados
LABEL maintainer="jean06soares@gmail.com"
LABEL description="Bag+ Sistema de Fidelização Sustentável"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY services/backend/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY services/backend/ .

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
