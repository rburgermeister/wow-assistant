FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App code
COPY bot.py /app/bot.py

# Writable data dir (will be mounted as a volume)
RUN mkdir -p /app/data/voice && chown -R appuser:appuser /app

USER appuser

CMD ["python", "bot.py"]
