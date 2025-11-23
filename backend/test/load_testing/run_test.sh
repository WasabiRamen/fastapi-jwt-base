#!/bin/bash
# Locust Load Testing Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
HOST=${HOST:-"http://localhost:8000"}
USERS=${USERS:-10}
SPAWN_RATE=${SPAWN_RATE:-2}
RUN_TIME=${RUN_TIME:-"1m"}

print_header() {
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  FastAPI Load Testing Runner${NC}"
    echo -e "${GREEN}================================${NC}"
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -w, --web               Run with Web UI (default: headless)"
    echo "  -u, --users NUM         Number of users to simulate (default: 10)"
    echo "  -r, --spawn-rate NUM    Users spawned per second (default: 2)"
    echo "  -t, --time DURATION     Test duration e.g., 1m, 30s (default: 1m)"
    echo "  -H, --host URL          Target host (default: http://localhost:8000)"
    echo "  -o, --output DIR        Output directory for CSV results"
    echo "  -c, --class CLASS       Run specific user class (AuthenticatedUser or LoginOnlyUser)"
    echo ""
    echo "Examples:"
    echo "  $0 --web"
    echo "  $0 -u 50 -r 5 -t 2m"
    echo "  $0 -u 100 -r 10 -t 5m -o ./results"
    echo "  $0 -c AuthenticatedUser -u 20"
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    if ! command -v locust &> /dev/null; then
        echo -e "${RED}Error: locust is not installed${NC}"
        echo "Install with: pip install -r requirements.txt"
        exit 1
    fi
    
    if [ ! -f "locustfile.py" ]; then
        echo -e "${RED}Error: locustfile.py not found${NC}"
        echo "Make sure you're in the load_testing directory"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Dependencies OK${NC}"
}

check_env() {
    if [ -f ".env" ]; then
        echo -e "${GREEN}✓ Loading .env file${NC}"
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo -e "${YELLOW}⚠ .env file not found, using defaults${NC}"
        echo "  Copy .env.example to .env and configure it"
    fi
}

check_backend() {
    echo -e "${YELLOW}Checking backend health...${NC}"
    
    if curl -s "${HOST}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is running at ${HOST}${NC}"
    else
        echo -e "${RED}⚠ Warning: Cannot reach backend at ${HOST}${NC}"
        echo "  Make sure your backend server is running"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

run_web_ui() {
    echo -e "${GREEN}Starting Locust Web UI...${NC}"
    echo -e "Open browser at: ${YELLOW}http://localhost:8089${NC}"
    echo ""
    
    if [ -n "$USER_CLASS" ]; then
        locust -f locustfile.py --host="${HOST}" "$USER_CLASS"
    else
        locust -f locustfile.py --host="${HOST}"
    fi
}

run_headless() {
    echo -e "${GREEN}Running headless load test...${NC}"
    echo "  Host: ${HOST}"
    echo "  Users: ${USERS}"
    echo "  Spawn rate: ${SPAWN_RATE}/s"
    echo "  Duration: ${RUN_TIME}"
    [ -n "$OUTPUT_DIR" ] && echo "  Output: ${OUTPUT_DIR}"
    [ -n "$USER_CLASS" ] && echo "  User class: ${USER_CLASS}"
    echo ""
    
    CMD="locust -f locustfile.py --host=${HOST} --users ${USERS} --spawn-rate ${SPAWN_RATE} --run-time ${RUN_TIME} --headless"
    
    if [ -n "$OUTPUT_DIR" ]; then
        mkdir -p "$OUTPUT_DIR"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        CMD="$CMD --csv=${OUTPUT_DIR}/load_test_${TIMESTAMP}"
    fi
    
    if [ -n "$USER_CLASS" ]; then
        CMD="$CMD $USER_CLASS"
    fi
    
    eval $CMD
}

# Main script
print_header

# Parse arguments
WEB_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        -w|--web)
            WEB_MODE=true
            shift
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--class)
            USER_CLASS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Run checks
check_dependencies
check_env
check_backend

# Run the appropriate mode
if [ "$WEB_MODE" = true ]; then
    run_web_ui
else
    run_headless
fi

echo -e "${GREEN}Test completed!${NC}"
