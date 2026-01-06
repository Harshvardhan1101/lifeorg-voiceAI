#!/bin/bash

# Voice Pipeline Agent Control Script

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${BLUE}Voice Pipeline Agent Control Script${NC}"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start      - Start the voice pipeline agent container"
    echo "  stop       - Stop the container"
    echo "  restart    - Restart the container"
    echo "  logs       - Show container logs (use Ctrl+C to exit)"
    echo "  status     - Show container status"
    echo "  rebuild    - Rebuild the Docker image"
    echo "  debug      - Run interactive debug shell inside the container"
    echo "  clean      - Remove the container and image"
    echo "  help       - Show this help"
    echo ""
}

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Container and image names
CONTAINER_NAME="voice-pipeline-agent"
IMAGE_NAME="voice-pipeline-agent:slim-optimized"
DOCKERFILE="Dockerfile.distroless"

# Function to start the container
start_container() {
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo -e "${BLUE}Container already exists. Starting it...${NC}"
        docker start $CONTAINER_NAME
    else
        echo -e "${BLUE}Creating and starting container...${NC}"
        docker run -d --name $CONTAINER_NAME \
            --env-file .env.local \
            -v voice_model_cache:/app/.cache \
            $IMAGE_NAME
    fi
    
    # Check if container started successfully
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}Container started successfully!${NC}"
    else
        echo -e "${RED}Failed to start container. Check logs for details.${NC}"
        docker logs $CONTAINER_NAME
    fi
}

# Function to stop the container
stop_container() {
    echo -e "${BLUE}Stopping container...${NC}"
    if docker ps | grep -q $CONTAINER_NAME; then
        docker stop $CONTAINER_NAME
        echo -e "${GREEN}Container stopped.${NC}"
    else
        echo -e "${RED}Container is not running.${NC}"
    fi
}

# Function to show container logs
show_logs() {
    echo -e "${BLUE}Showing logs (Ctrl+C to exit):${NC}"
    docker logs -f $CONTAINER_NAME
}

# Function to show container status
show_status() {
    echo -e "${BLUE}Container status:${NC}"
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}Container is running.${NC}"
        docker ps | grep $CONTAINER_NAME
    elif docker ps -a | grep -q $CONTAINER_NAME; then
        echo -e "${RED}Container exists but is not running.${NC}"
        docker ps -a | grep $CONTAINER_NAME
    else
        echo -e "${RED}Container does not exist.${NC}"
    fi
    
    echo -e "\n${BLUE}Image status:${NC}"
    docker images | grep voice-pipeline-agent || echo -e "${RED}Image not found.${NC}"
}

# Function to rebuild the image
rebuild_image() {
    echo -e "${BLUE}Building Docker image...${NC}"
    docker build -t $IMAGE_NAME -f $DOCKERFILE .
    echo -e "${GREEN}Image built successfully.${NC}"
}

# Function to run interactive debug shell
debug_container() {
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${BLUE}Attaching to running container...${NC}"
        docker exec -it $CONTAINER_NAME /bin/bash
    else
        echo -e "${BLUE}Starting a new debug container...${NC}"
        docker run -it --rm --name "${CONTAINER_NAME}_debug" \
            --env-file .env.local \
            -v voice_model_cache:/app/.cache \
            $IMAGE_NAME /bin/bash
    fi
}

# Function to clean up
clean_up() {
    echo -e "${BLUE}Cleaning up...${NC}"
    
    if docker ps | grep -q $CONTAINER_NAME; then
        echo "Stopping container..."
        docker stop $CONTAINER_NAME
    fi
    
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo "Removing container..."
        docker rm $CONTAINER_NAME
    fi
    
    echo "Removing image..."
    docker rmi $IMAGE_NAME || true
    
    echo -e "${GREEN}Cleanup complete.${NC}"
}

# Check command argument
case "$1" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        stop_container
        start_container
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    rebuild)
        rebuild_image
        ;;
    debug)
        debug_container
        ;;
    clean)
        clean_up
        ;;
    help|*)
        show_help
        ;;
esac 