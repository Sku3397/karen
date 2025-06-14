#!/usr/bin/env python3
"""
Eigencode Knowledge Base Optimizer - Autonomous cleanup and consolidation
Part of the Karen AI Eigencode Loop System
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import hashlib
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseOptimizer:
    """Autonomous optimizer for the Karen knowledge base system."""
    
    def __init__(self, knowledge_base_path: str = "autonomous-agents/communication/knowledge-base"):
        self.kb_path = Path(knowledge_base_path)
        self.archive_path = Path("autonomous-agents/communication/archived-knowledge")
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # Optimization thresholds
        self.max_files = 100  # Maximum active knowledge files
        self.max_age_days = 7  # Archive files older than this
        self.similarity_threshold = 0.8  # Merge similar knowledge entries
        
    def analyze_knowledge_base(self) -> Dict[str, Any]:
        """Analyze current knowledge base state."""
        if not self.kb_path.exists():
            return {"error": "Knowledge base path not found"}
            
        files = list(self.kb_path.glob("*.json"))
        total_files = len(files)
        
        # Analyze file ages
        now = datetime.now()
        file_ages = []
        old_files = []
        
        for file_path in files:
            try:
                # Extract timestamp from filename pattern
                timestamp_str = self._extract_timestamp_from_filename(file_path.name)
                if timestamp_str:
                    file_time = datetime.fromisoformat(timestamp_str.replace('_', ':'))
                    age_days = (now - file_time).days
                    file_ages.append(age_days)
                    
                    if age_days > self.max_age_days:
                        old_files.append(file_path)
                else:
                    # Fallback to file modification time
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    age_days = (now - mod_time).days
                    file_ages.append(age_days)
                    
                    if age_days > self.max_age_days:
                        old_files.append(file_path)
                        
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                old_files.append(file_path)  # Archive problematic files
        
        return {
            "total_files": total_files,
            "old_files": len(old_files),
            "avg_age_days": sum(file_ages) / len(file_ages) if file_ages else 0,
            "max_age_days": max(file_ages) if file_ages else 0,
            "files_to_archive": old_files,
            "optimization_needed": total_files > self.max_files
        }
    
    def _extract_timestamp_from_filename(self, filename: str) -> str:
        """Extract timestamp from knowledge base filename pattern."""
        # Pattern: agent_name_YYYYMMDD_HHMMSS_ID.json
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 3:
            # Look for date pattern (8 digits) and time pattern (6 digits)
            for i, part in enumerate(parts):
                if len(part) == 8 and part.isdigit():  # Date part
                    if i + 1 < len(parts) and len(parts[i + 1]) == 6 and parts[i + 1].isdigit():
                        date_str = part
                        time_str = parts[i + 1]
                        # Convert to ISO format
                        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{time_str[:2]}_{time_str[2:4]}_{time_str[4:6]}"
        return None
    
    def consolidate_similar_knowledge(self, files: List[Path]) -> Dict[str, Any]:
        """Find and consolidate similar knowledge entries."""
        knowledge_groups = defaultdict(list)
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Create content hash for similarity detection
                content_hash = self._create_content_hash(data)
                knowledge_groups[content_hash].append({
                    'file': file_path,
                    'data': data,
                    'size': file_path.stat().st_size
                })
                
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
        
        consolidations = []
        for content_hash, group in knowledge_groups.items():
            if len(group) > 1:
                # Keep the largest/most complete file, archive others
                group.sort(key=lambda x: x['size'], reverse=True)
                primary = group[0]
                duplicates = group[1:]
                
                consolidations.append({
                    'primary_file': primary['file'],
                    'duplicate_files': [item['file'] for item in duplicates],
                    'content_hash': content_hash
                })
        
        return {
            'total_groups': len(knowledge_groups),
            'duplicate_groups': len(consolidations),
            'consolidations': consolidations
        }
    
    def _create_content_hash(self, data: Dict[str, Any]) -> str:
        """Create a hash representing the content structure."""
        # Extract key fields for comparison
        key_fields = {
            'agent_name': data.get('agent_name', ''),
            'activity_type': data.get('activity_type', ''),
            'topic': data.get('topic', ''),
            'status': data.get('status', ''),
            'type': data.get('type', '')
        }
        
        # Create hash from key fields
        content_str = json.dumps(key_fields, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()[:8]
    
    def archive_old_files(self, files_to_archive: List[Path]) -> Dict[str, Any]:
        """Archive old knowledge files."""
        archive_date = datetime.now().strftime("%Y%m%d")
        archive_dir = self.archive_path / f"archive_{archive_date}"
        archive_dir.mkdir(exist_ok=True)
        
        archived_count = 0
        archived_size = 0
        errors = []
        
        for file_path in files_to_archive:
            try:
                # Move file to archive
                archive_file = archive_dir / file_path.name
                file_path.rename(archive_file)
                
                archived_count += 1
                archived_size += archive_file.stat().st_size
                
            except Exception as e:
                errors.append(f"Error archiving {file_path}: {e}")
                logger.error(f"Error archiving {file_path}: {e}")
        
        return {
            'archived_count': archived_count,
            'archived_size_bytes': archived_size,
            'archive_directory': str(archive_dir),
            'errors': errors
        }
    
    def optimize_knowledge_base(self) -> Dict[str, Any]:
        """Perform complete knowledge base optimization."""
        logger.info("🧠 Starting eigencode knowledge base optimization...")
        
        # Phase 1: Analyze current state
        analysis = self.analyze_knowledge_base()
        logger.info(f"Analysis: {analysis['total_files']} files, {analysis['old_files']} old files")
        
        results = {'analysis': analysis}
        
        # Phase 2: Archive old files if needed
        if analysis.get('files_to_archive'):
            archive_results = self.archive_old_files(analysis['files_to_archive'])
            results['archival'] = archive_results
            logger.info(f"Archived {archive_results['archived_count']} old files")
        
        # Phase 3: Consolidate similar knowledge (on remaining files)
        remaining_files = [f for f in self.kb_path.glob("*.json")]
        if len(remaining_files) > self.max_files:
            consolidation_results = self.consolidate_similar_knowledge(remaining_files)
            results['consolidation'] = consolidation_results
            
            # Archive duplicate files
            duplicate_files = []
            for consolidation in consolidation_results.get('consolidations', []):
                duplicate_files.extend(consolidation['duplicate_files'])
            
            if duplicate_files:
                dup_archive_results = self.archive_old_files(duplicate_files)
                results['duplicate_archival'] = dup_archive_results
                logger.info(f"Archived {dup_archive_results['archived_count']} duplicate files")
        
        # Phase 4: Final analysis
        final_analysis = self.analyze_knowledge_base()
        results['final_state'] = final_analysis
        
        # Calculate optimization impact
        original_count = analysis['total_files']
        final_count = final_analysis['total_files']
        files_removed = original_count - final_count
        
        optimization_summary = {
            'optimization_completed': True,
            'files_before': original_count,
            'files_after': final_count,
            'files_removed': files_removed,
            'reduction_percentage': (files_removed / original_count * 100) if original_count > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        results['summary'] = optimization_summary
        
        logger.info(f"✅ Optimization complete: {files_removed} files removed ({optimization_summary['reduction_percentage']:.1f}% reduction)")
        
        return results

def main():
    """Run autonomous knowledge base optimization."""
    optimizer = KnowledgeBaseOptimizer()
    
    try:
        results = optimizer.optimize_knowledge_base()
        
        # Save optimization report
        report_path = Path("logs/eigencode_optimization_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Optimization report saved to: {report_path}")
        
        # Print summary
        summary = results.get('summary', {})
        print(f"\n🎯 EIGENCODE OPTIMIZATION SUMMARY:")
        print(f"   Files Before: {summary.get('files_before', 0)}")
        print(f"   Files After: {summary.get('files_after', 0)}")
        print(f"   Files Removed: {summary.get('files_removed', 0)}")
        print(f"   Reduction: {summary.get('reduction_percentage', 0):.1f}%")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())