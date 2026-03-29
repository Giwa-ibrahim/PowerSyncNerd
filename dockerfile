# Use an official Python multi-stage image to keep it lean
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system dependencies if required for crawlers (e.g., libraries for Playwright/Selenium if used)
# RUN apt-get update && apt-get install -y --no-install-recommends ...

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container
COPY . .

# Expose port 8090 for FastAPI
EXPOSE 8090

# Command to act as web server and scheduler together
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8090"]
