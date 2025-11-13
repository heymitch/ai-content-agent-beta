#!/bin/bash
# ============================================================================
# Deploy Supabase Bootstrap to Client Instance
# ============================================================================
# This script deploys the complete database schema to a client's Supabase
# instance via their database connection string.
#
# Usage:
#   ./deploy_to_client.sh <postgres_connection_string>
#
# Example:
#   ./deploy_to_client.sh "postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
#
# Or use environment variable:
#   export CLIENT_SUPABASE_DB_URL="postgresql://..."
#   ./deploy_to_client.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BOOTSTRAP_SQL="$SCRIPT_DIR/bootstrap_supabase.sql"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🚀 Supabase Bootstrap Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if bootstrap SQL exists
if [ ! -f "$BOOTSTRAP_SQL" ]; then
    echo -e "${RED}❌ Error: bootstrap_supabase.sql not found!${NC}"
    echo -e "${YELLOW}Expected location: $BOOTSTRAP_SQL${NC}"
    exit 1
fi

# Get database connection string
if [ -n "$1" ]; then
    DB_URL="$1"
elif [ -n "$CLIENT_SUPABASE_DB_URL" ]; then
    DB_URL="$CLIENT_SUPABASE_DB_URL"
else
    echo -e "${RED}❌ Error: No database URL provided${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  ${GREEN}./deploy_to_client.sh \"postgresql://...\"${NC}"
    echo ""
    echo -e "${YELLOW}Or set environment variable:${NC}"
    echo -e "  ${GREEN}export CLIENT_SUPABASE_DB_URL=\"postgresql://...\"${NC}"
    echo -e "  ${GREEN}./deploy_to_client.sh${NC}"
    echo ""
    exit 1
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ Error: psql is not installed${NC}"
    echo ""
    echo -e "${YELLOW}Install PostgreSQL client:${NC}"
    echo -e "  ${GREEN}macOS:${NC} brew install postgresql"
    echo -e "  ${GREEN}Ubuntu:${NC} sudo apt-get install postgresql-client"
    echo ""
    exit 1
fi

# Validate connection string format
if [[ ! "$DB_URL" =~ ^postgresql:// ]]; then
    echo -e "${RED}❌ Error: Invalid connection string format${NC}"
    echo -e "${YELLOW}Expected format:${NC}"
    echo -e "  postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
    exit 1
fi

# Mask password in display
DISPLAY_URL=$(echo "$DB_URL" | sed -E 's/:([^@]+)@/:***@/')
echo -e "${BLUE}📡 Target Database:${NC}"
echo -e "  $DISPLAY_URL"
echo ""

# Test connection
echo -e "${YELLOW}🔍 Testing connection...${NC}"
if ! psql "$DB_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to connect to database${NC}"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo -e "  1. Check your password is correct"
    echo -e "  2. Verify your IP is allowed in Supabase settings"
    echo -e "  3. Ensure database pooler is enabled"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ Connection successful${NC}"
echo ""

# Ask for confirmation
echo -e "${YELLOW}⚠️  This will create/update tables in the target database${NC}"
echo -e "${YELLOW}   Safe to run multiple times (uses IF NOT EXISTS)${NC}"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}📦 Deploying bootstrap schema...${NC}"
echo ""

# Run the bootstrap SQL
if psql "$DB_URL" -f "$BOOTSTRAP_SQL"; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}✅ Deployment Successful!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}📋 What was created:${NC}"
    echo -e "  • 9 tables (content_examples, research, etc.)"
    echo -e "  • RAG search functions"
    echo -e "  • Indexes for performance"
    echo -e "  • Row Level Security policies"
    echo ""
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo -e "  1. Update client .env with their Supabase credentials"
    echo -e "  2. Import n8n workflow (tables already exist!)"
    echo -e "  3. Configure Google Drive integration"
    echo -e "  4. Test the agent"
    echo ""
else
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}❌ Deployment Failed${NC}"
    echo -e "${RED}============================================${NC}"
    echo ""
    echo -e "${YELLOW}Check the error messages above for details${NC}"
    exit 1
fi
