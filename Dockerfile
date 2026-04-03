FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx

COPY server.py .

EXPOSE 8765

# keys.txt must be mounted at runtime: -v /path/to/keys.txt:/app/keys.txt
CMD ["python3", "server.py"]
