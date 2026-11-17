FROM python:3.12-slim
WORKDIR /app
RUN groupadd -g 10001 appgroup && useradd -u 10001 -g appgroup appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py .
USER 10001
EXPOSE 8000
CMD ["python", "worker.py"]
