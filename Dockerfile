FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
    libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 xdg-utils libgbm-dev \
    libgtk-3-0 libxshmfence1 libxss1 libxtst6 && \
    apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install --with-deps chromium

COPY app.py .

EXPOSE 8080
CMD ["python", "app.py"]

