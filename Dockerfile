FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
RUN python -m pip install --upgrade pip && \
    pip install fastapi "uvicorn[standard]" python-multipart passlib[bcrypt] pyjwt \
                boto3 segno sqlmodel pydantic-settings httpx email-validator jinja2

# ⬇️ penting: copy semua folder yang dipakai runtime
COPY app ./app
COPY templates ./templates
COPY static ./static

EXPOSE 8080
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
