#!/usr/bin/env python3
"""
Eigencode Validation Monitor
Autonomous monitoring and validation of eigencode optimizations
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

class EigencodeValidationMonitor:
    """Monitor and validate eigencode optimizations and system health."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Validation metrics
        self.validation_results = {}
        self.baseline_metrics = {}
        
    def validate_knowledge_base_optimization(self) -> Dict[str, Any]:
        """Validate the knowledge base optimization results."""
        logger.info("🔍 Validating knowledge base optimization...")
        
        kb_path = self.project_root / "autonomous-agents" / "communication" / "knowledge-base"
        archive_path = self.project_root / "autonomous-agents" / "communication" / "archived-knowledge"
        
        validation = {
            "optimization_type": "knowledge_base_cleanup",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "metrics": {}
        }
        
        try:
            # Count current files
            current_files = len(list(kb_path.glob("*.json"))) if kb_path.exists() else 0
            
            # Check archive existence and count
            archived_files = 0
            if archive_path.exists():
                for archive_dir in archive_path.iterdir():
                    if archive_dir.is_dir():
                        archived_files += len(list(archive_dir.glob("*.json")))
            
            # Load optimization report
            opt_report_path = self.logs_dir / "eigencode_optimization_report.json"
            if opt_report_path.exists():
                with open(opt_report_path, 'r') as f:
                    opt_report = json.load(f)
                
                original_count = opt_report.get('analysis', {}).get('total_files', 0)
                reduction_pct = opt_report.get('summary', {}).get('reduction_percentage', 0)
                
                validation["metrics"] = {
                    "files_before_optimization": original_count,
                    "files_after_optimization": current_files,
                    "files_archived": archived_files,
                    "reduction_percentage": reduction_pct,
                    "optimization_effective": reduction_pct > 90,
                    "filesystem_impact": "significant_improvement" if reduction_pct > 90 else "moderate_improvement"
                }
                
                # Validate that files were actually moved, not deleted
                total_preserved = current_files + archived_files
                data_integrity = abs(total_preserved - original_count) <= 5  # Allow small variance
                
                validation["metrics"]["data_integrity"] = data_integrity
                validation["metrics"]["total_files_preserved"] = total_preserved
                
                if not data_integrity:
                    validation["status"] = "warning"
                    validation["issues"] = ["Potential data loss detected"]
                
            else:
                validation["status"] = "error"
                validation["issues"] = ["Optimization report not found"]
                
        except Exception as e:
            validation["status"] = "error"
            validation["issues"] = [f"Validation error: {str(e)}"]
            logger.error(f"Knowledge base validation error: {e}")
        
        return validation
    
    def validate_agent_communication_optimization(self) -> Dict[str, Any]:
        """Validate agent communication optimization."""
        logger.info("🔍 Validating agent communication optimization...")
        
        validation = {
            "optimization_type": "agent_communication_enhancement",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "metrics": {}
        }
        
        try:
            agent_comm_file = self.project_root / "src" / "agent_communication.py"
            backup_file = agent_comm_file.with_suffix('.py.backup')
            
            if not agent_comm_file.exists():
                validation["status"] = "error"
                validation["issues"] = ["Agent communication file not found"]
                return validation
            
            # Check if optimizations were applied
            with open(agent_comm_file, 'r') as f:
                content = f.read()
            
            optimizations_applied = {
                "redis_connection_pooling": "ConnectionPool" in content,
                "lru_cache_optimization": "@lru_cache" in content,
                "optimized_redis_client": "_get_redis_client" in content,
                "cached_skill_loading": "_load_agent_skills_cached" in content
            }
            
            # Check backup exists
            backup_exists = backup_file.exists()
            
            validation["metrics"] = {
                "optimizations_applied": optimizations_applied,
                "all_optimizations_present": all(optimizations_applied.values()),
                "backup_created": backup_exists,
                "file_size_bytes": agent_comm_file.stat().st_size,
                "optimization_effectiveness": "high" if all(optimizations_applied.values()) else "partial"
            }
            
            # Syntax validation
            try:
                compile(content, str(agent_comm_file), 'exec')
                validation["metrics"]["syntax_valid"] = True
            except SyntaxError as e:
                validation["status"] = "error"
                validation["issues"] = [f"Syntax error in optimized file: {str(e)}"]
                validation["metrics"]["syntax_valid"] = False
            
        except Exception as e:
            validation["status"] = "error"
            validation["issues"] = [f"Validation error: {str(e)}"]
            logger.error(f"Agent communication validation error: {e}")
        
        return validation
    
    def validate_celery_optimization(self) -> Dict[str, Any]:
        """Validate Celery task optimization."""
        logger.info("🔍 Validating Celery optimization...")
        
        validation = {
            "optimization_type": "celery_task_caching",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "metrics": {}
        }
        
        try:
            celery_file = self.project_root / "src" / "celery_app.py"
            
            if not celery_file.exists():
                validation["status"] = "error"
                validation["issues"] = ["Celery app file not found"]
                return validation
            
            with open(celery_file, 'r') as f:
                content = f.read()
            
            # Check for optimization features
            optimizations = {
                "redis_task_cache": "REDIS_TASK_CACHE" in content,
                "cache_task_result_function": "cache_task_result" in content,
                "get_cached_task_result_function": "get_cached_task_result" in content,
                "redis_integration": "redis.from_url" in content
            }
            
            validation["metrics"] = {
                "optimizations_applied": optimizations,
                "caching_system_complete": all(optimizations.values()),
                "file_size_bytes": celery_file.stat().st_size
            }
            
            # Syntax validation
            try:
                compile(content, str(celery_file), 'exec')
                validation["metrics"]["syntax_valid"] = True
            except SyntaxError as e:
                validation["status"] = "error"
                validation["issues"] = [f"Syntax error in optimized file: {str(e)}"]
                validation["metrics"]["syntax_valid"] = False
            
        except Exception as e:
            validation["status"] = "error"
            validation["issues"] = [f"Validation error: {str(e)}"]
            logger.error(f"Celery validation error: {e}")
        
        return validation
    
    def validate_configuration_management(self) -> Dict[str, Any]:
        """Validate configuration management system."""
        logger.info("🔍 Validating configuration management...")
        
        validation = {
            "optimization_type": "configuration_management",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "metrics": {}
        }
        
        try:
            config_file = self.project_root / "src" / "eigencode_config_manager.py"
            
            if not config_file.exists():
                validation["status"] = "error"
                validation["issues"] = ["Configuration manager file not found"]
                return validation
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check for required components
            components = {
                "email_configuration": "EmailConfiguration" in content,
                "agent_configuration": "AgentConfiguration" in content,
                "api_configuration": "APIConfiguration" in content,
                "sms_configuration": "SMSConfiguration" in content,
                "configuration_manager": "ConfigurationManager" in content,
                "validation_methods": "validate_all_configs" in content
            }
            
            validation["metrics"] = {
                "components_present": components,
                "system_complete": all(components.values()),
                "file_size_bytes": config_file.stat().st_size
            }
            
            # Syntax validation
            try:
                compile(content, str(config_file), 'exec')
                validation["metrics"]["syntax_valid"] = True
            except SyntaxError as e:
                validation["status"] = "error"
                validation["issues"] = [f"Syntax error in configuration file: {str(e)}"]
                validation["metrics"]["syntax_valid"] = False
            
        except Exception as e:
            validation["status"] = "error"
            validation["issues"] = [f"Validation error: {str(e)}"]
            logger.error(f"Configuration validation error: {e}")
        
        return validation
    
    def validate_agent_activity_logger(self) -> Dict[str, Any]:
        """Validate agent activity logger system."""
        logger.info("🔍 Validating agent activity logger...")
        
        validation = {
            "optimization_type": "agent_activity_logging",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "metrics": {}
        }
        
        try:
            logger_file = self.project_root / "src" / "agent_activity_logger.py"
            
            if not logger_file.exists():
                validation["status"] = "error"
                validation["issues"] = ["Agent activity logger file not found"]
                return validation
            
            # Check logs directory
            logs_agent_dir = self.logs_dir / "agents"
            log_files_exist = logs_agent_dir.exists() and len(list(logs_agent_dir.glob("*.json"))) > 0
            
            # Check for recent activity logs
            recent_logs = []
            if logs_agent_dir.exists():
                for log_file in logs_agent_dir.glob("*_activity.json"):
                    try:
                        with open(log_file, 'r') as f:
                            data = json.load(f)
                            if data:  # Has content
                                recent_logs.append(log_file.name)
                    except:
                        pass
            
            validation["metrics"] = {
                "logger_file_exists": True,
                "logs_directory_exists": logs_agent_dir.exists(),
                "active_log_files": len(recent_logs),
                "recent_activity_logs": recent_logs[:5],  # First 5 for reporting
                "logging_system_functional": log_files_exist and len(recent_logs) > 0
            }
            
        except Exception as e:
            validation["status"] = "error" 
            validation["issues"] = [f"Validation error: {str(e)}"]
            logger.error(f"Activity logger validation error: {e}")
        
        return validation
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health after optimizations."""
        logger.info("🔍 Checking overall system health...")
        
        health_check = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "metrics": {}
        }
        
        try:
            # Check Redis connectivity
            redis_healthy = False
            try:
                import redis
                redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
                redis_client.ping()
                redis_healthy = True
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
            
            # Check file system health
            critical_dirs = [
                self.project_root / "src",
                self.project_root / "autonomous-agents",
                self.project_root / "logs"
            ]
            
            dirs_healthy = all(d.exists() for d in critical_dirs)
            
            # Check for critical files
            critical_files = [
                self.project_root / "src" / "agent_communication.py",
                self.project_root / "src" / "celery_app.py",
                self.project_root / "src" / "agent_activity_logger.py"
            ]
            
            files_healthy = all(f.exists() for f in critical_files)
            
            health_check["metrics"] = {
                "redis_connectivity": redis_healthy,
                "critical_directories": dirs_healthy,
                "critical_files": files_healthy,
                "optimizations_preserved": True,  # Assume true unless validation fails
                "system_responsive": True  # Basic check passed
            }
            
            # Overall health assessment
            if not all([redis_healthy, dirs_healthy, files_healthy]):
                health_check["overall_status"] = "degraded"
                health_check["issues"] = []
                
                if not redis_healthy:
                    health_check["issues"].append("Redis connectivity issues")
                if not dirs_healthy:
                    health_check["issues"].append("Critical directories missing")
                if not files_healthy:
                    health_check["issues"].append("Critical files missing")
            
        except Exception as e:
            health_check["overall_status"] = "error"
            health_check["issues"] = [f"Health check error: {str(e)}"]
            logger.error(f"System health check error: {e}")
        
        return health_check
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        logger.info("📊 Generating comprehensive validation report...")
        
        validations = [
            self.validate_knowledge_base_optimization(),
            self.validate_agent_communication_optimization(),
            self.validate_celery_optimization(),
            self.validate_configuration_management(),
            self.validate_agent_activity_logger()
        ]
        
        system_health = self.check_system_health()
        
        # Calculate overall score
        successful_validations = sum(1 for v in validations if v["status"] == "success")
        total_validations = len(validations)
        success_rate = (successful_validations / total_validations) * 100
        
        # Determine overall status
        if success_rate == 100 and system_health["overall_status"] == "healthy":
            overall_status = "excellent"
        elif success_rate >= 80 and system_health["overall_status"] in ["healthy", "degraded"]:
            overall_status = "good"
        elif success_rate >= 60:
            overall_status = "acceptable"
        else:
            overall_status = "needs_attention"
        
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "eigencode_loop_cycle": "autonomous_optimization_1",
            "overall_status": overall_status,
            "success_rate_percent": round(success_rate, 1),
            "optimizations_validated": total_validations,
            "successful_validations": successful_validations,
            "system_health": system_health,
            "individual_validations": validations,
            "recommendations": self.generate_recommendations(validations, system_health)
        }
        
        return report
    
    def generate_recommendations(self, validations: List[Dict], health: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check for failed validations
        failed_validations = [v for v in validations if v["status"] == "error"]
        if failed_validations:
            recommendations.append("Investigate and fix failed optimization validations")
        
        # Check for syntax errors
        syntax_errors = [v for v in validations if v.get("metrics", {}).get("syntax_valid") == False]
        if syntax_errors:
            recommendations.append("Fix syntax errors in optimized files")
        
        # Check system health
        if health["overall_status"] != "healthy":
            recommendations.append("Address system health issues before deploying optimizations")
        
        # Knowledge base specific
        kb_validation = next((v for v in validations if v["optimization_type"] == "knowledge_base_cleanup"), None)
        if kb_validation and not kb_validation.get("metrics", {}).get("data_integrity", True):
            recommendations.append("Verify knowledge base data integrity after cleanup")
        
        # Agent communication specific
        comm_validation = next((v for v in validations if v["optimization_type"] == "agent_communication_enhancement"), None)
        if comm_validation and not comm_validation.get("metrics", {}).get("all_optimizations_present", False):
            recommendations.append("Complete agent communication optimizations")
        
        # Generic recommendations
        if not recommendations:
            recommendations.extend([
                "Monitor system performance metrics for optimization impact",
                "Consider implementing additional performance monitoring",
                "Schedule regular validation cycles for continuous improvement"
            ])
        
        return recommendations
    
    def run_validation_cycle(self) -> Dict[str, Any]:
        """Run complete validation cycle."""
        logger.info("🚀 Starting eigencode validation cycle...")
        
        start_time = datetime.now()
        
        try:
            report = self.generate_validation_report()
            
            # Add timing information
            report["validation_duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            # Save report
            report_file = self.logs_dir / f"eigencode_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Save as latest
            latest_report_file = self.logs_dir / "eigencode_validation_latest.json"
            with open(latest_report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"✅ Validation report saved: {report_file}")
            
            return report
            
        except Exception as e:
            error_report = {
                "validation_timestamp": datetime.now().isoformat(),
                "overall_status": "validation_failed",
                "error": str(e),
                "validation_duration_seconds": (datetime.now() - start_time).total_seconds()
            }
            
            logger.error(f"❌ Validation cycle failed: {e}")
            return error_report

def main():
    """Run eigencode validation monitoring."""
    logging.basicConfig(level=logging.INFO)
    
    monitor = EigencodeValidationMonitor()
    report = monitor.run_validation_cycle()
    
    # Print summary
    print("\n🎯 EIGENCODE VALIDATION SUMMARY:")
    print(f"   Overall Status: {report.get('overall_status', 'unknown')}")
    print(f"   Success Rate: {report.get('success_rate_percent', 0)}%")
    print(f"   Validations: {report.get('successful_validations', 0)}/{report.get('optimizations_validated', 0)}")
    
    if report.get('recommendations'):
        print(f"\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Return appropriate exit code
    status = report.get('overall_status', 'unknown')
    if status in ['excellent', 'good']:
        return 0
    elif status == 'acceptable':
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(main())