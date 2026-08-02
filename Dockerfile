FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Site Monitor" \
      org.opencontainers.image.description="Lightweight HTTP endpoint monitoring application built with FastAPI" \
      org.opencontainers.image.source="https://github.com/mstrugarevic1/aws-ecs-site-monitor"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /install /usr/local
COPY app ./app
COPY samples ./samples

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()"

CMD ["python", "-m", "app.api.main"]
