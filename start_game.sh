#!/bin/bash

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use"
        return 1
    fi
    return 0
}

# Function to wait for a service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service_name to be ready..."
    while ! nc -z localhost $port; do
        if [ $attempt -eq $max_attempts ]; then
            echo "$service_name failed to start"
            exit 1
        fi
        attempt=$((attempt+1))
        sleep 1
    done
    echo "$service_name is ready!"
}

# Check if required ports are available
check_port 11434 || exit 1  # Ollama
check_port 1920 || exit 1   # TTS
check_port 8000 || exit 1   # STT

# Start Ollama in the background
echo "Starting Ollama..."
ollama serve &
OLLAMA_PID=$!
wait_for_service 11434 "Ollama"

# Start TTS server in the background
echo "Starting TTS server..."
cd stt_tts_api
uvicorn tts_engine:app --host 0.0.0.0 --port 1920 &
TTS_PID=$!
wait_for_service 1920 "TTS server"

# Start STT server in the background
echo "Starting STT server..."
uvicorn stt_engine:app --host 0.0.0.0 --port 8000 &
STT_PID=$!
wait_for_service 8000 "STT server"

# Return to main directory
cd ..

# Start the game
echo "Starting the game..."
cd src
python main.py

# Cleanup function
cleanup() {
    echo "Shutting down services..."
    kill $OLLAMA_PID 2>/dev/null
    kill $TTS_PID 2>/dev/null
    kill $STT_PID 2>/dev/null
    exit 0
}

# Set up cleanup on script termination
trap cleanup EXIT SIGINT SIGTERM

# Wait for the game to exit
wait