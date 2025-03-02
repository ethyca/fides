#!/bin/bash
# parallel-build.sh - Run frontend and backend builds in parallel for faster development

set -e

# Print colored output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting parallel build of Fides frontend and backend...${NC}"

# Create a temporary directory for logs
mkdir -p .build_logs

# Function to monitor a background process
monitor_process() {
  local pid=$1
  local name=$2
  local log_file=$3

  while kill -0 $pid 2>/dev/null; do
    echo -e "${YELLOW}$name build running...${NC}"
    tail -n 5 $log_file
    sleep 5
  done

  # Get the exit status
  wait $pid
  local exit_status=$?

  if [ $exit_status -eq 0 ]; then
    echo -e "${GREEN}$name build completed successfully!${NC}"
  else
    echo -e "${RED}$name build failed with status $exit_status${NC}"
    echo "See full log at $log_file"
    # Output the last 20 lines to help diagnose the issue
    echo -e "${RED}Last 20 lines of the build log:${NC}"
    tail -n 20 $log_file
    exit $exit_status
  fi
}

# Ensure cache directories exist for BuildKit
mkdir -p ~/.cache/buildkit

# Start the backend build
echo -e "${BLUE}Starting backend build...${NC}"
DOCKER_BUILDKIT=1 docker build \
  --target backend \
  --build-arg PYTHON_VERSION=3.10.13 \
  -t ethyca/fides:backend-dev \
  . > .build_logs/backend.log 2>&1 &
backend_pid=$!

# Start the frontend build
echo -e "${BLUE}Starting frontend build...${NC}"
DOCKER_BUILDKIT=1 docker build \
  --target built_frontend \
  -t ethyca/fides:frontend-dev \
  . > .build_logs/frontend.log 2>&1 &
frontend_pid=$!

# Monitor the builds
monitor_process $backend_pid "Backend" ".build_logs/backend.log" &
monitor_process $frontend_pid "Frontend" ".build_logs/frontend.log" &

# Wait for all monitor processes to complete
wait

echo -e "${GREEN}All builds completed successfully!${NC}"
echo -e "${BLUE}You can now run containers with:${NC}"
echo "  docker run -it ethyca/fides:backend-dev"
echo "  docker run -it ethyca/fides:frontend-dev"

# Optional: build the production image by combining results
read -p "Would you like to build the production image now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
  echo -e "${BLUE}Building production image...${NC}"
  DOCKER_BUILDKIT=1 docker build \
    --target prod \
    --build-arg PYTHON_VERSION=3.10.13 \
    -t ethyca/fides:prod \
    . > .build_logs/prod.log 2>&1

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Production build completed successfully!${NC}"
  else
    echo -e "${RED}Production build failed${NC}"
    echo "See full log at .build_logs/prod.log"
    # Output the last 20 lines to help diagnose the issue
    echo -e "${RED}Last 20 lines of the build log:${NC}"
    tail -n 20 .build_logs/prod.log
    exit 1
  fi
fi

echo -e "${GREEN}Build process complete!${NC}"
