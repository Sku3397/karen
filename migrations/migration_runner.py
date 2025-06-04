"""
Migration Runner for Karen AI Database
DATABASE-001 Implementation

Handles running and tracking database migrations.
"""

import os
import importlib.util
from typing import List, Dict
from google.cloud import firestore
from datetime import datetime

class MigrationRunner:
    """Handles database migration execution and tracking"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.migrations_dir = 'migrations'
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations from Firestore"""
        try:
            migrations = []
            docs = self.db.collection('_migrations').stream()
            for doc in docs:
                data = doc.to_dict()
                if data.get('status') == 'completed':
                    migrations.append(doc.id)
            return sorted(migrations)
        except Exception as e:
            print(f"Warning: Could not read applied migrations: {e}")
            return []
    
    def get_available_migrations(self) -> List[str]:
        """Get list of available migration files"""
        migrations = []
        
        if not os.path.exists(self.migrations_dir):
            print(f"Migrations directory not found: {self.migrations_dir}")
            return migrations
        
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.py') and filename != '__init__.py' and filename != 'migration_runner.py':
                # Extract migration ID from filename (e.g., "001_initial_schema.py" -> "001_initial_schema")
                migration_id = filename[:-3]
                migrations.append(migration_id)
        
        return sorted(migrations)
    
    def get_pending_migrations(self) -> List[str]:
        """Get list of migrations that haven't been applied"""
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        return [m for m in available if m not in applied]
    
    def load_migration_module(self, migration_id: str):
        """Load a migration module dynamically"""
        migration_file = os.path.join(self.migrations_dir, f"{migration_id}.py")
        
        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        spec = importlib.util.spec_from_file_location(migration_id, migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def apply_migration(self, migration_id: str) -> bool:
        """Apply a single migration"""
        try:
            print(f"🔄 Applying migration: {migration_id}")
            
            # Load migration module
            module = self.load_migration_module(migration_id)
            
            # Check if migration has required functions
            if not hasattr(module, 'up'):
                raise AttributeError(f"Migration {migration_id} missing 'up' function")
            
            # Mark migration as in progress
            migration_ref = self.db.collection('_migrations').document(migration_id)
            migration_ref.set({
                'migration_id': migration_id,
                'applied_at': firestore.SERVER_TIMESTAMP,
                'status': 'in_progress',
                'description': getattr(module, '__doc__', '').strip() if hasattr(module, '__doc__') else ''
            })
            
            # Run the migration
            module.up(self.db)
            
            # Mark migration as completed
            migration_ref.update({
                'status': 'completed',
                'completed_at': firestore.SERVER_TIMESTAMP
            })
            
            print(f"✅ Migration {migration_id} applied successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply migration {migration_id}: {e}")
            
            # Mark migration as failed
            try:
                migration_ref = self.db.collection('_migrations').document(migration_id)
                migration_ref.update({
                    'status': 'failed',
                    'error': str(e),
                    'failed_at': firestore.SERVER_TIMESTAMP
                })
            except:
                pass
            
            return False
    
    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a single migration"""
        try:
            print(f"🔄 Rolling back migration: {migration_id}")
            
            # Load migration module
            module = self.load_migration_module(migration_id)
            
            # Check if migration has rollback function
            if not hasattr(module, 'down'):
                print(f"⚠️  Migration {migration_id} has no 'down' function - cannot rollback")
                return False
            
            # Run the rollback
            module.down(self.db)
            
            # Remove migration tracking document
            migration_ref = self.db.collection('_migrations').document(migration_id)
            migration_ref.delete()
            
            print(f"✅ Migration {migration_id} rolled back successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to rollback migration {migration_id}: {e}")
            return False
    
    def migrate_up(self, target_migration: str = None) -> bool:
        """Apply all pending migrations or up to a specific migration"""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✅ No pending migrations")
            return True
        
        migrations_to_apply = pending
        if target_migration:
            if target_migration in pending:
                # Apply only up to target migration
                idx = pending.index(target_migration)
                migrations_to_apply = pending[:idx + 1]
            else:
                print(f"❌ Target migration {target_migration} not found in pending migrations")
                return False
        
        print(f"📋 Applying {len(migrations_to_apply)} migrations: {migrations_to_apply}")
        
        success_count = 0
        for migration_id in migrations_to_apply:
            if self.apply_migration(migration_id):
                success_count += 1
            else:
                print(f"💥 Migration failed, stopping at {migration_id}")
                break
        
        print(f"✅ Applied {success_count}/{len(migrations_to_apply)} migrations")
        return success_count == len(migrations_to_apply)
    
    def migrate_down(self, target_migration: str = None, steps: int = 1) -> bool:
        """Rollback migrations"""
        applied = self.get_applied_migrations()
        
        if not applied:
            print("✅ No migrations to rollback")
            return True
        
        migrations_to_rollback = []
        if target_migration:
            if target_migration in applied:
                # Rollback to target (exclusive)
                idx = applied.index(target_migration)
                migrations_to_rollback = applied[idx + 1:]
            else:
                print(f"❌ Target migration {target_migration} not found in applied migrations")
                return False
        else:
            # Rollback specified number of steps
            migrations_to_rollback = applied[-steps:]
        
        # Reverse order for rollback
        migrations_to_rollback.reverse()
        
        print(f"📋 Rolling back {len(migrations_to_rollback)} migrations: {migrations_to_rollback}")
        
        success_count = 0
        for migration_id in migrations_to_rollback:
            if self.rollback_migration(migration_id):
                success_count += 1
            else:
                print(f"💥 Rollback failed, stopping at {migration_id}")
                break
        
        print(f"✅ Rolled back {success_count}/{len(migrations_to_rollback)} migrations")
        return success_count == len(migrations_to_rollback)
    
    def status(self):
        """Show migration status"""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        print("📊 Migration Status:")
        print(f"   Available: {len(available)}")
        print(f"   Applied:   {len(applied)}")
        print(f"   Pending:   {len(pending)}")
        
        if applied:
            print("\n✅ Applied migrations:")
            for migration in applied:
                print(f"   - {migration}")
        
        if pending:
            print("\n⏳ Pending migrations:")
            for migration in pending:
                print(f"   - {migration}")

if __name__ == "__main__":
    from src.firebase_setup import setup_firebase
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/migration_runner.py [up|down|status] [options]")
        print("  up [migration]     - Apply all or specific migration")
        print("  down [migration]   - Rollback to migration (or 1 step)")
        print("  status             - Show migration status")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        db = setup_firebase()
        runner = MigrationRunner(db)
        
        if action == 'up':
            target = sys.argv[2] if len(sys.argv) > 2 else None
            runner.migrate_up(target)
        elif action == 'down':
            target = sys.argv[2] if len(sys.argv) > 2 else None
            if target and target.isdigit():
                runner.migrate_down(steps=int(target))
            else:
                runner.migrate_down(target)
        elif action == 'status':
            runner.status()
        else:
            print("Invalid action. Use 'up', 'down', or 'status'")
            sys.exit(1)
            
    except Exception as e:
        print(f"Migration runner failed: {e}")
        sys.exit(1)