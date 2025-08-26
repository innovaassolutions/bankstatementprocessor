@echo off
echo 🚀 Starting Bank Statement Processor...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found. Please install Docker Compose.
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist "uploads" mkdir uploads
if not exist "output" mkdir output
if not exist "data" mkdir data

REM Build and start the container
echo 🔨 Building and starting container...
docker-compose up --build -d

REM Wait for the service to be ready
echo ⏳ Waiting for service to be ready...
timeout /t 10 /nobreak >nul

REM Check if the service is running
curl -f http://localhost:3005/ >nul 2>&1
if errorlevel 1 (
    echo ❌ Service failed to start. Check logs with: docker-compose logs
    exit /b 1
) else (
    echo ✅ Service is running!
    echo.
    echo 🌐 Open your browser and go to: http://localhost:3005
    echo 📁 Put your PDF files in the 'data' folder
    echo 📊 Results will appear in the 'output' folder
    echo.
    echo To stop the service, run: docker-compose down
)

pause
