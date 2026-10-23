# API Gestão de visitantes (ADR-015). Contexto de build: raiz do repositório.
#   docker build -f backend/Dockerfile --target api  -t gestao-visitantes-api .
#   docker build -f backend/Dockerfile --target test -t gestao-visitantes-tests .

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY backend/app ./app
COPY backend/seed.py ./seed.py

# ---------- testes: mesma imagem + tests/ e pytest.ini ----------
FROM base AS test
WORKDIR /repo
COPY pytest.ini ./pytest.ini
COPY tests ./tests
RUN ln -s /app /repo/backend
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider"]

# ---------- execução ----------
FROM base AS api
# Banco em volume; nada de dado dentro da imagem (ADR-005).
ENV DATABASE_URL=sqlite:////data/visitantes.db \
    CORS_ORIGINS=http://localhost:8080
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app:app /data
USER app
# PORT: o Render define a porta por variável; localmente/compose usa 8000.
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health', timeout=2).status == 200 else 1)"
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
