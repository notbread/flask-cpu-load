FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

ENV PORT=5000
ENV FIB_ITERATIONS=500000

CMD ["python", "app.py"]
