#!/usr/bin/env python3
"""
Database Migration Runner for Vertex Data Integration
Handles automated deployment, rollback, and validation of database migrations.

Features:
- Idempotent migrations that can be safely re-run
- Rollback capabilities for safe database changes
- Comprehensive error handling and logging
- Migration validation and verification
- Row Level Security policy management
- HIPAA compliance for medical data

Usage:
    python migrate.py up                    # Apply all pending migrations
    python migrate.py down <migration_id>   # Rollback to specific migration
    python migrate.py status                # Show migration status
    python migrate.py validate              # Validate current schema
    python migrate.py create <name>         # Create new migration file
"""

import os
import sys
import logging
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass

class DatabaseMigrator:
    """
    Database migration manager with rollback capabilities and validation.
    Ensures HIPAA compliance and medical data security.
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.conn = None
        
    def connect(self):
        """Establish database connection with error handling"""
        try:
            self.conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            self.conn.autocommit = False
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise MigrationError(f"Database connection failed: {e}")
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        migration_id VARCHAR(255) UNIQUE NOT NULL,
                        filename VARCHAR(255) NOT NULL,
                        checksum VARCHAR(64) NOT NULL,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        applied_by VARCHAR(255) DEFAULT CURRENT_USER,
                        execution_time_ms INTEGER,
                        rollback_sql TEXT,
                        is_rolled_back BOOLEAN DEFAULT FALSE,
                        rollback_at TIMESTAMP WITH TIME ZONE,
                        rollback_by VARCHAR(255)
                    );
                    
                    -- Index for performance
                    CREATE INDEX IF NOT EXISTS idx_schema_migrations_id 
                        ON schema_migrations(migration_id);
                    CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied 
                        ON schema_migrations(applied_at DESC);
                """)
                self.conn.commit()
                logger.info("Migration tracking table ensured")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to create migration table: {e}")
            raise MigrationError(f"Migration table creation failed: {e}")
    
    def get_migration_files(self) -> List[Tuple[str, Path]]:
        """Get all migration files sorted by ID"""
        migration_files = []
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return migration_files
        
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            # Extract migration ID from filename (e.g., "001_add_clinical_thresholds.sql" -> "001")
            migration_id = file_path.stem.split('_')[0]
            migration_files.append((migration_id, file_path))
        
        logger.info(f"Found {len(migration_files)} migration files")
        return migration_files
    
    def get_applied_migrations(self) -> Dict[str, Dict]:
        """Get list of applied migrations from database"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT migration_id, filename, checksum, applied_at, 
                           is_rolled_back, execution_time_ms
                    FROM schema_migrations 
                    WHERE is_rolled_back = FALSE
                    ORDER BY migration_id
                """)
                
                applied = {}
                for row in cursor.fetchall():
                    applied[row['migration_id']] = dict(row)
                
                logger.info(f"Found {len(applied)} applied migrations")
                return applied
                
        except psycopg2.Error as e:
            logger.error(f"Failed to get applied migrations: {e}")
            raise MigrationError(f"Failed to query migrations: {e}")
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of migration file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except IOError as e:
            logger.error(f"Failed to read migration file {file_path}: {e}")
            raise MigrationError(f"File read error: {e}")
    
    def validate_migration_checksum(self, migration_id: str, file_path: Path) -> bool:
        """Validate that migration file hasn't been modified after application"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT checksum FROM schema_migrations WHERE migration_id = %s",
                    (migration_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return True  # Migration not applied yet
                
                stored_checksum = row['checksum']
                current_checksum = self.calculate_checksum(file_path)
                
                if stored_checksum != current_checksum:
                    logger.error(f"Migration {migration_id} checksum mismatch!")
                    logger.error(f"Stored: {stored_checksum}")
                    logger.error(f"Current: {current_checksum}")
                    return False
                
                return True
                
        except psycopg2.Error as e:
            logger.error(f"Failed to validate checksum for {migration_id}: {e}")
            return False
    
    def extract_rollback_sql(self, content: str) -> Optional[str]:
        """Extract rollback SQL from migration file comments"""
        lines = content.split('\n')
        rollback_lines = []
        in_rollback_section = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('-- ROLLBACK:'):
                in_rollback_section = True
                continue
            elif line.startswith('-- END ROLLBACK') or (line.startswith('--') and not in_rollback_section):
                if in_rollback_section:
                    break
            elif in_rollback_section and line.startswith('-- '):
                rollback_lines.append(line[3:])  # Remove '-- ' prefix
        
        return '\n'.join(rollback_lines) if rollback_lines else None
    
    def apply_migration(self, migration_id: str, file_path: Path) -> bool:
        """Apply a single migration with error handling and rollback support"""
        logger.info(f"Applying migration {migration_id}: {file_path.name}")
        
        try:
            # Read migration file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate checksum
            checksum = self.calculate_checksum(file_path)
            
            # Extract rollback SQL if available
            rollback_sql = self.extract_rollback_sql(content)
            
            # Start transaction
            start_time = datetime.datetime.now()
            
            with self.conn.cursor() as cursor:
                # Execute migration SQL
                cursor.execute(content)
                
                # Record migration in tracking table
                end_time = datetime.datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                cursor.execute("""
                    INSERT INTO schema_migrations 
                    (migration_id, filename, checksum, execution_time_ms, rollback_sql)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (migration_id) DO UPDATE SET
                        applied_at = NOW(),
                        applied_by = CURRENT_USER,
                        execution_time_ms = EXCLUDED.execution_time_ms,
                        is_rolled_back = FALSE
                """, (migration_id, file_path.name, checksum, execution_time, rollback_sql))
                
                self.conn.commit()
                logger.info(f"Migration {migration_id} applied successfully in {execution_time}ms")
                return True
                
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to apply migration {migration_id}: {e}")
            logger.error(f"SQL Error: {e.pgerror if hasattr(e, 'pgerror') else 'Unknown'}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Unexpected error applying migration {migration_id}: {e}")
            return False
    
    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a specific migration using stored rollback SQL"""
        logger.info(f"Rolling back migration {migration_id}")
        
        try:
            with self.conn.cursor() as cursor:
                # Get rollback SQL
                cursor.execute("""
                    SELECT rollback_sql, filename 
                    FROM schema_migrations 
                    WHERE migration_id = %s AND is_rolled_back = FALSE
                """, (migration_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.error(f"Migration {migration_id} not found or already rolled back")
                    return False
                
                rollback_sql = row['rollback_sql']
                if not rollback_sql:
                    logger.error(f"No rollback SQL available for migration {migration_id}")
                    return False
                
                # Execute rollback SQL
                cursor.execute(rollback_sql)
                
                # Mark as rolled back
                cursor.execute("""
                    UPDATE schema_migrations 
                    SET is_rolled_back = TRUE, 
                        rollback_at = NOW(), 
                        rollback_by = CURRENT_USER
                    WHERE migration_id = %s
                """, (migration_id,))
                
                self.conn.commit()
                logger.info(f"Migration {migration_id} rolled back successfully")
                return True
                
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to rollback migration {migration_id}: {e}")
            return False
    
    def migrate_up(self) -> bool:
        """Apply all pending migrations"""
        logger.info("Starting migration up process")
        
        try:
            self.ensure_migration_table()
            
            migration_files = self.get_migration_files()
            applied_migrations = self.get_applied_migrations()
            
            pending_migrations = []
            for migration_id, file_path in migration_files:
                if migration_id not in applied_migrations:
                    pending_migrations.append((migration_id, file_path))
                else:
                    # Validate checksum for applied migrations
                    if not self.validate_migration_checksum(migration_id, file_path):
                        logger.error(f"Migration {migration_id} has been modified after application!")
                        return False
            
            if not pending_migrations:
                logger.info("No pending migrations found")
                return True
            
            logger.info(f"Found {len(pending_migrations)} pending migrations")
            
            # Apply pending migrations
            success_count = 0
            for migration_id, file_path in pending_migrations:
                if self.apply_migration(migration_id, file_path):
                    success_count += 1
                else:
                    logger.error(f"Migration failed at {migration_id}, stopping")
                    return False
            
            logger.info(f"Successfully applied {success_count} migrations")
            return True
            
        except Exception as e:
            logger.error(f"Migration up process failed: {e}")
            return False
    
    def migrate_down(self, target_migration_id: str) -> bool:
        """Rollback migrations down to target migration"""
        logger.info(f"Rolling back to migration {target_migration_id}")
        
        try:
            applied_migrations = self.get_applied_migrations()
            
            # Find migrations to rollback (in reverse order)
            migrations_to_rollback = []
            for migration_id in sorted(applied_migrations.keys(), reverse=True):
                if migration_id > target_migration_id:
                    migrations_to_rollback.append(migration_id)
            
            if not migrations_to_rollback:
                logger.info("No migrations to rollback")
                return True
            
            logger.info(f"Rolling back {len(migrations_to_rollback)} migrations")
            
            # Rollback migrations
            for migration_id in migrations_to_rollback:
                if not self.rollback_migration(migration_id):
                    logger.error(f"Rollback failed at {migration_id}, stopping")
                    return False
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback process failed: {e}")
            return False
    
    def show_status(self):
        """Show current migration status"""
        try:
            self.ensure_migration_table()
            
            migration_files = self.get_migration_files()
            applied_migrations = self.get_applied_migrations()
            
            print("\n=== Migration Status ===")
            print(f"{'ID':<10} {'Filename':<40} {'Status':<15} {'Applied At':<20}")
            print("-" * 85)
            
            for migration_id, file_path in migration_files:
                if migration_id in applied_migrations:
                    applied_info = applied_migrations[migration_id]
                    status = "APPLIED"
                    applied_at = applied_info['applied_at'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    status = "PENDING"
                    applied_at = "-"
                
                print(f"{migration_id:<10} {file_path.name:<40} {status:<15} {applied_at:<20}")
            
            print(f"\nTotal migrations: {len(migration_files)}")
            print(f"Applied: {len(applied_migrations)}")
            print(f"Pending: {len(migration_files) - len(applied_migrations)}")
            
        except Exception as e:
            logger.error(f"Failed to show status: {e}")
    
    def validate_schema(self) -> bool:
        """Validate current database schema against expected structure"""
        logger.info("Validating database schema")
        
        validation_queries = [
            # Check critical tables exist
            ("patients table", "SELECT 1 FROM information_schema.tables WHERE table_name = 'patients'"),
            ("sensor_readings table", "SELECT 1 FROM information_schema.tables WHERE table_name = 'sensor_readings'"),
            ("pusher_episodes table", "SELECT 1 FROM information_schema.tables WHERE table_name = 'pusher_episodes'"),
            ("clinical_thresholds table", "SELECT 1 FROM information_schema.tables WHERE table_name = 'clinical_thresholds'"),
            ("esp32_devices table", "SELECT 1 FROM information_schema.tables WHERE table_name = 'esp32_devices'"),
            
            # Check RLS is enabled
            ("patients RLS", "SELECT 1 FROM pg_tables WHERE tablename = 'patients' AND rowsecurity = true"),
            ("sensor_readings RLS", "SELECT 1 FROM pg_tables WHERE tablename = 'sensor_readings' AND rowsecurity = true"),
            ("pusher_episodes RLS", "SELECT 1 FROM pg_tables WHERE tablename = 'pusher_episodes' AND rowsecurity = true"),
            
            # Check critical indexes exist
            ("sensor_readings patient index", """
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'sensor_readings' 
                AND indexname = 'idx_sensor_readings_patient_timestamp'
            """),
            ("pusher_episodes patient index", """
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'pusher_episodes' 
                AND indexname = 'idx_pusher_episodes_patient_date'
            """),
            
            # Check critical constraints
            ("clinical_thresholds paretic_side constraint", """
                SELECT 1 FROM information_schema.check_constraints 
                WHERE constraint_name LIKE '%paretic_side%'
            """),
            ("pusher_episodes severity_score constraint", """
                SELECT 1 FROM information_schema.check_constraints 
                WHERE constraint_name LIKE '%severity_score%'
            """),
        ]
        
        validation_passed = True
        
        try:
            with self.conn.cursor() as cursor:
                for check_name, query in validation_queries:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    
                    if result:
                        logger.info(f"✓ {check_name}")
                    else:
                        logger.error(f"✗ {check_name}")
                        validation_passed = False
            
            if validation_passed:
                logger.info("Schema validation passed")
            else:
                logger.error("Schema validation failed")
            
            return validation_passed
            
        except psycopg2.Error as e:
            logger.error(f"Schema validation error: {e}")
            return False
    
    def create_migration(self, name: str):
        """Create a new migration file template"""
        # Get next migration ID
        existing_migrations = self.get_migration_files()
        if existing_migrations:
            last_id = int(existing_migrations[-1][0])
            next_id = f"{last_id + 1:03d}"
        else:
            next_id = "001"
        
        # Create filename
        clean_name = name.lower().replace(' ', '_').replace('-', '_')
        filename = f"{next_id}_{clean_name}.sql"
        file_path = self.migrations_dir / filename
        
        # Create migration template
        template = f"""-- Migration: {name}
-- Date: {datetime.datetime.now().strftime('%Y-%m-%d')}
-- Description: {name}

-- ============================================================================
-- MIGRATION UP
-- ============================================================================

-- Add your migration SQL here
-- Example:
-- CREATE TABLE example_table (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     name VARCHAR NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- ============================================================================
-- INDEXES AND CONSTRAINTS
-- ============================================================================

-- Add indexes for performance
-- CREATE INDEX IF NOT EXISTS idx_example_table_name ON example_table(name);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS if needed
-- ALTER TABLE example_table ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- CREATE POLICY "example_policy" ON example_table
--     FOR SELECT USING (auth.uid()::text = user_id::text);

-- ============================================================================
-- ROLLBACK SQL (for automated rollback support)
-- ============================================================================

-- ROLLBACK:
-- DROP TABLE IF EXISTS example_table;
-- END ROLLBACK
"""
        
        try:
            self.migrations_dir.mkdir(exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template)
            
            logger.info(f"Created migration file: {file_path}")
            print(f"Migration file created: {file_path}")
            
        except IOError as e:
            logger.error(f"Failed to create migration file: {e}")
            raise MigrationError(f"File creation failed: {e}")

def get_database_url() -> str:
    """Get database connection string from environment"""
    # Try different environment variable names
    db_url = (
        os.getenv('DATABASE_URL') or
        os.getenv('SUPABASE_DB_URL') or
        os.getenv('POSTGRES_URL')
    )
    
    if not db_url:
        # Construct from individual components
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'postgres')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    return db_url

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Up command
    subparsers.add_parser('up', help='Apply all pending migrations')
    
    # Down command
    down_parser = subparsers.add_parser('down', help='Rollback to specific migration')
    down_parser.add_argument('migration_id', help='Target migration ID to rollback to')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate current schema')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new migration file')
    create_parser.add_argument('name', help='Migration name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Get database connection
    try:
        db_url = get_database_url()
        migrator = DatabaseMigrator(db_url)
        migrator.connect()
        
        # Execute command
        if args.command == 'up':
            success = migrator.migrate_up()
        elif args.command == 'down':
            success = migrator.migrate_down(args.migration_id)
        elif args.command == 'status':
            migrator.show_status()
            success = True
        elif args.command == 'validate':
            success = migrator.validate_schema()
        elif args.command == 'create':
            migrator.create_migration(args.name)
            success = True
        else:
            logger.error(f"Unknown command: {args.command}")
            success = False
        
        migrator.disconnect()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())