# Use Python 3.12-slim for maximum stability and lower RAM footprint
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system dependencies for Chrome/Selenium (optimized for size)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    --no-install-recommends \
    && mkdir -p /etc/apt/keyrings \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container
COPY . .

# Expose port (Default for Render FastAPI)
EXPOSE 10000

# 🧠 CRITICAL RAM WIN: Single worker prevents double-loading the app
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1"]
