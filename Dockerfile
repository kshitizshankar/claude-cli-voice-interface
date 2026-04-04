FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx

COPY server.py .

EXPOSE 8765

# Pass keys via --env-file .env or -e MISTRAL_API_KEYS=key1,key2
CMD ["python3", "server.py"]
