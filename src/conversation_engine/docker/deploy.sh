#!/bin/bash
#
# Conversation Engine Deployment Script
# Orchestrates complete Docker deployment with validation
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
DEPLOYMENT_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_RETRIES=12
HEALTH_CHECK_INTERVAL=10

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "🚀 RIKER CONVERSATION ENGINE DEPLOYMENT"
    echo "========================================"
    echo -e "${NC}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check for required environment variables
    if [[ -z "${ANTHROPIC_API_KEY}" ]]; then
        log_warning "ANTHROPIC_API_KEY not set. LLM features may not work."
        log_info "Set with: export ANTHROPIC_API_KEY=your_api_key"
    fi
    
    log_success "Prerequisites check passed"
}

cleanup_existing() {
    log_info "Cleaning up existing deployment..."
    
    # Stop and remove existing containers
    docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove dangling images
    docker image prune -f &> /dev/null || true
    
    log_success "Cleanup completed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build with no cache to ensure fresh build
    if docker-compose -f "$COMPOSE_FILE" build --no-cache; then
        log_success "Images built successfully"
    else
        log_error "Failed to build images"
        exit 1
    fi
}

start_services() {
    log_info "Starting services..."
    
    # Start services in detached mode
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        log_success "Services started"
    else
        log_error "Failed to start services"
        exit 1
    fi
}

wait_for_health() {
    log_info "Waiting for services to become healthy..."
    
    local retries=0
    local max_retries=$HEALTH_CHECK_RETRIES
    
    while [ $retries -lt $max_retries ]; do
        local healthy_services=$(docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l)
        local total_services=3  # redis, backend, frontend
        
        if [ "$healthy_services" -eq "$total_services" ]; then
            # Additional health checks
            if check_service_health; then
                log_success "All services are healthy"
                return 0
            fi
        fi
        
        retries=$((retries + 1))
        log_info "Health check $retries/$max_retries - waiting ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_error "Services failed to become healthy within timeout"
    show_service_logs
    exit 1
}

check_service_health() {
    # Check Redis
    if ! docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping &> /dev/null; then
        log_warning "Redis health check failed"
        return 1
    fi
    
    # Check Backend
    if ! curl -f http://localhost:8000/health &> /dev/null; then
        log_warning "Backend health check failed"
        return 1
    fi
    
    # Check Frontend
    if ! curl -f http://localhost:3000/ &> /dev/null; then
        log_warning "Frontend health check failed"
        return 1
    fi
    
    return 0
}

show_service_logs() {
    log_info "Showing service logs for debugging..."
    echo -e "${YELLOW}=== REDIS LOGS ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 redis
    echo -e "${YELLOW}=== BACKEND LOGS ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 backend
    echo -e "${YELLOW}=== FRONTEND LOGS ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 frontend
}

run_validation() {
    log_info "Running deployment validation..."
    
    if python3 validate_deployment.py --quick; then
        log_success "Deployment validation passed"
        return 0
    else
        log_error "Deployment validation failed"
        return 1
    fi
}

show_deployment_info() {
    echo -e "${GREEN}"
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "========================"
    echo -e "${NC}"
    echo "Services are running and accessible at:"
    echo "• Frontend:  http://localhost:3000"
    echo "• Backend:   http://localhost:8000"
    echo "• API Docs:  http://localhost:8000/docs"
    echo "• Health:    http://localhost:8000/health"
    echo ""
    echo "To view logs:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f"
    echo ""
    echo "To stop services:"
    echo "  docker-compose -f $COMPOSE_FILE down"
    echo ""
    echo "To stop and clean up:"
    echo "  docker-compose -f $COMPOSE_FILE down --volumes"
}

show_failure_info() {
    echo -e "${RED}"
    echo "💥 DEPLOYMENT FAILED!"
    echo "===================="
    echo -e "${NC}"
    echo "Check the logs above for details."
    echo ""
    echo "To view detailed logs:"
    echo "  docker-compose -f $COMPOSE_FILE logs"
    echo ""
    echo "To clean up:"
    echo "  docker-compose -f $COMPOSE_FILE down --volumes"
}

# Main deployment function
deploy() {
    print_header
    
    local start_time=$(date +%s)
    
    # Run deployment steps
    check_prerequisites
    cleanup_existing
    build_images
    start_services
    wait_for_health
    
    # Run validation
    if run_validation; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        show_deployment_info
        log_success "Deployment completed in ${duration}s"
        return 0
    else
        show_failure_info
        return 1
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "validate")
        log_info "Running validation only..."
        run_validation
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "clean")
        log_info "Cleaning up deployment..."
        docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans
        docker image prune -f
        log_success "Cleanup completed"
        ;;
    "status")
        echo "Service Status:"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "help")
        echo "Conversation Engine Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment (default)"
        echo "  validate  - Run validation only"
        echo "  logs      - Show service logs"
        echo "  stop      - Stop services"
        echo "  clean     - Stop and clean up"
        echo "  status    - Show service status"
        echo "  help      - Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac