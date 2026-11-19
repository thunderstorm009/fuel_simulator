FROM python:3.12.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system app && useradd --system --gid app --home-dir /app app
COPY backend/shared/core ./core
COPY backend/worker ./worker
USER app
EXPOSE 8102
CMD ["uvicorn", "worker.main:app", "--host", "0.0.0.0", "--port", "8102"]
