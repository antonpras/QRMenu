FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml .
RUN python -m pip install --upgrade pip && \
    pip install fastapi "uvicorn[standard]" python-multipart passlib[bcrypt] pyjwt \
                boto3 segno sqlmodel pydantic-settings httpx email-validator jinja2
COPY app ./app
EXPOSE 7860
CMD ["bash","-lc","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
