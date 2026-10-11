FROM ghcr.io/astral-sh/uv:0.11.15 AS uv
FROM python:3.11.15-slim
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY serving.py ./
COPY site ./site
RUN useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"]
CMD ["/app/.venv/bin/uvicorn", "serving:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
