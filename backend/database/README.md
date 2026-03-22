# Database Migration System

This directory contains the database migration system for the Vertex Data Integration project, providing automated deployment, rollback capabilities, and comprehensive validation for clinical data security and HIPAA compliance.

## Overview

The migration system ensures:
- **Idempotent migrations** that can be safely re-run
- **Rollback capabilities** for safe database changes
- **Comprehensive error handling** and logging
- **Migration validation** and verification
- **Row Level Security** policy management
- **HIPAA compliance** for medical data

## Files Structure

```
backend/database/
├── migrate.py              # Main migration runner script
├── validate_schema.py      # Schema validation script
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── schema.sql             # Base database schema
└── migrations/            # Migration files directory
    ├── 001_add_clinical_thresholds.sql
    ├── 002_clinical_episode_tracking.sql
    └── 003_security_and_validation.sql
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend/database
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file or set environment variables:

```bash
# Option 1: Full database URL
export DATABASE_URL="postgresql://username:password@host:port/database"

# Option 2: Individual components
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="vertex_db"
export DB_USER="postgres"
export DB_PASSWORD="your_password"
```

### 3. Run Migrations

```bash
# Apply all pending migrations
python migrate.py up

# Check migration status
python migrate.py status

# Validate schema after migration
python validate_schema.py
```

## Migration Commands

### Apply Migrations

```bash
# Apply all pending migrations
python migrate.py up
```

### Check Status

```bash
# Show current migration status
python migrate.py status
```

Output example:
```
=== Migration Status ===
ID         Filename                                 Status          Applied At          
---------------------------------------------------------------------------------
001        001_add_clinical_thresholds.sql         APPLIED         2024-01-15 10:30:25
002        002_clinical_episode_tracking.sql       APPLIED         2024-01-15 10:31:12
003        003_security_and_validation.sql         PENDING         -                   

Total migrations: 3
Applied: 2
Pending: 1
```

### Rollback Migrations

```bash
# Rollback to specific migration (rolls back all migrations after the target)
python migrate.py down 001
```

### Validate Schema

```bash
# Validate current database schema
python migrate.py validate
```

### Create New Migration

```bash
# Create new migration file with template
python migrate.py create "Add new feature"
```

## Schema Validation

The validation script provides comprehensive checks for:

### Run All Validations

```bash
python validate_schema.py
```

### Run Specific Validations

```bash
python validate_schema.py --tables      # Validate table structure only
python validate_schema.py --policies    # Validate RLS policies only
python validate_schema.py --constraints # Validate constraints only
python validate_schema.py --indexes     # Validate indexes only
```

### Validation Categories

1. **Tables**: Verifies all required tables exist
2. **Columns**: Checks column existence and data types
3. **Constraints**: Validates data validation constraints
4. **Indexes**: Ensures performance indexes are in place
5. **RLS Policies**: Verifies Row Level Security policies
6. **Functions**: Checks database functions exist
7. **Triggers**: Validates database triggers

## Migration Files

### Current Migrations

#### 001_add_clinical_thresholds.sql
- Adds clinical thresholds management tables
- Patient-specific clinical parameters
- Version history tracking
- ESP32 device registry
- Enhanced device calibrations

#### 002_clinical_episode_tracking.sql
- Comprehensive clinical episode tracking
- Pusher syndrome detection analytics
- Enhanced sensor readings with clinical data
- Performance indexes for clinical queries
- Row Level Security policies

#### 003_security_and_validation.sql
- Data validation constraints for all tables
- Enhanced Row Level Security policies
- HIPAA compliance measures
- Audit logging system
- Patient-provider relationship management
- Data retention and anonymization functions

### Migration File Format

Each migration file follows this structure:

```sql
-- Migration: Description
-- Date: YYYY-MM-DD
-- Description: Detailed description
-- Task: Reference to implementation task
-- Requirements: Reference to requirements

-- ============================================================================
-- MIGRATION UP
-- ============================================================================

-- Your migration SQL here

-- ============================================================================
-- INDEXES AND CONSTRAINTS
-- ============================================================================

-- Performance indexes

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- RLS policies

-- ============================================================================
-- ROLLBACK SQL (for automated rollback support)
-- ============================================================================

-- ROLLBACK:
-- Your rollback SQL here
-- END ROLLBACK
```

## Security Features

### Row Level Security (RLS)

All sensitive tables have RLS enabled with policies for:
- **Patient Data Access**: Patients can only access their own data
- **Healthcare Provider Access**: Providers can access their patients' data
- **System Service Access**: Backend services can manage data
- **Admin Access**: Administrative users have appropriate permissions

### HIPAA Compliance

The system includes:
- **Audit Logging**: All data access and modifications are logged
- **Data Retention**: Configurable retention policies for sensor data
- **Data Anonymization**: Automatic anonymization of old patient data
- **Access Control**: Strict role-based access control
- **Encryption**: All cloud communications use HTTPS

### Data Validation

Comprehensive constraints ensure:
- **Sensor Data Ranges**: IMU angles (-180° to +180°), FSR values (0-4095)
- **Clinical Scores**: Severity scores (0-3), confidence levels (0.0-1.0)
- **Episode Data**: Positive durations, valid angle ranges
- **Threshold Progression**: Normal < Pusher < Severe thresholds
- **Date Validation**: Effective dates before expiry dates

## Troubleshooting

### Common Issues

#### Connection Errors
```bash
# Check database connection
psql -h localhost -U postgres -d vertex_db -c "SELECT 1;"
```

#### Permission Errors
```bash
# Ensure user has necessary permissions
GRANT CREATE, USAGE ON SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
```

#### Migration Checksum Errors
If a migration file is modified after application:
```bash
# Check migration status
python migrate.py status

# If needed, rollback and reapply
python migrate.py down 002
python migrate.py up
```

### Logging

Migration logs are written to:
- **Console**: Real-time progress and errors
- **migration.log**: Detailed log file with timestamps

### Recovery Procedures

#### Rollback Failed Migration
```bash
# Check what migrations are applied
python migrate.py status

# Rollback to last known good state
python migrate.py down <last_good_migration_id>

# Fix the issue and reapply
python migrate.py up
```

#### Schema Validation Failures
```bash
# Run validation to see specific issues
python validate_schema.py

# Check specific category
python validate_schema.py --constraints

# Fix issues and re-validate
python validate_schema.py
```

## Development Workflow

### Adding New Migrations

1. **Create Migration File**:
   ```bash
   python migrate.py create "Add new feature"
   ```

2. **Edit Migration File**:
   - Add your SQL changes
   - Include rollback SQL in comments
   - Add appropriate constraints and indexes
   - Include RLS policies if needed

3. **Test Migration**:
   ```bash
   # Apply migration
   python migrate.py up
   
   # Validate schema
   python validate_schema.py
   
   # Test rollback
   python migrate.py down <previous_migration>
   python migrate.py up
   ```

4. **Commit Changes**:
   ```bash
   git add backend/database/migrations/
   git commit -m "Add migration: description"
   ```

### Best Practices

1. **Always Test Rollbacks**: Ensure rollback SQL is correct
2. **Use Transactions**: Migrations run in transactions for safety
3. **Validate After Changes**: Run schema validation after migrations
4. **Document Changes**: Include clear descriptions and requirements
5. **Test with Data**: Test migrations with realistic data volumes
6. **Monitor Performance**: Check that new indexes improve query performance

## Production Deployment

### Pre-deployment Checklist

- [ ] All migrations tested in staging environment
- [ ] Schema validation passes
- [ ] Rollback procedures tested
- [ ] Database backup created
- [ ] Downtime window scheduled (if needed)

### Deployment Steps

1. **Backup Database**:
   ```bash
   pg_dump -h host -U user -d database > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Apply Migrations**:
   ```bash
   python migrate.py up
   ```

3. **Validate Schema**:
   ```bash
   python validate_schema.py
   ```

4. **Test Application**:
   - Verify API endpoints work
   - Test ESP32 data ingestion
   - Verify frontend functionality

### Monitoring

Monitor the following after deployment:
- Database performance metrics
- Query execution times
- RLS policy effectiveness
- Audit log entries
- Error rates in application logs

## Support

For issues with the migration system:

1. **Check Logs**: Review `migration.log` for detailed error information
2. **Validate Schema**: Run validation to identify specific issues
3. **Check Documentation**: Review this README and migration file comments
4. **Test in Development**: Reproduce issues in development environment

## Security Considerations

### Access Control
- Migration scripts should only be run by authorized personnel
- Database credentials should be securely managed
- Production access should be logged and monitored

### Data Protection
- All patient data is protected by RLS policies
- Audit logging tracks all data access
- Data retention policies ensure compliance
- Anonymization protects long-term research data

### Compliance
- HIPAA compliance through comprehensive audit trails
- Data validation ensures clinical data integrity
- Role-based access control protects sensitive information
- Secure communication channels for all data transfer