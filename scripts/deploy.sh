#!/bin/bash
# Production deployment script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="mortgage-calculator"
CONTAINER_NAME="mortgage-calc-prod"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_status "Docker is available and running"
}

# Check if required files exist
check_files() {
    required_files=("Dockerfile" "requirements.txt" "app_refactored.py" "gunicorn.conf.py")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file $file not found"
            exit 1
        fi
    done
    
    print_status "All required files are present"
}

# Create backup of current deployment
create_backup() {
    print_status "Creating backup of current deployment..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup configuration files
    cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r logs/ "$BACKUP_DIR/" 2>/dev/null || true
    
    # Export current container if it exists
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_status "Exporting current container..."
        docker export "$CONTAINER_NAME" > "$BACKUP_DIR/container_backup.tar"
    fi
    
    print_status "Backup created at $BACKUP_DIR"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    # Build with build args for optimization
    docker build \
        --target production \
        --tag "$IMAGE_NAME:latest" \
        --tag "$IMAGE_NAME:$(date +%Y%m%d_%H%M%S)" \
        .
    
    print_status "Docker image built successfully"
}

# Run security scan
security_scan() {
    if command -v docker &> /dev/null; then
        print_status "Running security scan..."
        
        # Use Docker scout if available, otherwise skip
        if docker scout version &> /dev/null; then
            docker scout cves "$IMAGE_NAME:latest" || print_warning "Security scan completed with warnings"
        else
            print_warning "Docker Scout not available, skipping security scan"
        fi
    fi
}

# Stop existing container
stop_container() {
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_status "Stopping existing container..."
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
}

# Deploy new container
deploy_container() {
    print_status "Deploying new container..."
    
    # Check if .env file exists for environment variables
    ENV_FILE=""
    if [ -f ".env" ]; then
        ENV_FILE="--env-file .env"
    fi
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        -p 8000:8000 \
        $ENV_FILE \
        -e FLASK_ENV=production \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/config:/app/config" \
        "$IMAGE_NAME:latest"
    
    print_status "Container deployed successfully"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Wait for container to start
    sleep 10
    
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_status "Health check passed"
            return 0
        fi
        sleep 2
    done
    
    print_error "Health check failed"
    return 1
}

# Show deployment status
show_status() {
    print_section "DEPLOYMENT STATUS"
    
    echo "Container Status:"
    docker ps -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "Recent Logs:"
    docker logs --tail 20 "$CONTAINER_NAME"
    
    echo ""
    echo "Application URL: http://localhost:8000"
    echo "Health Check: http://localhost:8000/health"
}

# Rollback function
rollback() {
    print_warning "Rolling back deployment..."
    
    # Stop current container
    stop_container
    
    # Find the previous image
    PREVIOUS_IMAGE=$(docker images "$IMAGE_NAME" --format "{{.Repository}}:{{.Tag}}" | grep -v latest | head -1)
    
    if [ -n "$PREVIOUS_IMAGE" ]; then
        print_status "Rolling back to $PREVIOUS_IMAGE"
        
        docker run -d \
            --name "$CONTAINER_NAME" \
            --restart unless-stopped \
            -p 8000:8000 \
            --env-file .env \
            -e FLASK_ENV=production \
            -v "$(pwd)/logs:/app/logs" \
            -v "$(pwd)/data:/app/data" \
            -v "$(pwd)/config:/app/config" \
            "$PREVIOUS_IMAGE"
        
        print_status "Rollback completed"
    else
        print_error "No previous image found for rollback"
        exit 1
    fi
}

# Cleanup old images
cleanup() {
    print_status "Cleaning up old images..."
    
    # Keep last 3 images
    OLD_IMAGES=$(docker images "$IMAGE_NAME" --format "{{.Repository}}:{{.Tag}}" | grep -v latest | tail -n +4)
    
    if [ -n "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | xargs docker rmi || true
        print_status "Old images cleaned up"
    else
        print_status "No old images to clean up"
    fi
}

# Main deployment function
main() {
    case $1 in
        "deploy")
            print_section "STARTING DEPLOYMENT"
            check_docker
            check_files
            create_backup
            build_image
            security_scan
            stop_container
            deploy_container
            
            if health_check; then
                show_status
                cleanup
                print_section "DEPLOYMENT COMPLETED SUCCESSFULLY"
            else
                print_error "Deployment failed health check"
                rollback
                exit 1
            fi
            ;;
        "build")
            check_docker
            check_files
            build_image
            security_scan
            ;;
        "rollback")
            rollback
            health_check
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker logs -f "$CONTAINER_NAME"
            ;;
        "stop")
            stop_container
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            echo "Usage: $0 {deploy|build|rollback|status|logs|stop|cleanup}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full deployment with backup and health check"
            echo "  build    - Build Docker image only"
            echo "  rollback - Rollback to previous version"
            echo "  status   - Show deployment status"
            echo "  logs     - Show container logs"
            echo "  stop     - Stop running container"
            echo "  cleanup  - Remove old images"
            exit 1
            ;;
    esac
}

main $1