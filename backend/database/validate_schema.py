#!/usr/bin/env python3
"""
Database Schema Validation Script
Verifies that all migrations have been applied correctly and the database schema
meets the requirements for HIPAA compliance and clinical data security.

Usage:
    python validate_schema.py              # Run all validations
    python validate_schema.py --tables     # Validate table structure only
    python validate_schema.py --policies   # Validate RLS policies only
    python validate_schema.py --constraints # Validate constraints only
    python validate_schema.py --indexes    # Validate indexes only
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class SchemaValidator:
    """
    Comprehensive database schema validator for Vertex Data Integration.
    Ensures HIPAA compliance, clinical data security, and proper migration application.
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self.validation_results = {
            'tables': {'passed': 0, 'failed': 0, 'errors': []},
            'columns': {'passed': 0, 'failed': 0, 'errors': []},
            'constraints': {'passed': 0, 'failed': 0, 'errors': []},
            'indexes': {'passed': 0, 'failed': 0, 'errors': []},
            'policies': {'passed': 0, 'failed': 0, 'errors': []},
            'functions': {'passed': 0, 'failed': 0, 'errors': []},
            'triggers': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connection established")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise ValidationError(f"Database connection failed: {e}")
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise ValidationError(f"Query failed: {e}")
    
    def check_exists(self, query: str, params: tuple = None) -> bool:
        """Check if query returns any results"""
        try:
            results = self.execute_query(query, params)
            return len(results) > 0
        except ValidationError:
            return False
    
    def validate_table_exists(self, table_name: str, description: str = None) -> bool:
        """Validate that a table exists"""
        query = """
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        """
        
        exists = self.check_exists(query, (table_name,))
        
        if exists:
            self.validation_results['tables']['passed'] += 1
            logger.info(f"✓ Table '{table_name}' exists")
        else:
            self.validation_results['tables']['failed'] += 1
            error_msg = f"✗ Table '{table_name}' missing"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['tables']['errors'].append(error_msg)
        
        return exists
    
    def validate_column_exists(self, table_name: str, column_name: str, 
                             expected_type: str = None, description: str = None) -> bool:
        """Validate that a column exists with correct type"""
        query = """
            SELECT data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s 
            AND column_name = %s
        """
        
        results = self.execute_query(query, (table_name, column_name))
        
        if not results:
            self.validation_results['columns']['failed'] += 1
            error_msg = f"✗ Column '{table_name}.{column_name}' missing"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['columns']['errors'].append(error_msg)
            return False
        
        column_info = results[0]
        
        # Check data type if specified
        if expected_type and column_info['data_type'] != expected_type:
            self.validation_results['columns']['failed'] += 1
            error_msg = f"✗ Column '{table_name}.{column_name}' has type '{column_info['data_type']}', expected '{expected_type}'"
            logger.error(error_msg)
            self.validation_results['columns']['errors'].append(error_msg)
            return False
        
        self.validation_results['columns']['passed'] += 1
        logger.info(f"✓ Column '{table_name}.{column_name}' exists with correct type")
        return True
    
    def validate_constraint_exists(self, constraint_name: str, table_name: str = None, 
                                 description: str = None) -> bool:
        """Validate that a constraint exists"""
        if table_name:
            query = """
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = %s AND table_name = %s
            """
            params = (constraint_name, table_name)
        else:
            query = """
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = %s
            """
            params = (constraint_name,)
        
        exists = self.check_exists(query, params)
        
        if exists:
            self.validation_results['constraints']['passed'] += 1
            logger.info(f"✓ Constraint '{constraint_name}' exists")
        else:
            self.validation_results['constraints']['failed'] += 1
            error_msg = f"✗ Constraint '{constraint_name}' missing"
            if table_name:
                error_msg += f" on table '{table_name}'"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['constraints']['errors'].append(error_msg)
        
        return exists
    
    def validate_index_exists(self, index_name: str, table_name: str = None, 
                            description: str = None) -> bool:
        """Validate that an index exists"""
        if table_name:
            query = """
                SELECT 1 FROM pg_indexes 
                WHERE indexname = %s AND tablename = %s
            """
            params = (index_name, table_name)
        else:
            query = """
                SELECT 1 FROM pg_indexes 
                WHERE indexname = %s
            """
            params = (index_name,)
        
        exists = self.check_exists(query, params)
        
        if exists:
            self.validation_results['indexes']['passed'] += 1
            logger.info(f"✓ Index '{index_name}' exists")
        else:
            self.validation_results['indexes']['failed'] += 1
            error_msg = f"✗ Index '{index_name}' missing"
            if table_name:
                error_msg += f" on table '{table_name}'"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['indexes']['errors'].append(error_msg)
        
        return exists
    
    def validate_rls_enabled(self, table_name: str, description: str = None) -> bool:
        """Validate that Row Level Security is enabled on a table"""
        query = """
            SELECT 1 FROM pg_tables 
            WHERE tablename = %s AND rowsecurity = true
        """
        
        exists = self.check_exists(query, (table_name,))
        
        if exists:
            self.validation_results['policies']['passed'] += 1
            logger.info(f"✓ RLS enabled on table '{table_name}'")
        else:
            self.validation_results['policies']['failed'] += 1
            error_msg = f"✗ RLS not enabled on table '{table_name}'"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['policies']['errors'].append(error_msg)
        
        return exists
    
    def validate_policy_exists(self, policy_name: str, table_name: str, 
                             description: str = None) -> bool:
        """Validate that a specific RLS policy exists"""
        query = """
            SELECT 1 FROM pg_policies 
            WHERE policyname = %s AND tablename = %s
        """
        
        exists = self.check_exists(query, (policy_name, table_name))
        
        if exists:
            self.validation_results['policies']['passed'] += 1
            logger.info(f"✓ Policy '{policy_name}' exists on table '{table_name}'")
        else:
            self.validation_results['policies']['failed'] += 1
            error_msg = f"✗ Policy '{policy_name}' missing on table '{table_name}'"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['policies']['errors'].append(error_msg)
        
        return exists
    
    def validate_function_exists(self, function_name: str, description: str = None) -> bool:
        """Validate that a function exists"""
        query = """
            SELECT 1 FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public' AND p.proname = %s
        """
        
        exists = self.check_exists(query, (function_name,))
        
        if exists:
            self.validation_results['functions']['passed'] += 1
            logger.info(f"✓ Function '{function_name}' exists")
        else:
            self.validation_results['functions']['failed'] += 1
            error_msg = f"✗ Function '{function_name}' missing"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['functions']['errors'].append(error_msg)
        
        return exists
    
    def validate_trigger_exists(self, trigger_name: str, table_name: str, 
                              description: str = None) -> bool:
        """Validate that a trigger exists"""
        query = """
            SELECT 1 FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            WHERE t.tgname = %s AND c.relname = %s
        """
        
        exists = self.check_exists(query, (trigger_name, table_name))
        
        if exists:
            self.validation_results['triggers']['passed'] += 1
            logger.info(f"✓ Trigger '{trigger_name}' exists on table '{table_name}'")
        else:
            self.validation_results['triggers']['failed'] += 1
            error_msg = f"✗ Trigger '{trigger_name}' missing on table '{table_name}'"
            if description:
                error_msg += f" - {description}"
            logger.error(error_msg)
            self.validation_results['triggers']['errors'].append(error_msg)
        
        return exists
    
    def validate_tables(self) -> bool:
        """Validate all required tables exist"""
        logger.info("=== Validating Tables ===")
        
        tables = [
            ('patients', 'Patient profiles and authentication'),
            ('sensor_readings', 'Device sensor readings'),
            ('monitoring_sessions', 'Patient monitoring sessions'),
            ('device_calibrations', 'Device calibration settings'),
            ('pusher_episodes', 'Clinical episode tracking with severity scoring'),
            ('clinical_thresholds', 'Patient-specific clinical parameters'),
            ('esp32_devices', 'ESP32 device registry and connection tracking'),
            ('patient_provider_relationships', 'Healthcare team management'),
            ('audit_log', 'HIPAA compliance audit logging'),
            ('schema_migrations', 'Migration tracking table')
        ]
        
        all_passed = True
        for table_name, description in tables:
            if not self.validate_table_exists(table_name, description):
                all_passed = False
        
        return all_passed
    
    def validate_columns(self) -> bool:
        """Validate critical columns exist with correct types"""
        logger.info("=== Validating Columns ===")
        
        columns = [
            # sensor_readings enhancements
            ('sensor_readings', 'device_id', 'character varying', 'ESP32 device identifier'),
            ('sensor_readings', 'pusher_detected', 'boolean', 'Pusher syndrome detection flag'),
            ('sensor_readings', 'confidence_level', 'double precision', 'Detection confidence level'),
            ('sensor_readings', 'clinical_score', 'integer', 'Clinical severity score'),
            ('sensor_readings', 'episode_id', 'uuid', 'Link to pusher episode'),
            ('sensor_readings', 'tilt_direction', 'character varying', 'Tilt direction classification'),
            ('sensor_readings', 'weight_ratio', 'double precision', 'FSR weight distribution ratio'),
            
            # pusher_episodes table
            ('pusher_episodes', 'severity_score', 'integer', 'BLS/4PPS compatible severity score'),
            ('pusher_episodes', 'max_tilt_angle', 'double precision', 'Maximum tilt angle during episode'),
            ('pusher_episodes', 'resistance_index', 'double precision', 'Resistance to correction'),
            ('pusher_episodes', 'episode_duration_seconds', 'double precision', 'Episode duration'),
            ('pusher_episodes', 'tilt_direction', 'character varying', 'Tilt direction'),
            
            # clinical_thresholds table
            ('clinical_thresholds', 'paretic_side', 'character varying', 'Patient paretic side'),
            ('clinical_thresholds', 'normal_threshold', 'double precision', 'Normal posture threshold'),
            ('clinical_thresholds', 'pusher_threshold', 'double precision', 'Pusher detection threshold'),
            ('clinical_thresholds', 'severe_threshold', 'double precision', 'Severe episode threshold'),
            ('clinical_thresholds', 'created_by', 'character varying', 'Therapist authorization'),
            
            # esp32_devices table
            ('esp32_devices', 'device_id', 'character varying', 'Unique device identifier'),
            ('esp32_devices', 'connection_status', 'character varying', 'Device connection status'),
            ('esp32_devices', 'last_seen', 'timestamp with time zone', 'Last communication timestamp'),
            ('esp32_devices', 'patient_id', 'uuid', 'Assigned patient'),
            
            # device_calibrations enhancements
            ('device_calibrations', 'baseline_fsr_left', 'double precision', 'FSR left baseline'),
            ('device_calibrations', 'baseline_fsr_right', 'double precision', 'FSR right baseline'),
            ('device_calibrations', 'baseline_fsr_ratio', 'double precision', 'FSR ratio baseline'),
            ('device_calibrations', 'pitch_std_dev', 'double precision', 'Pitch standard deviation'),
            ('device_calibrations', 'validation_status', 'character varying', 'Calibration validation status'),
            
            # audit_log table
            ('audit_log', 'table_name', 'character varying', 'Audited table name'),
            ('audit_log', 'operation', 'character varying', 'Database operation'),
            ('audit_log', 'user_id', 'uuid', 'User performing operation'),
            ('audit_log', 'changed_fields', 'jsonb', 'Changed fields data'),
            
            # patient_provider_relationships table
            ('patient_provider_relationships', 'provider_type', 'character varying', 'Healthcare provider type'),
            ('patient_provider_relationships', 'access_level', 'character varying', 'Access permission level'),
            ('patient_provider_relationships', 'is_active', 'boolean', 'Relationship active status')
        ]
        
        all_passed = True
        for table_name, column_name, expected_type, description in columns:
            if not self.validate_column_exists(table_name, column_name, expected_type, description):
                all_passed = False
        
        return all_passed
    
    def validate_constraints(self) -> bool:
        """Validate data validation constraints"""
        logger.info("=== Validating Constraints ===")
        
        constraints = [
            # sensor_readings constraints
            ('check_imu_pitch_range', 'sensor_readings', 'IMU pitch angle range validation'),
            ('check_fsr_left_range', 'sensor_readings', 'FSR left sensor range validation'),
            ('check_fsr_right_range', 'sensor_readings', 'FSR right sensor range validation'),
            ('check_confidence_level_range', 'sensor_readings', 'Confidence level range validation'),
            ('check_clinical_score_range', 'sensor_readings', 'Clinical score range validation'),
            
            # pusher_episodes constraints
            ('check_episode_duration_positive', 'pusher_episodes', 'Episode duration positive validation'),
            ('check_episode_start_before_end', 'pusher_episodes', 'Episode timing validation'),
            ('check_max_tilt_angle_range', 'pusher_episodes', 'Tilt angle range validation'),
            
            # clinical_thresholds constraints
            ('check_threshold_progression', 'clinical_thresholds', 'Threshold progression validation'),
            ('check_effective_before_expiry', 'clinical_thresholds', 'Date range validation'),
            
            # esp32_devices constraints
            ('check_battery_level_range', 'esp32_devices', 'Battery level range validation'),
            ('check_total_uptime_positive', 'esp32_devices', 'Uptime positive validation'),
            
            # Foreign key constraints
            ('fk_sensor_readings_episode', 'sensor_readings', 'Episode foreign key'),
            ('pusher_episodes_patient_id_fkey', 'pusher_episodes', 'Patient foreign key'),
            ('clinical_thresholds_patient_id_fkey', 'clinical_thresholds', 'Patient foreign key')
        ]
        
        all_passed = True
        for constraint_name, table_name, description in constraints:
            if not self.validate_constraint_exists(constraint_name, table_name, description):
                all_passed = False
        
        return all_passed
    
    def validate_indexes(self) -> bool:
        """Validate performance indexes"""
        logger.info("=== Validating Indexes ===")
        
        indexes = [
            # Original indexes
            ('idx_sensor_readings_patient_timestamp', 'sensor_readings', 'Patient timestamp index'),
            ('idx_monitoring_sessions_patient', 'monitoring_sessions', 'Patient sessions index'),
            ('idx_device_calibrations_patient_active', 'device_calibrations', 'Patient calibrations index'),
            
            # New clinical indexes
            ('idx_pusher_episodes_patient_date', 'pusher_episodes', 'Patient episodes by date'),
            ('idx_clinical_thresholds_patient_active', 'clinical_thresholds', 'Active patient thresholds'),
            ('idx_esp32_devices_status', 'esp32_devices', 'Device connection status'),
            ('idx_sensor_readings_episode', 'sensor_readings', 'Episode sensor readings'),
            ('idx_sensor_readings_pusher', 'sensor_readings', 'Pusher detection index'),
            
            # Audit and relationship indexes
            ('idx_audit_log_table_timestamp', 'audit_log', 'Audit log by table and time'),
            ('idx_patient_provider_relationships_patient', 'patient_provider_relationships', 'Patient relationships')
        ]
        
        all_passed = True
        for index_name, table_name, description in indexes:
            if not self.validate_index_exists(index_name, table_name, description):
                all_passed = False
        
        return all_passed
    
    def validate_rls_policies(self) -> bool:
        """Validate Row Level Security policies"""
        logger.info("=== Validating RLS Policies ===")
        
        # First check RLS is enabled on critical tables
        rls_tables = [
            ('patients', 'Patient data protection'),
            ('sensor_readings', 'Sensor data protection'),
            ('pusher_episodes', 'Clinical episode protection'),
            ('clinical_thresholds', 'Clinical threshold protection'),
            ('esp32_devices', 'Device data protection'),
            ('audit_log', 'Audit log protection'),
            ('patient_provider_relationships', 'Healthcare team protection')
        ]
        
        all_passed = True
        for table_name, description in rls_tables:
            if not self.validate_rls_enabled(table_name, description):
                all_passed = False
        
        # Check specific policies exist
        policies = [
            # sensor_readings policies
            ('patients_view_own_sensor_readings', 'sensor_readings', 'Patient sensor data access'),
            ('patients_insert_own_sensor_readings', 'sensor_readings', 'Patient sensor data insertion'),
            ('system_service_manage_sensor_readings', 'sensor_readings', 'System service access'),
            
            # pusher_episodes policies
            ('patients_view_own_pusher_episodes', 'pusher_episodes', 'Patient episode access'),
            ('healthcare_providers_manage_patient_episodes', 'pusher_episodes', 'Provider episode management'),
            ('system_service_create_episodes', 'pusher_episodes', 'System episode creation'),
            
            # clinical_thresholds policies
            ('patients_view_own_clinical_thresholds', 'clinical_thresholds', 'Patient threshold access'),
            ('therapists_manage_clinical_thresholds', 'clinical_thresholds', 'Therapist threshold management'),
            
            # esp32_devices policies
            ('patients_view_assigned_devices', 'esp32_devices', 'Patient device access'),
            ('system_service_manage_all_devices', 'esp32_devices', 'System device management'),
            
            # audit_log policies
            ('admins_view_audit_log', 'audit_log', 'Admin audit access'),
            
            # patient_provider_relationships policies
            ('patients_view_own_healthcare_team', 'patient_provider_relationships', 'Patient team access'),
            ('admins_manage_provider_relationships', 'patient_provider_relationships', 'Admin relationship management')
        ]
        
        for policy_name, table_name, description in policies:
            if not self.validate_policy_exists(policy_name, table_name, description):
                all_passed = False
        
        return all_passed
    
    def validate_functions(self) -> bool:
        """Validate database functions"""
        logger.info("=== Validating Functions ===")
        
        functions = [
            ('update_updated_at_column', 'Automatic timestamp update function'),
            ('handle_new_user', 'User profile creation function'),
            ('create_audit_log_entry', 'Audit logging function'),
            ('cleanup_old_sensor_readings', 'Data retention function'),
            ('anonymize_old_patient_data', 'Data anonymization function'),
            ('validate_user_permissions', 'Permission validation function'),
            ('calculate_episode_statistics', 'Episode statistics calculation'),
            ('validate_clinical_thresholds', 'Threshold validation function')
        ]
        
        all_passed = True
        for function_name, description in functions:
            if not self.validate_function_exists(function_name, description):
                all_passed = False
        
        return all_passed
    
    def validate_triggers(self) -> bool:
        """Validate database triggers"""
        logger.info("=== Validating Triggers ===")
        
        triggers = [
            ('update_patients_updated_at', 'patients', 'Patient timestamp trigger'),
            ('update_pusher_episodes_updated_at', 'pusher_episodes', 'Episode timestamp trigger'),
            ('update_clinical_thresholds_updated_at', 'clinical_thresholds', 'Threshold timestamp trigger'),
            ('update_esp32_devices_updated_at', 'esp32_devices', 'Device timestamp trigger'),
            ('audit_patients_trigger', 'patients', 'Patient audit trigger'),
            ('audit_sensor_readings_trigger', 'sensor_readings', 'Sensor readings audit trigger'),
            ('audit_pusher_episodes_trigger', 'pusher_episodes', 'Episode audit trigger'),
            ('audit_clinical_thresholds_trigger', 'clinical_thresholds', 'Threshold audit trigger'),
            ('calculate_pusher_episode_stats', 'pusher_episodes', 'Episode statistics trigger'),
            ('validate_clinical_thresholds_trigger', 'clinical_thresholds', 'Threshold validation trigger')
        ]
        
        all_passed = True
        for trigger_name, table_name, description in triggers:
            if not self.validate_trigger_exists(trigger_name, table_name, description):
                all_passed = False
        
        return all_passed
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        logger.info("Starting comprehensive schema validation...")
        
        validations = [
            ('Tables', self.validate_tables),
            ('Columns', self.validate_columns),
            ('Constraints', self.validate_constraints),
            ('Indexes', self.validate_indexes),
            ('RLS Policies', self.validate_rls_policies),
            ('Functions', self.validate_functions),
            ('Triggers', self.validate_triggers)
        ]
        
        all_passed = True
        for validation_name, validation_func in validations:
            try:
                if not validation_func():
                    all_passed = False
            except Exception as e:
                logger.error(f"Validation '{validation_name}' failed with error: {e}")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.validation_results.items():
            passed = results['passed']
            failed = results['failed']
            total_passed += passed
            total_failed += failed
            
            status = "✓ PASS" if failed == 0 else "✗ FAIL"
            print(f"{category.upper():<15} {status:<8} ({passed} passed, {failed} failed)")
            
            # Print errors if any
            if results['errors']:
                for error in results['errors'][:3]:  # Show first 3 errors
                    print(f"  - {error}")
                if len(results['errors']) > 3:
                    print(f"  - ... and {len(results['errors']) - 3} more errors")
        
        print("-" * 80)
        overall_status = "✓ PASS" if total_failed == 0 else "✗ FAIL"
        print(f"OVERALL         {overall_status:<8} ({total_passed} passed, {total_failed} failed)")
        
        if total_failed == 0:
            print("\n🎉 All validations passed! Database schema is ready for production.")
        else:
            print(f"\n⚠️  {total_failed} validation(s) failed. Please review and fix the issues above.")
        
        print("="*80)

def get_database_url() -> str:
    """Get database connection string from environment"""
    db_url = (
        os.getenv('DATABASE_URL') or
        os.getenv('SUPABASE_DB_URL') or
        os.getenv('POSTGRES_URL')
    )
    
    if not db_url:
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'postgres')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    return db_url

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Database Schema Validator')
    parser.add_argument('--tables', action='store_true', help='Validate tables only')
    parser.add_argument('--columns', action='store_true', help='Validate columns only')
    parser.add_argument('--constraints', action='store_true', help='Validate constraints only')
    parser.add_argument('--indexes', action='store_true', help='Validate indexes only')
    parser.add_argument('--policies', action='store_true', help='Validate RLS policies only')
    parser.add_argument('--functions', action='store_true', help='Validate functions only')
    parser.add_argument('--triggers', action='store_true', help='Validate triggers only')
    
    args = parser.parse_args()
    
    try:
        db_url = get_database_url()
        validator = SchemaValidator(db_url)
        validator.connect()
        
        success = True
        
        # Run specific validations if requested
        if args.tables:
            success = validator.validate_tables()
        elif args.columns:
            success = validator.validate_columns()
        elif args.constraints:
            success = validator.validate_constraints()
        elif args.indexes:
            success = validator.validate_indexes()
        elif args.policies:
            success = validator.validate_rls_policies()
        elif args.functions:
            success = validator.validate_functions()
        elif args.triggers:
            success = validator.validate_triggers()
        else:
            # Run all validations
            success = validator.run_all_validations()
        
        validator.print_summary()
        validator.disconnect()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())