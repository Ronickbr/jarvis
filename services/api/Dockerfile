FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY services/api ./services/api
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 jarvis && mkdir -p /app/data && chown -R jarvis:jarvis /app
USER jarvis

EXPOSE 8000
CMD ["uvicorn", "jarvis_api.main:app", "--app-dir", "services/api", "--host", "0.0.0.0", "--port", "8000"]
