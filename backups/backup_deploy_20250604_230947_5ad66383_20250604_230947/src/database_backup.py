"""
Database Backup System for Karen AI
DATABASE-001 Implementation

Handles Firestore database backups, exports, and restoration.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import gzip
import shutil

class FirestoreBackup:
    """Handle Firestore database backup and restoration"""
    
    def __init__(self, db: firestore.Client, backup_dir: str = "backups"):
        self.db = db
        self.backup_dir = backup_dir
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"✅ Created backup directory: {self.backup_dir}")
    
    def backup_collection(self, collection_name: str) -> Dict[str, Any]:
        """Backup a single collection"""
        print(f"📦 Backing up collection: {collection_name}")
        
        collection_data = {
            'collection_name': collection_name,
            'backup_timestamp': datetime.now(timezone.utc).isoformat(),
            'documents': {}
        }
        
        try:
            docs = self.db.collection(collection_name).stream()
            doc_count = 0
            
            for doc in docs:
                doc_data = doc.to_dict()
                
                # Handle Firestore timestamps
                doc_data = self._serialize_firestore_data(doc_data)
                
                collection_data['documents'][doc.id] = {
                    'data': doc_data,
                    'id': doc.id,
                    'path': f"{collection_name}/{doc.id}"
                }
                doc_count += 1
            
            collection_data['document_count'] = doc_count
            print(f"✅ Backed up {doc_count} documents from {collection_name}")
            
        except Exception as e:
            print(f"❌ Failed to backup collection {collection_name}: {e}")
            raise
        
        return collection_data
    
    def backup_database(self, collections: Optional[List[str]] = None, compress: bool = True) -> str:
        """Backup entire database or specified collections"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"firestore_backup_{timestamp}.json"
        
        if compress:
            backup_filename += ".gz"
        
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        print(f"🔄 Starting database backup...")
        
        # Get all collections if none specified
        if collections is None:
            collections = self._get_all_collections()
        
        backup_data = {
            'backup_metadata': {
                'created_at': datetime.now(timezone.utc).isoformat(),
                'format_version': '1.0',
                'source': 'Karen AI Firestore',
                'total_collections': len(collections)
            },
            'collections': {}
        }
        
        total_documents = 0
        
        for collection_name in collections:
            try:
                collection_backup = self.backup_collection(collection_name)
                backup_data['collections'][collection_name] = collection_backup
                total_documents += collection_backup['document_count']
            except Exception as e:
                print(f"⚠️  Skipping collection {collection_name} due to error: {e}")
        
        backup_data['backup_metadata']['total_documents'] = total_documents
        
        # Write backup file
        try:
            if compress:
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(backup_path)
            print(f"✅ Database backup completed: {backup_path}")
            print(f"📊 Backup stats: {len(collections)} collections, {total_documents} documents, {file_size:,} bytes")
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Failed to write backup file: {e}")
            raise
    
    def restore_collection(self, collection_data: Dict[str, Any], overwrite: bool = False):
        """Restore a single collection from backup data"""
        collection_name = collection_data['collection_name']
        documents = collection_data['documents']
        
        print(f"🔄 Restoring collection: {collection_name}")
        
        if not overwrite:
            # Check if collection exists and has documents
            existing_docs = list(self.db.collection(collection_name).limit(1).stream())
            if existing_docs:
                response = input(f"Collection {collection_name} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print(f"⏭️  Skipping collection {collection_name}")
                    return
        
        restored_count = 0
        
        for doc_id, doc_info in documents.items():
            try:
                doc_data = doc_info['data']
                
                # Deserialize Firestore data
                doc_data = self._deserialize_firestore_data(doc_data)
                
                # Write document
                self.db.collection(collection_name).document(doc_id).set(doc_data)
                restored_count += 1
                
            except Exception as e:
                print(f"⚠️  Failed to restore document {doc_id}: {e}")
        
        print(f"✅ Restored {restored_count}/{len(documents)} documents to {collection_name}")
    
    def restore_database(self, backup_path: str, collections: Optional[List[str]] = None, overwrite: bool = False):
        """Restore database from backup file"""
        print(f"🔄 Starting database restoration from: {backup_path}")
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Load backup data
        try:
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load backup file: {e}")
            raise
        
        # Validate backup format
        if 'backup_metadata' not in backup_data or 'collections' not in backup_data:
            raise ValueError("Invalid backup file format")
        
        metadata = backup_data['backup_metadata']
        print(f"📋 Backup info: {metadata['created_at']}, {metadata['total_collections']} collections, {metadata['total_documents']} documents")
        
        # Restore collections
        collections_to_restore = collections or list(backup_data['collections'].keys())
        
        for collection_name in collections_to_restore:
            if collection_name in backup_data['collections']:
                try:
                    self.restore_collection(backup_data['collections'][collection_name], overwrite)
                except Exception as e:
                    print(f"⚠️  Failed to restore collection {collection_name}: {e}")
            else:
                print(f"⚠️  Collection {collection_name} not found in backup")
        
        print("✅ Database restoration completed")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backup files"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('firestore_backup_') and (filename.endswith('.json') or filename.endswith('.json.gz')):
                file_path = os.path.join(self.backup_dir, filename)
                file_stat = os.stat(file_path)
                
                backups.append({
                    'filename': filename,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime),
                    'compressed': filename.endswith('.gz')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backup files, keeping only the specified number"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            print(f"✅ No cleanup needed. {len(backups)} backups found, keeping {keep_count}")
            return
        
        backups_to_remove = backups[keep_count:]
        
        for backup in backups_to_remove:
            try:
                os.remove(backup['path'])
                print(f"🗑️  Removed old backup: {backup['filename']}")
            except Exception as e:
                print(f"⚠️  Failed to remove backup {backup['filename']}: {e}")
        
        print(f"✅ Cleanup completed. Removed {len(backups_to_remove)} old backups")
    
    def _get_all_collections(self) -> List[str]:
        """Get list of all collections in the database"""
        collections = []
        try:
            for collection in self.db.collections():
                collections.append(collection.id)
        except Exception as e:
            print(f"⚠️  Could not list collections: {e}")
            # Fallback to known collections
            collections = ['tasks', 'agents', 'customers', 'conversations', 'preferences', 'analytics']
        
        return collections
    
    def _serialize_firestore_data(self, data: Any) -> Any:
        """Convert Firestore data types to JSON-serializable format"""
        if isinstance(data, dict):
            return {k: self._serialize_firestore_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_firestore_data(item) for item in data]
        elif hasattr(data, 'timestamp'):  # Firestore timestamp
            return {'__firestore_timestamp__': data.timestamp()}
        elif hasattr(data, 'latitude') and hasattr(data, 'longitude'):  # GeoPoint
            return {'__firestore_geopoint__': {'latitude': data.latitude, 'longitude': data.longitude}}
        elif isinstance(data, bytes):
            return {'__firestore_bytes__': data.hex()}
        else:
            return data
    
    def _deserialize_firestore_data(self, data: Any) -> Any:
        """Convert JSON data back to Firestore data types"""
        if isinstance(data, dict):
            if '__firestore_timestamp__' in data:
                return firestore.SERVER_TIMESTAMP  # Use server timestamp for restoration
            elif '__firestore_geopoint__' in data:
                from google.cloud.firestore import GeoPoint
                geo_data = data['__firestore_geopoint__']
                return GeoPoint(geo_data['latitude'], geo_data['longitude'])
            elif '__firestore_bytes__' in data:
                return bytes.fromhex(data['__firestore_bytes__'])
            else:
                return {k: self._deserialize_firestore_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deserialize_firestore_data(item) for item in data]
        else:
            return data

def create_scheduled_backup(db: firestore.Client, backup_dir: str = "backups") -> str:
    """Create a scheduled backup (to be called by cron or task scheduler)"""
    backup_system = FirestoreBackup(db, backup_dir)
    
    # Create backup
    backup_path = backup_system.backup_database(compress=True)
    
    # Cleanup old backups (keep last 10)
    backup_system.cleanup_old_backups(keep_count=10)
    
    return backup_path

if __name__ == "__main__":
    from src.firebase_setup import setup_firebase
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python src/database_backup.py [backup|restore|list|cleanup] [options]")
        print("  backup [collections...]        - Backup database or specific collections")
        print("  restore <backup_file> [colls]  - Restore from backup file")
        print("  list                           - List available backups")
        print("  cleanup [keep_count]           - Remove old backups")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        db = setup_firebase()
        backup_system = FirestoreBackup(db)
        
        if action == 'backup':
            collections = sys.argv[2:] if len(sys.argv) > 2 else None
            backup_path = backup_system.backup_database(collections)
            print(f"🎉 Backup completed: {backup_path}")
            
        elif action == 'restore':
            if len(sys.argv) < 3:
                print("Error: Backup file path required")
                sys.exit(1)
            
            backup_file = sys.argv[2]
            collections = sys.argv[3:] if len(sys.argv) > 3 else None
            backup_system.restore_database(backup_file, collections)
            
        elif action == 'list':
            backups = backup_system.list_backups()
            if backups:
                print("📋 Available backups:")
                for backup in backups:
                    size_mb = backup['size'] / 1024 / 1024
                    compress_flag = " (compressed)" if backup['compressed'] else ""
                    print(f"  - {backup['filename']}: {size_mb:.1f} MB, {backup['created_at']}{compress_flag}")
            else:
                print("No backups found")
                
        elif action == 'cleanup':
            keep_count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            backup_system.cleanup_old_backups(keep_count)
            
        else:
            print("Invalid action. Use 'backup', 'restore', 'list', or 'cleanup'")
            sys.exit(1)
            
    except Exception as e:
        print(f"Backup operation failed: {e}")
        sys.exit(1)