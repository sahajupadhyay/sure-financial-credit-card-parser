#!/bin/bash

# Sure Financial Credit Card Parser - Demo Script
# Run this script to demonstrate the complete solution

echo "🚀 Sure Financial Credit Card Parser - Live Demo"
echo "================================================"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    exit 1
fi

echo "📦 Building Docker image..."
docker build -t sure-parser . --quiet

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

echo ""
echo "🚀 Starting web application..."
echo "   URL: http://localhost:5001"
echo "   Press Ctrl+C to stop"
echo ""

# Stop any existing container
docker stop sure-parser-demo 2>/dev/null
docker rm sure-parser-demo 2>/dev/null

# Run the container
docker run --name sure-parser-demo -p 5001:5001 sure-parser