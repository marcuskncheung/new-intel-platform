#!/bin/bash
# Quick PostgreSQL Migration and Deployment Script
# Intelligence Platform Migration Helper

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.postgresql.yml"
ENV_FILE=".env.postgresql"

echo -e "${BLUE}🐘 Intelligence Platform - PostgreSQL Migration${NC}"
echo "=================================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to backup SQLite database
backup_sqlite() {
    if [ -f "instance/users.db" ]; then
        echo -e "${YELLOW}📋 Backing up existing SQLite database...${NC}"
        cp instance/users.db instance/users.db.backup.$(date +%Y%m%d_%H%M%S)
        echo -e "${GREEN}✅ SQLite database backed up${NC}"
    else
        echo -e "${YELLOW}⚠️ No existing SQLite database found to backup${NC}"
    fi
}

# Function to update environment variables
setup_environment() {
    echo -e "${YELLOW}🔧 Setting up environment variables...${NC}"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ Environment file $ENV_FILE not found!${NC}"
        exit 1
    fi
    
    # Check if Exchange password is set
    if grep -q "EXCHANGE_PASSWORD=YourExchangePassword123" "$ENV_FILE"; then
        echo -e "${YELLOW}⚠️ Please update your Exchange password in $ENV_FILE${NC}"
        echo "   Edit the file and replace 'YourExchangePassword123' with your real password"
        read -p "Press Enter when you've updated the password..."
    fi
    
    # Copy to production environment
    cp "$ENV_FILE" .env.production
    echo -e "${GREEN}✅ Environment configured${NC}"
}

# Function to start PostgreSQL
start_database() {
    echo -e "${YELLOW}🗄️ Starting PostgreSQL database...${NC}"
    docker compose -f "$COMPOSE_FILE" up -d postgres-db
    
    echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready (30 seconds)...${NC}"
    sleep 30
    
    # Check if database is ready
    if docker compose -f "$COMPOSE_FILE" exec -T postgres-db pg_isready -U intelligence -d intelligence_db; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
    else
        echo -e "${RED}❌ PostgreSQL failed to start properly${NC}"
        echo "Checking logs:"
        docker compose -f "$COMPOSE_FILE" logs postgres-db
        exit 1
    fi
}

# Function to run migration
run_migration() {
    if [ -f "instance/users.db" ]; then
        echo -e "${YELLOW}🔄 Running database migration...${NC}"
        docker compose -f "$COMPOSE_FILE" --profile migration up db-migrate
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Database migration completed successfully${NC}"
        else
            echo -e "${RED}❌ Database migration failed${NC}"
            echo "Checking migration logs:"
            docker-compose -f "$COMPOSE_FILE" logs db-migrate
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️ No SQLite database found - starting with fresh PostgreSQL database${NC}"
    fi
}

# Function to start application
start_application() {
    echo -e "${YELLOW}🚀 Starting Intelligence Platform application...${NC}"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    echo -e "${YELLOW}⏳ Waiting for application to start (30 seconds)...${NC}"
    sleep 30
    
    # Check application health
    if curl -f -k https://localhost/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is running successfully${NC}"
    else
        echo -e "${YELLOW}⚠️ Application may still be starting up. Checking logs...${NC}"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20 intelligence-platform
    fi
}

# Function to verify deployment
verify_deployment() {
    echo -e "${BLUE}🔍 Verifying deployment...${NC}"
    echo ""
    echo "Container Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Check database connectivity
    echo "Database Connectivity:"
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres-db psql -U intelligence -d intelligence_db -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database: Connected${NC}"
    else
        echo -e "${RED}❌ Database: Connection failed${NC}"
    fi
    
    # Check table count
    echo "Database Tables:"
    table_count=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres-db psql -U intelligence -d intelligence_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
    echo -e "${GREEN}✅ Tables created: $table_count${NC}"
    
    # Check application health
    echo "Application Status:"
    if curl -f -k https://localhost > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Web interface: Accessible at https://localhost${NC}"
    else
        echo -e "${YELLOW}⚠️ Web interface: Still starting up${NC}"
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo -e "${BLUE}🎉 Deployment Complete!${NC}"
    echo "===================="
    echo ""
    echo -e "${GREEN}✅ Your Intelligence Platform is now running with PostgreSQL!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. 🌐 Access your platform: https://localhost"
    echo "2. 🔐 Login with admin credentials from your .env.production file"
    echo "3. 📊 Check that all your data has been migrated successfully"
    echo "4. 🔗 Update firewall rules for Exchange server connectivity"
    echo "5. 📈 Monitor performance and setup regular backups"
    echo ""
    echo "Management commands:"
    echo "• View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "• Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "• Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "• Backup database: docker exec intelligence-db pg_dump -U intelligence -d intelligence_db > backup.sql"
    echo ""
    echo "For troubleshooting, see POSTGRESQL_MIGRATION.md"
}

# Main execution
main() {
    echo -e "${BLUE}Starting migration process...${NC}"
    
    check_docker
    backup_sqlite
    setup_environment
    start_database
    run_migration
    start_application
    verify_deployment
    show_next_steps
}

# Handle script arguments
case "${1:-}" in
    "clean")
        echo -e "${YELLOW}🧹 Cleaning up containers and volumes...${NC}"
        docker-compose -f "$COMPOSE_FILE" down -v
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "backup")
        echo -e "${YELLOW}💾 Creating database backup...${NC}"
        docker exec intelligence-db pg_dump -U intelligence -d intelligence_db > "backup_$(date +%Y%m%d_%H%M%S).sql"
        echo -e "${GREEN}✅ Backup created${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Restarting services...${NC}"
        docker-compose -f "$COMPOSE_FILE" restart
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
    *)
        main
        ;;
esac
