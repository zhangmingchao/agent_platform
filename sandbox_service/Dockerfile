FROM python:3.12-slim

WORKDIR /app
COPY sandbox_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY sandbox_service /app/sandbox_service

EXPOSE 20002
CMD ["uvicorn", "sandbox_service.app:app", "--host", "0.0.0.0", "--port", "20002"]
