FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY migrations/ migrations/
COPY config/ config/

RUN pip install --no-cache-dir .

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/jobclass-* /usr/local/bin/
COPY --from=builder /app/src/ src/
COPY --from=builder /app/migrations/ migrations/
COPY --from=builder /app/config/ config/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["jobclass-web", "--host", "0.0.0.0", "--port", "8000"]
