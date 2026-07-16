FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN mkdir -p /data
ENV LOOP_DATABASE_URL=sqlite:////data/loop.db
EXPOSE 7878
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7878/health/live')"
CMD ["uvicorn", "loop_api.main:app", "--host", "0.0.0.0", "--port", "7878"]
