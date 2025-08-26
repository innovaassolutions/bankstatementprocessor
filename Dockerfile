# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set metadata labels for versioning
LABEL maintainer="innovaassolutions"
LABEL version="1.0.0"
LABEL description="Bank Statement PDF Processor with Web UI"
LABEL org.opencontainers.image.source="https://github.com/innovaassolutions/bankstatementprocessor"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output data

# Create templates directory if it doesn't exist
RUN mkdir -p templates

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "app.py"]
