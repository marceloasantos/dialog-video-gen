FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

FROM python:3.12-slim
WORKDIR /app

# pydub requires ffmpeg at runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg fontconfig wget \
    && mkdir -p /usr/share/fonts/truetype/bangers \
    && wget -O /usr/share/fonts/truetype/bangers/Bangers-Regular.ttf https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "src.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-server-header", "--no-date-header"]
