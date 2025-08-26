#!/bin/bash

echo "🚀 Starting Bank Statement Processor..."
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads output data

# Build and start the container
echo "🔨 Building and starting container..."
docker-compose up --build -d

# Wait for the service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

# Check if the service is running
if curl -f http://localhost:3005/ > /dev/null 2>&1; then
    echo "✅ Service is running!"
    echo
    echo "🌐 Open your browser and go to: http://localhost:3005"
    echo "📁 Put your PDF files in the 'data' folder"
    echo "📊 Results will appear in the 'output' folder"
    echo
    echo "To stop the service, run: docker-compose down"
else
    echo "❌ Service failed to start. Check logs with: docker-compose logs"
    exit 1
fi
