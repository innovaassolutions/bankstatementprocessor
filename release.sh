#!/bin/bash

# Release Script for Bank Statement Processor
# Automates the process of releasing new versions to Docker Hub

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME="innovaasdev"
IMAGE_NAME="bankstatementprocessor"
GITHUB_REPO="innovaassolutions/bankstatementprocessor"
DOCKER_REPO="innovaasdev/bankstatementprocessor"

echo -e "${BLUE}🚀 Bank Statement Processor Release Script${NC}"
echo "================================================"

# Check if version argument provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: Please provide a version number${NC}"
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.1.0"
    exit 1
fi

VERSION=$1

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}❌ Error: Version must be in format X.Y.Z (e.g., 1.0.0)${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Release Details:${NC}"
echo "Version: $VERSION"
echo "Docker Image: $DOCKER_USERNAME/$IMAGE_NAME"
echo "GitHub Repo: $GITHUB_REPO"
echo ""

# Confirm release
read -p "Do you want to proceed with releasing version $VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Release cancelled${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 Step 1: Updating version across project files...${NC}"
python3 update_version.py $VERSION

echo -e "${BLUE}🔄 Step 2: Building Docker image...${NC}"
docker build -t $DOCKER_REPO:$VERSION .
docker tag $DOCKER_REPO:$VERSION $DOCKER_REPO:latest

echo -e "${BLUE}🔄 Step 3: Testing Docker image...${NC}"
# Start container in background
CONTAINER_ID=$(docker run -d -p 3005:5000 $DOCKER_REPO:$VERSION)

# Wait for container to start
echo "Waiting for container to start..."
sleep 10

# Test health check
if curl -f http://localhost:3005/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Container is running and responding${NC}"
else
    echo -e "${RED}❌ Container health check failed${NC}"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# Stop and remove test container
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo -e "${BLUE}🔄 Step 4: Pushing to Docker Hub...${NC}"
docker push $DOCKER_REPO:$VERSION
docker push $DOCKER_REPO:latest

echo -e "${BLUE}🔄 Step 5: Creating Git release...${NC}"
# Add all changes
git add .

# Commit version bump
git commit -m "Bump version to $VERSION"

# Create and push tag
git tag -a v$VERSION -m "Release version $VERSION"
git push origin main --tags

echo -e "${BLUE}🔄 Step 6: Creating GitHub release notes...${NC}"
echo -e "${YELLOW}📝 Please create a GitHub release manually:${NC}"
echo "1. Go to: https://github.com/$GITHUB_REPO/releases"
echo "2. Click 'Create a new release'"
echo "3. Tag: v$VERSION"
echo "4. Title: Release v$VERSION"
echo "5. Description: Include changelog and Docker pull instructions"
echo ""

echo -e "${GREEN}🎉 Release $VERSION completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 What users need to do to get updates:${NC}"
echo "1. Pull latest version:"
echo "   docker pull $DOCKER_REPO:latest"
echo ""
echo "2. Or pull specific version:"
echo "   docker pull $DOCKER_REPO:$VERSION"
echo ""
echo "3. Update their docker-compose.yml or run command:"
echo "   docker run -p 3005:5000 $DOCKER_REPO:$VERSION"
echo ""
echo -e "${YELLOW}💡 Pro tip: Users can set up automatic updates by:${NC}"
echo "1. Using 'latest' tag in their scripts"
echo "2. Running 'docker pull' before 'docker run'"
echo "3. Setting up cron jobs to check for updates"
echo ""
echo -e "${GREEN}✅ Release process complete!${NC}"
