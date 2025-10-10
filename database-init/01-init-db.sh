#!/bin/bash
# PostgreSQL Database Initialization Script
# This script runs when PostgreSQL container starts for the first time

set -e

echo "🚀 Initializing Intelligence Platform PostgreSQL Database..."

# Create extensions
echo "📦 Installing PostgreSQL extensions..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable extensions for better text search and performance
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE EXTENSION IF NOT EXISTS btree_gin;
    CREATE EXTENSION IF NOT EXISTS btree_gist;
    
    -- Create custom functions for intelligence analysis
    CREATE OR REPLACE FUNCTION update_modified_column()
    RETURNS TRIGGER AS \$\$
    BEGIN
        NEW.modified = now();
        RETURN NEW;
    END;
    \$\$ language 'plpgsql';
    
    -- Grant necessary permissions
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- Set default search path
    ALTER DATABASE $POSTGRES_DB SET search_path TO public;
    
    COMMIT;
EOSQL

echo "✅ PostgreSQL database initialized successfully!"

# Create backup directory if it doesn't exist
mkdir -p /backups
chmod 755 /backups

echo "📁 Backup directory created at /backups"
echo "🎉 Database initialization completed!"
