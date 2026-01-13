FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

COPY frontend ./frontend
RUN cd frontend && npm run build

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

RUN python -m playwright install chromium

COPY backend ./backend

EXPOSE 8000

ENV DOCKER_BUILD=true

CMD ["python", "backend/start.py"]
