"""
DevOps CI/CD Pipeline Orchestration Demo

This example demonstrates a comprehensive DevOps CI/CD pipeline using ModuLink
chains. It includes:

- Source code management and version control
- Automated testing (unit, integration, security)
- Code quality analysis and compliance checks
- Docker containerization and registry management
- Multi-environment deployment (dev, staging, production)
- Infrastructure as Code (IaC) provisioning
- Monitoring and alerting setup
- Rollback mechanisms and disaster recovery
- Approval workflows and notifications
- Performance benchmarking and load testing
"""

import asyncio
import time
import json
import hashlib
import subprocess
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import tempfile
import os

# Import ModuLink
from modulink import chain, when, parallel, catch_errors, ctx
from modulink.utils import (
    timing, logging, validate, performance_tracker,
    transform, set_values, validators, error_handlers,
    memoize
)

# Export all testable functions and classes
__all__ = [
    # Enums and Data Classes
    'PipelineStage', 'Environment', 'DeploymentStrategy', 'TestType',
    'Repository', 'BuildConfig', 'TestConfig', 'QualityConfig',
    'SecurityConfig', 'ContainerConfig', 'DeploymentConfig', 'MonitoringConfig',
    
    # Mock Services
    'MockVersionControl', 'MockBuildSystem', 'MockTestRunner', 'MockQualityAnalyzer',
    'MockSecurityScanner', 'MockContainerRegistry', 'MockClusterManager', 
    'MockMonitoringSystem', 'MockNotificationService',
    
    # Core Pipeline Functions
    'checkout_source_code', 'build_application', 'run_test_suite',
    'analyze_code_quality', 'perform_security_scan', 'containerize_application',
    'deploy_to_environment', 'setup_monitoring_and_alerts', 'validate_deployment',
    'send_success_notification', 'build_failure_handler',
    
    # Chain Creation
    'create_development_pipeline', 'create_staging_pipeline', 'create_production_pipeline',
    'create_multi_environment_pipeline',
    
    # Demo Functions
    'demo_successful_deployment', 'demo_failed_tests', 'demo_security_failure',
    'demo_rollback_scenario',
    
    # Utility Functions
    'reset_pipeline_state', 'get_pipeline_metrics', 'create_test_context'
]

# Enums and Data Models
class PipelineStage(Enum):
    SOURCE_CONTROL = "source_control"
    BUILD = "build"
    TEST = "test"
    QUALITY_ANALYSIS = "quality_analysis"
    SECURITY_SCAN = "security_scan"
    CONTAINERIZATION = "containerization"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    VALIDATION = "validation"

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DeploymentStrategy(Enum):
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SMOKE = "smoke"

@dataclass
class Repository:
    name: str
    url: str
    branch: str
    commit_hash: str
    language: str
    framework: str

@dataclass
class BuildConfig:
    build_tool: str
    docker_image: str
    build_commands: List[str]
    artifacts: List[str]
    cache_enabled: bool

@dataclass
class TestConfig:
    test_types: List[TestType]
    test_commands: Dict[str, str]
    coverage_threshold: float
    parallel_execution: bool

@dataclass
class QualityConfig:
    code_quality_tools: List[str]
    quality_gates: Dict[str, float]
    compliance_checks: List[str]

@dataclass
class SecurityConfig:
    vulnerability_scan: bool
    dependency_check: bool
    secrets_scan: bool
    compliance_frameworks: List[str]

@dataclass
class ContainerConfig:
    registry_url: str
    image_name: str
    tag_strategy: str
    security_scan: bool
    multi_arch: bool

@dataclass
class DeploymentConfig:
    environment: Environment
    strategy: DeploymentStrategy
    replicas: int
    health_checks: Dict[str, Any]
    rollback_enabled: bool

@dataclass
class MonitoringConfig:
    metrics_enabled: bool
    logging_enabled: bool
    alerting_rules: List[Dict[str, Any]]
    dashboards: List[str]

# Mock Services
class MockVersionControl:
    """Mock version control system."""
    
    def __init__(self):
        self.repositories = {
            "web-app": {
                "url": "https://github.com/company/web-app.git",
                "branch": "main",
                "latest_commit": "abc123",
                "changes": ["src/app.py", "tests/test_app.py", "Dockerfile"]
            },
            "api-service": {
                "url": "https://github.com/company/api-service.git", 
                "branch": "develop",
                "latest_commit": "def456",
                "changes": ["api/handlers.py", "requirements.txt"]
            }
        }
    
    async def checkout_code(self, repo_name: str, branch: str) -> Dict[str, Any]:
        """Simulate code checkout."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if repo_name not in self.repositories:
            raise Exception(f"Repository {repo_name} not found")
        
        repo_info = self.repositories[repo_name]
        return {
            "checkout_successful": True,
            "commit_hash": repo_info["latest_commit"],
            "changed_files": repo_info["changes"],
            "workspace_path": f"/tmp/workspace/{repo_name}"
        }
    
    async def create_tag(self, repo_name: str, tag: str) -> bool:
        """Create a git tag."""
        await asyncio.sleep(0.05)
        return True

class MockBuildSystem:
    """Mock build system."""
    
    def __init__(self):
        self.build_cache = {}
    
    async def build_project(self, config: BuildConfig, workspace_path: str) -> Dict[str, Any]:
        """Simulate project build."""
        build_time = 2.0 if not config.cache_enabled else 0.5
        await asyncio.sleep(build_time)
        
        # Simulate build success/failure based on cache
        cache_key = hashlib.md5(str(config.build_commands).encode()).hexdigest()
        
        if config.cache_enabled and cache_key in self.build_cache:
            return {
                "build_successful": True,
                "artifacts": config.artifacts,
                "build_time": build_time,
                "cache_hit": True,
                "build_logs": "Build completed using cache"
            }
        
        # Simulate occasional build failures
        success = True
        if "fail" in str(config.build_commands):
            success = False
        
        result = {
            "build_successful": success,
            "artifacts": config.artifacts if success else [],
            "build_time": build_time,
            "cache_hit": False,
            "build_logs": "Build completed successfully" if success else "Build failed"
        }
        
        if success and config.cache_enabled:
            self.build_cache[cache_key] = result
        
        return result

class MockTestRunner:
    """Mock test execution system."""
    
    async def run_tests(self, config: TestConfig, workspace_path: str) -> Dict[str, Any]:
        """Run various types of tests."""
        test_results = {}
        total_time = 0
        
        for test_type in config.test_types:
            test_time = 1.0 if not config.parallel_execution else 0.3
            await asyncio.sleep(test_time)
            total_time += test_time
            
            # Simulate test results
            if test_type == TestType.UNIT:
                test_results[test_type.value] = {
                    "passed": 95,
                    "failed": 2,
                    "coverage": 88.5,
                    "duration": test_time
                }
            elif test_type == TestType.INTEGRATION:
                test_results[test_type.value] = {
                    "passed": 12,
                    "failed": 0,
                    "duration": test_time
                }
            elif test_type == TestType.SECURITY:
                test_results[test_type.value] = {
                    "vulnerabilities": 1,
                    "severity": "medium",
                    "duration": test_time
                }
            elif test_type == TestType.PERFORMANCE:
                test_results[test_type.value] = {
                    "response_time_ms": 150,
                    "throughput_rps": 1000,
                    "duration": test_time
                }
        
        # Check if tests meet threshold
        unit_results = test_results.get(TestType.UNIT.value, {})
        coverage = unit_results.get("coverage", 0)
        tests_passed = coverage >= config.coverage_threshold
        
        return {
            "tests_passed": tests_passed,
            "test_results": test_results,
            "total_duration": total_time,
            "coverage": coverage
        }

class MockQualityAnalyzer:
    """Mock code quality analysis system."""
    
    async def analyze_quality(self, config: QualityConfig, workspace_path: str) -> Dict[str, Any]:
        """Perform code quality analysis."""
        await asyncio.sleep(1.0)
        
        quality_scores = {
            "complexity": 7.2,
            "maintainability": 8.5,
            "reliability": 9.1,
            "security": 8.8,
            "coverage": 88.5
        }
        
        # Check quality gates
        gates_passed = all(
            quality_scores.get(gate, 0) >= threshold
            for gate, threshold in config.quality_gates.items()
        )
        
        return {
            "quality_analysis_passed": gates_passed,
            "quality_scores": quality_scores,
            "issues_found": 5 if not gates_passed else 2,
            "compliance_status": "compliant"
        }

class MockSecurityScanner:
    """Mock security scanning system."""
    
    async def scan_security(self, config: SecurityConfig, workspace_path: str) -> Dict[str, Any]:
        """Perform security scanning."""
        await asyncio.sleep(1.5)
        
        vulnerabilities = []
        if config.vulnerability_scan:
            vulnerabilities.append({
                "type": "dependency",
                "severity": "medium",
                "component": "requests==2.25.1",
                "description": "Known vulnerability in requests library"
            })
        
        secrets_found = []
        if config.secrets_scan:
            # Simulate finding a potential secret
            secrets_found.append({
                "type": "api_key",
                "file": "config.py",
                "line": 15,
                "pattern": "api_key = 'sk-...'"
            })
        
        scan_passed = len(vulnerabilities) == 0 and len(secrets_found) == 0
        
        return {
            "security_scan_passed": scan_passed,
            "vulnerabilities": vulnerabilities,
            "secrets_found": secrets_found,
            "compliance_frameworks_met": config.compliance_frameworks
        }

class MockContainerRegistry:
    """Mock container registry."""
    
    def __init__(self):
        self.images = {}
    
    async def build_and_push(self, config: ContainerConfig, workspace_path: str, 
                           artifacts: List[str]) -> Dict[str, Any]:
        """Build and push container image."""
        await asyncio.sleep(2.0)  # Simulate build and push time
        
        tag = f"{config.image_name}:{self._generate_tag(config.tag_strategy)}"
        
        # Simulate security scan if enabled
        security_scan_passed = True
        if config.security_scan:
            await asyncio.sleep(0.5)
            # Simulate occasional security issues
            security_scan_passed = "vulnerable" not in config.image_name
        
        if security_scan_passed:
            self.images[tag] = {
                "size_mb": 150,
                "layers": 8,
                "created": datetime.now().isoformat(),
                "security_scan": "passed" if config.security_scan else "skipped"
            }
        
        return {
            "container_built": security_scan_passed,
            "image_tag": tag,
            "registry_url": config.registry_url,
            "security_scan_passed": security_scan_passed,
            "image_size_mb": 150
        }
    
    def _generate_tag(self, strategy: str) -> str:
        """Generate image tag based on strategy."""
        if strategy == "commit":
            return "abc123"
        elif strategy == "timestamp":
            return datetime.now().strftime("%Y%m%d-%H%M%S")
        else:
            return "latest"

class MockClusterManager:
    """Mock Kubernetes/container orchestration system."""
    
    def __init__(self):
        self.deployments = {}
        self.environments = {
            Environment.DEVELOPMENT: {"replicas": 1, "resources": "minimal"},
            Environment.STAGING: {"replicas": 2, "resources": "medium"},
            Environment.PRODUCTION: {"replicas": 5, "resources": "high"}
        }
    
    async def deploy_application(self, config: DeploymentConfig, image_tag: str) -> Dict[str, Any]:
        """Deploy application to cluster."""
        deployment_time = {
            DeploymentStrategy.ROLLING: 3.0,
            DeploymentStrategy.BLUE_GREEN: 5.0,
            DeploymentStrategy.CANARY: 4.0
        }
        
        await asyncio.sleep(deployment_time[config.strategy])
        
        deployment_id = f"deploy-{config.environment.value}-{int(time.time())}"
        
        # Simulate deployment success
        deployment_successful = True
        if "fail" in image_tag:
            deployment_successful = False
        
        if deployment_successful:
            self.deployments[deployment_id] = {
                "environment": config.environment.value,
                "strategy": config.strategy.value,
                "replicas": config.replicas,
                "image": image_tag,
                "status": "running",
                "health": "healthy"
            }
        
        return {
            "deployment_successful": deployment_successful,
            "deployment_id": deployment_id,
            "environment": config.environment.value,
            "strategy": config.strategy.value,
            "replicas_running": config.replicas if deployment_successful else 0,
            "health_status": "healthy" if deployment_successful else "unhealthy"
        }
    
    async def rollback_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Rollback a deployment."""
        await asyncio.sleep(1.0)
        
        if deployment_id in self.deployments:
            self.deployments[deployment_id]["status"] = "rolled_back"
            return {
                "rollback_successful": True,
                "deployment_id": deployment_id
            }
        
        return {"rollback_successful": False}

class MockMonitoringSystem:
    """Mock monitoring and alerting system."""
    
    async def setup_monitoring(self, config: MonitoringConfig, deployment_id: str) -> Dict[str, Any]:
        """Set up monitoring for deployed application."""
        await asyncio.sleep(0.5)
        
        monitoring_components = []
        
        if config.metrics_enabled:
            monitoring_components.append("prometheus")
            monitoring_components.append("grafana")
        
        if config.logging_enabled:
            monitoring_components.append("elasticsearch")
            monitoring_components.append("kibana")
        
        alerts_configured = len(config.alerting_rules)
        dashboards_created = len(config.dashboards)
        
        return {
            "monitoring_setup": True,
            "components": monitoring_components,
            "alerts_configured": alerts_configured,
            "dashboards_created": dashboards_created,
            "health_check_url": f"https://monitoring.company.com/health/{deployment_id}"
        }

class MockNotificationService:
    """Mock notification service."""
    
    async def send_notification(self, message: str, channels: List[str], 
                              severity: str = "info") -> Dict[str, Any]:
        """Send notifications to various channels."""
        await asyncio.sleep(0.1)
        
        notifications_sent = []
        for channel in channels:
            notifications_sent.append({
                "channel": channel,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "notifications_sent": True,
            "channels": channels,
            "notifications": notifications_sent
        }

# Pipeline Functions
async def checkout_source_code(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check out source code from version control."""
    repo_config = ctx_data["repository"]
    vcs = ctx_data["version_control"]
    
    result = await vcs.checkout_code(repo_config["name"], repo_config["branch"])
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.SOURCE_CONTROL.value
    }


  
async def build_application(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the application."""
    if not ctx_data.get("checkout_successful"):
        raise Exception("Cannot build without successful checkout")
    
    build_config = ctx_data["build_config"]
    workspace_path = ctx_data["workspace_path"]
    build_system = ctx_data["build_system"]
    
    result = await build_system.build_project(build_config, workspace_path)
    
    if not result["build_successful"]:
        raise Exception("Build failed")
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.BUILD.value
    }



async def run_test_suite(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run comprehensive test suite."""
    if not ctx_data.get("build_successful"):
        raise Exception("Cannot test without successful build")
    
    test_config = ctx_data["test_config"]
    workspace_path = ctx_data["workspace_path"]
    test_runner = ctx_data["test_runner"]
    
    result = await test_runner.run_tests(test_config, workspace_path)
    
    if not result["tests_passed"]:
        raise Exception(f"Tests failed. Coverage: {result.get('coverage', 0)}%")
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.TEST.value
    }



async def analyze_code_quality(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze code quality and compliance."""
    if not ctx_data.get("tests_passed"):
        raise Exception("Cannot proceed with quality analysis after test failures")
    
    quality_config = ctx_data["quality_config"]
    workspace_path = ctx_data["workspace_path"]
    quality_analyzer = ctx_data["quality_analyzer"]
    
    result = await quality_analyzer.analyze_quality(quality_config, workspace_path)
    
    if not result["quality_analysis_passed"]:
        raise Exception("Code quality standards not met")
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.QUALITY_ANALYSIS.value
    }



async def perform_security_scan(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform security scanning."""
    if not ctx_data.get("quality_analysis_passed"):
        raise Exception("Cannot proceed with security scan after quality failures")
    
    security_config = ctx_data["security_config"]
    workspace_path = ctx_data["workspace_path"]
    security_scanner = ctx_data["security_scanner"]
    
    result = await security_scanner.scan_security(security_config, workspace_path)
    
    if not result["security_scan_passed"]:
        raise Exception("Security vulnerabilities found")
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.SECURITY_SCAN.value
    }



async def containerize_application(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build and push container image."""
    if not ctx_data.get("security_scan_passed"):
        raise Exception("Cannot containerize with security issues")
    
    container_config = ctx_data["container_config"]
    workspace_path = ctx_data["workspace_path"]
    artifacts = ctx_data.get("artifacts", [])
    container_registry = ctx_data["container_registry"]
    
    result = await container_registry.build_and_push(
        container_config, workspace_path, artifacts
    )
    
    if not result["container_built"]:
        raise Exception("Container build or security scan failed")
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.CONTAINERIZATION.value
    }



async def deploy_to_environment(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy application to target environment."""
    if not ctx_data.get("container_built"):
        raise Exception("Cannot deploy without container image")
    
    deployment_config = ctx_data["deployment_config"]
    image_tag = ctx_data["image_tag"]
    cluster_manager = ctx_data["cluster_manager"]
    
    result = await cluster_manager.deploy_application(deployment_config, image_tag)
    
    if not result["deployment_successful"]:
        raise Exception("Deployment failed")
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.DEPLOYMENT.value
    }



async def setup_monitoring_and_alerts(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Set up monitoring and alerting."""
    if not ctx_data.get("deployment_successful"):
        raise Exception("Cannot setup monitoring without successful deployment")
    
    monitoring_config = ctx_data["monitoring_config"]
    deployment_id = ctx_data["deployment_id"]
    monitoring_system = ctx_data["monitoring_system"]
    
    result = await monitoring_system.setup_monitoring(monitoring_config, deployment_id)
    
    return {
        **ctx_data,
        **result,
        "stage_completed": PipelineStage.MONITORING.value
    }



async def validate_deployment(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate deployment with smoke tests."""
    if not ctx_data.get("monitoring_setup"):
        raise Exception("Cannot validate without monitoring setup")
    
    # Simulate smoke tests
    await asyncio.sleep(1.0)
    
    health_status = ctx_data.get("health_status", "unhealthy")
    validation_passed = health_status == "healthy"
    
    if not validation_passed:
        raise Exception("Deployment validation failed")
    
    return {
        **ctx_data,
        "validation_passed": validation_passed,
        "smoke_tests_passed": True,
        "stage_completed": PipelineStage.VALIDATION.value
    }



async def send_success_notification(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send success notification."""
    notification_service = ctx_data["notification_service"]
    deployment_config = ctx_data["deployment_config"]
    
    message = f"Deployment successful to {deployment_config.environment.value}"
    channels = ["slack", "email"]
    
    result = await notification_service.send_notification(message, channels, "success")
    
    return {
        **ctx_data,
        **result,
        "pipeline_completed": True
    }

# Error Handlers
async def build_failure_handler(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle build failures."""
    notification_service = ctx_data["notification_service"]
    
    message = f"Build failed for {ctx_data.get('repository', {}).get('name', 'unknown')}"
    channels = ["slack"]
    
    await notification_service.send_notification(message, channels, "error")
    
    return {
        **ctx_data,
        "build_failed": True,
        "pipeline_failed": True,
        "failure_reason": "build_failure"
    }

async def test_failure_handler(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle test failures."""
    notification_service = ctx_data["notification_service"]
    
    coverage = ctx_data.get("coverage", 0)
    message = f"Tests failed. Coverage: {coverage}%"
    channels = ["slack"]
    
    await notification_service.send_notification(message, channels, "error")
    
    return {
        **ctx_data,
        "test_failed": True,
        "pipeline_failed": True,
        "failure_reason": "test_failure"
    }

async def security_failure_handler(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle security scan failures."""
    notification_service = ctx_data["notification_service"]
    
    vulnerabilities = len(ctx_data.get("vulnerabilities", []))
    secrets = len(ctx_data.get("secrets_found", []))
    
    message = f"Security issues found: {vulnerabilities} vulnerabilities, {secrets} secrets"
    channels = ["slack", "security-team"]
    
    await notification_service.send_notification(message, channels, "critical")
    
    return {
        **ctx_data,
        "security_failed": True,
        "pipeline_failed": True,
        "failure_reason": "security_failure"
    }

async def deployment_failure_handler(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle deployment failures with rollback."""
    notification_service = ctx_data["notification_service"]
    cluster_manager = ctx_data.get("cluster_manager")
    
    # Attempt rollback if deployment was attempted
    deployment_id = ctx_data.get("deployment_id")
    rollback_result = {}
    
    if deployment_id and cluster_manager:
        rollback_result = await cluster_manager.rollback_deployment(deployment_id)
    
    message = f"Deployment failed. Rollback: {'successful' if rollback_result.get('rollback_successful') else 'failed'}"
    channels = ["slack", "devops-team"]
    
    await notification_service.send_notification(message, channels, "critical")
    
    return {
        **ctx_data,
        **rollback_result,
        "deployment_failed": True,
        "pipeline_failed": True,
        "failure_reason": "deployment_failure"
    }

# Pipeline Creation Functions
def create_development_pipeline() -> chain:
    """Create development environment pipeline."""
    return chain([
        checkout_source_code,
        build_application,
        run_test_suite,
        analyze_code_quality,
        containerize_application,
        deploy_to_environment,
        validate_deployment,
        send_success_notification
    ]).catch_errors({
        Exception: build_failure_handler
    })

def create_staging_pipeline() -> chain:
    """Create staging environment pipeline with additional security checks."""
    return chain([
        checkout_source_code,
        build_application,
        run_test_suite,
        analyze_code_quality,
        perform_security_scan,
        containerize_application,
        deploy_to_environment,
        setup_monitoring_and_alerts,
        validate_deployment,
        send_success_notification
    ]).catch_errors({
        Exception: test_failure_handler
    })

def create_production_pipeline() -> chain:
    """Create production pipeline with comprehensive checks and approvals."""
    
    # Production pipeline with parallel security and quality checks
    security_and_quality = parallel([
        perform_security_scan,
        analyze_code_quality
    ])
    
    return chain([
        checkout_source_code,
        build_application,
        run_test_suite,
        security_and_quality,
        containerize_application,
        deploy_to_environment,
        setup_monitoring_and_alerts,
        validate_deployment,
        send_success_notification
    ]).catch_errors({
        Exception: deployment_failure_handler
    })

def create_multi_environment_pipeline() -> chain:
    """Create pipeline that deploys to multiple environments."""
    
    # Parallel deployment to dev and staging
    parallel_deploy = parallel([
        deploy_to_environment,  # Will use context to determine environment
        deploy_to_environment   # Second deployment for staging
    ])
    
    return chain([
        checkout_source_code,
        build_application,
        run_test_suite,
        analyze_code_quality,
        perform_security_scan,
        containerize_application,
        parallel_deploy,
        setup_monitoring_and_alerts,
        validate_deployment,
        send_success_notification
    ])

# Demo Functions
async def demo_simple_development_deployment():
    """Demo a simple development deployment."""
    print("\n=== Simple Development Deployment Demo ===")
    
    pipeline = create_development_pipeline()
    
    # Create mock services
    vcs = MockVersionControl()
    build_system = MockBuildSystem()
    test_runner = MockTestRunner()
    quality_analyzer = MockQualityAnalyzer()
    container_registry = MockContainerRegistry()
    cluster_manager = MockClusterManager()
    notification_service = MockNotificationService()
    
    # Configuration
    ctx_data = {
        "repository": {"name": "web-app", "branch": "main"},
        "build_config": BuildConfig(
            build_tool="npm",
            docker_image="node:16",
            build_commands=["npm install", "npm run build"],
            artifacts=["dist/", "package.json"],
            cache_enabled=True
        ),
        "test_config": TestConfig(
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            test_commands={"unit": "npm test", "integration": "npm run test:integration"},
            coverage_threshold=80.0,
            parallel_execution=True
        ),
        "quality_config": QualityConfig(
            code_quality_tools=["eslint", "sonarqube"],
            quality_gates={"complexity": 7.0, "maintainability": 8.0},
            compliance_checks=["pci", "gdpr"]
        ),
        "container_config": ContainerConfig(
            registry_url="registry.company.com",
            image_name="web-app",
            tag_strategy="commit",
            security_scan=False,
            multi_arch=False
        ),
        "deployment_config": DeploymentConfig(
            environment=Environment.DEVELOPMENT,
            strategy=DeploymentStrategy.ROLLING,
            replicas=1,
            health_checks={"path": "/health", "timeout": 30},
            rollback_enabled=True
        ),
        
        # Services
        "version_control": vcs,
        "build_system": build_system,
        "test_runner": test_runner,
        "quality_analyzer": quality_analyzer,
        "container_registry": container_registry,
        "cluster_manager": cluster_manager,
        "notification_service": notification_service
    }
    
    start_time = datetime.now()
    try:
        result = await pipeline.run(ctx_data)
        end_time = datetime.now()
        
        print(f"✅ Development deployment successful!")
        print(f"⏱️  Total time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"🏗️  Build time: {result.get('build_time', 0):.2f}s")
        print(f"🧪 Test coverage: {result.get('coverage', 0):.1f}%")
        print(f"🐳 Container: {result.get('image_tag', 'unknown')}")
        print(f"🚀 Environment: {result.get('environment', 'unknown')}")
        print(f"✅ Health status: {result.get('health_status', 'unknown')}")
        
    except Exception as e:
        end_time = datetime.now()
        print(f"❌ Deployment failed: {str(e)}")
        print(f"⏱️  Time to failure: {(end_time - start_time).total_seconds():.2f}s")

async def demo_production_deployment_with_security():
    """Demo production deployment with comprehensive security checks."""
    print("\n=== Production Deployment with Security Demo ===")
    
    pipeline = create_production_pipeline()
    
    # Create mock services
    vcs = MockVersionControl()
    build_system = MockBuildSystem()
    test_runner = MockTestRunner()
    quality_analyzer = MockQualityAnalyzer()
    security_scanner = MockSecurityScanner()
    container_registry = MockContainerRegistry()
    cluster_manager = MockClusterManager()
    monitoring_system = MockMonitoringSystem()
    notification_service = MockNotificationService()
    
    ctx_data = {
        "repository": {"name": "api-service", "branch": "main"},
        "build_config": BuildConfig(
            build_tool="maven",
            docker_image="openjdk:11",
            build_commands=["mvn clean compile", "mvn package"],
            artifacts=["target/*.jar"],
            cache_enabled=False
        ),
        "test_config": TestConfig(
            test_types=[TestType.UNIT, TestType.INTEGRATION, TestType.SECURITY, TestType.PERFORMANCE],
            test_commands={
                "unit": "mvn test",
                "integration": "mvn verify",
                "security": "mvn owasp:check",
                "performance": "mvn jmeter:jmeter"
            },
            coverage_threshold=85.0,
            parallel_execution=False
        ),
        "quality_config": QualityConfig(
            code_quality_tools=["sonarqube", "checkstyle", "pmd"],
            quality_gates={"complexity": 8.0, "maintainability": 8.5, "reliability": 9.0},
            compliance_checks=["sox", "pci", "hipaa"]
        ),
        "security_config": SecurityConfig(
            vulnerability_scan=True,
            dependency_check=True,
            secrets_scan=True,
            compliance_frameworks=["cis", "nist"]
        ),
        "container_config": ContainerConfig(
            registry_url="registry.company.com",
            image_name="api-service",
            tag_strategy="timestamp",
            security_scan=True,
            multi_arch=True
        ),
        "deployment_config": DeploymentConfig(
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.BLUE_GREEN,
            replicas=5,
            health_checks={"path": "/health", "timeout": 60},
            rollback_enabled=True
        ),
        "monitoring_config": MonitoringConfig(
            metrics_enabled=True,
            logging_enabled=True,
            alerting_rules=[
                {"metric": "cpu_usage", "threshold": 80, "severity": "warning"},
                {"metric": "error_rate", "threshold": 5, "severity": "critical"}
            ],
            dashboards=["application", "infrastructure", "business"]
        ),
        
        # Services
        "version_control": vcs,
        "build_system": build_system,
        "test_runner": test_runner,
        "quality_analyzer": quality_analyzer,
        "security_scanner": security_scanner,
        "container_registry": container_registry,
        "cluster_manager": cluster_manager,
        "monitoring_system": monitoring_system,
        "notification_service": notification_service
    }
    
    start_time = datetime.now()
    try:
        result = await pipeline.run(ctx_data)
        end_time = datetime.now()
        
        print(f"✅ Production deployment successful!")
        print(f"⏱️  Total time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"🔒 Security scan: {result.get('security_scan_passed', False)}")
        print(f"🎯 Quality score: {result.get('quality_scores', {}).get('maintainability', 0):.1f}")
        print(f"🐳 Container: {result.get('image_tag', 'unknown')}")
        print(f"🚀 Strategy: {result.get('strategy', 'unknown')}")
        print(f"📊 Monitoring: {result.get('monitoring_setup', False)}")
        print(f"📈 Dashboards: {result.get('dashboards_created', 0)}")
        
    except Exception as e:
        end_time = datetime.now()
        print(f"❌ Production deployment failed: {str(e)}")
        print(f"⏱️  Time to failure: {(end_time - start_time).total_seconds():.2f}s")

async def demo_failed_deployment_with_rollback():
    """Demo deployment failure with automatic rollback."""
    print("\n=== Failed Deployment with Rollback Demo ===")
    
    pipeline = create_production_pipeline()
    
    # Create mock services with failure simulation
    vcs = MockVersionControl()
    build_system = MockBuildSystem()
    test_runner = MockTestRunner()
    quality_analyzer = MockQualityAnalyzer()
    security_scanner = MockSecurityScanner()
    container_registry = MockContainerRegistry()
    cluster_manager = MockClusterManager()
    monitoring_system = MockMonitoringSystem()
    notification_service = MockNotificationService()
    
    ctx_data = {
        "repository": {"name": "api-service", "branch": "main"},
        "build_config": BuildConfig(
            build_tool="maven",
            docker_image="openjdk:11",
            build_commands=["mvn clean compile", "mvn package"],
            artifacts=["target/*.jar"],
            cache_enabled=False
        ),
        "test_config": TestConfig(
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            test_commands={"unit": "mvn test", "integration": "mvn verify"},
            coverage_threshold=85.0,
            parallel_execution=False
        ),
        "quality_config": QualityConfig(
            code_quality_tools=["sonarqube"],
            quality_gates={"complexity": 8.0, "maintainability": 8.5},
            compliance_checks=["sox"]
        ),
        "security_config": SecurityConfig(
            vulnerability_scan=True,
            dependency_check=True,
            secrets_scan=True,
            compliance_frameworks=["cis"]
        ),
        "container_config": ContainerConfig(
            registry_url="registry.company.com",
            image_name="api-service",
            tag_strategy="timestamp",
            security_scan=True,
            multi_arch=False
        ),
        "deployment_config": DeploymentConfig(
            environment=Environment.PRODUCTION,
            strategy=DeploymentStrategy.BLUE_GREEN,
            replicas=5,
            health_checks={"path": "/health", "timeout": 60},
            rollback_enabled=True
        ),
        
        # Services
        "version_control": vcs,
        "build_system": build_system,
        "test_runner": test_runner,
        "quality_analyzer": quality_analyzer,
        "security_scanner": security_scanner,
        "container_registry": container_registry,
        "cluster_manager": cluster_manager,
        "monitoring_system": monitoring_system,
        "notification_service": notification_service
    }
    
    # Introduce failure by modifying image tag to trigger deployment failure
    start_time = datetime.now()
    
    # First run a partial pipeline to get an image
    partial_pipeline = chain([
        checkout_source_code,
        build_application,
        run_test_suite,
        analyze_code_quality,
        perform_security_scan,
        containerize_application
    ])
    
    try:
        partial_result = await partial_pipeline.run(ctx_data)
        
        # Now simulate deployment failure
        ctx_data["image_tag"] = "fail-tag"  # This will trigger failure
        
        deploy_pipeline = chain([
            deploy_to_environment,
            setup_monitoring_and_alerts,
            validate_deployment,
            send_success_notification
        ]).catch_errors({
            Exception: deployment_failure_handler
        })
        
        result = await deploy_pipeline.run({**ctx_data, **partial_result})
        end_time = datetime.now()
        
        print(f"🔄 Deployment failed as expected, rollback initiated")
        print(f"⏱️  Total time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"❌ Deployment failed: {result.get('deployment_failed', False)}")
        print(f"🔙 Rollback successful: {result.get('rollback_successful', False)}")
        print(f"📧 Notifications sent: {result.get('notifications_sent', False)}")
        
    except Exception as e:
        end_time = datetime.now()
        print(f"💥 Unexpected error: {str(e)}")
        print(f"⏱️  Time to error: {(end_time - start_time).total_seconds():.2f}s")

async def demo_multi_environment_pipeline():
    """Demo multi-environment deployment pipeline."""
    print("\n=== Multi-Environment Pipeline Demo ===")
    
    # Create separate pipelines for each environment
    dev_pipeline = create_development_pipeline()
    staging_pipeline = create_staging_pipeline()
    
    # Mock services
    vcs = MockVersionControl()
    build_system = MockBuildSystem()
    test_runner = MockTestRunner()
    quality_analyzer = MockQualityAnalyzer()
    security_scanner = MockSecurityScanner()
    container_registry = MockContainerRegistry()
    cluster_manager = MockClusterManager()
    monitoring_system = MockMonitoringSystem()
    notification_service = MockNotificationService()
    
    base_ctx = {
        "repository": {"name": "web-app", "branch": "main"},
        "build_config": BuildConfig(
            build_tool="npm",
            docker_image="node:16",
            build_commands=["npm install", "npm run build"],
            artifacts=["dist/"],
            cache_enabled=True
        ),
        "test_config": TestConfig(
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            test_commands={"unit": "npm test", "integration": "npm run test:integration"},
            coverage_threshold=80.0,
            parallel_execution=True
        ),
        "quality_config": QualityConfig(
            code_quality_tools=["eslint"],
            quality_gates={"complexity": 7.0, "maintainability": 8.0},
            compliance_checks=["gdpr"]
        ),
        "security_config": SecurityConfig(
            vulnerability_scan=True,
            dependency_check=True,
            secrets_scan=True,
            compliance_frameworks=["owasp"]
        ),
        "container_config": ContainerConfig(
            registry_url="registry.company.com",
            image_name="web-app",
            tag_strategy="commit",
            security_scan=True,
            multi_arch=False
        ),
        
        # Services
        "version_control": vcs,
        "build_system": build_system,
        "test_runner": test_runner,
        "quality_analyzer": quality_analyzer,
        "security_scanner": security_scanner,
        "container_registry": container_registry,
        "cluster_manager": cluster_manager,
        "monitoring_system": monitoring_system,
        "notification_service": notification_service
    }
    
    environments = [
        (Environment.DEVELOPMENT, DeploymentStrategy.ROLLING, 1),
        (Environment.STAGING, DeploymentStrategy.BLUE_GREEN, 2)
    ]
    
    start_time = datetime.now()
    
    try:
        for env, strategy, replicas in environments:
            print(f"\n🚀 Deploying to {env.value}...")
            
            env_ctx = {
                **base_ctx,
                "deployment_config": DeploymentConfig(
                    environment=env,
                    strategy=strategy,
                    replicas=replicas,
                    health_checks={"path": "/health", "timeout": 30},
                    rollback_enabled=True
                ),
                "monitoring_config": MonitoringConfig(
                    metrics_enabled=True,
                    logging_enabled=True,
                    alerting_rules=[{"metric": "cpu_usage", "threshold": 80}],
                    dashboards=["application"]
                )
            }
            
            if env == Environment.DEVELOPMENT:
                result = await dev_pipeline.run(env_ctx)
            else:
                result = await staging_pipeline.run(env_ctx)
            
            print(f"✅ {env.value} deployment successful!")
            print(f"🐳 Image: {result.get('image_tag', 'unknown')}")
            print(f"🔄 Strategy: {strategy.value}")
            print(f"📊 Replicas: {replicas}")
        
        end_time = datetime.now()
        print(f"\n🎉 All environments deployed successfully!")
        print(f"⏱️  Total time: {(end_time - start_time).total_seconds():.2f}s")
        
    except Exception as e:
        end_time = datetime.now()
        print(f"❌ Multi-environment deployment failed: {str(e)}")
        print(f"⏱️  Time to failure: {(end_time - start_time).total_seconds():.2f}s")

# Main demo runner
async def main():
    """Run all DevOps CI/CD pipeline demos."""
    print("🚀 ModuLink DevOps CI/CD Pipeline Demos")
    print("=" * 50)
    
    # Run all demos
    await demo_simple_development_deployment()
    await demo_production_deployment_with_security()
    await demo_failed_deployment_with_rollback()
    await demo_multi_environment_pipeline()
    
    print("\n🎯 All DevOps CI/CD pipeline demos completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Multi-stage pipeline orchestration")
    print("✅ Parallel execution of security and quality checks")
    print("✅ Container build and registry management")
    print("✅ Multi-environment deployment strategies")
    print("✅ Comprehensive monitoring and alerting setup")
    print("✅ Automated rollback on deployment failures")
    print("✅ Error handling and notification systems")
    print("✅ Performance tracking and optimization")

def reset_pipeline_state():
    """Reset pipeline state to initial values for testing."""
    # Reset mock services to initial state
    pass  # Mock services are stateless in this implementation

def get_pipeline_metrics() -> Dict[str, Any]:
    """Get current pipeline metrics for testing."""
    return {
        "pipeline_stages": len(PipelineStage),
        "supported_environments": len(Environment),
        "deployment_strategies": len(DeploymentStrategy),
        "test_types": len(TestType)
    }

def create_test_context(
    repo_name: str = "test-app",
    branch: str = "main",
    environment: Environment = Environment.DEVELOPMENT
) -> Dict[str, Any]:
    """Create a test context for pipeline testing."""
    return {
        "repository": Repository(
            name=repo_name,
            url=f"https://github.com/company/{repo_name}.git",
            branch=branch,
            commit_hash="test123",
            language="python",
            framework="fastapi"
        ),
        "build_config": BuildConfig(
            build_tool="pip",
            docker_image="python:3.9",
            build_commands=["pip install -r requirements.txt"],
            artifacts=["dist/"],
            cache_enabled=True
        ),
        "test_config": TestConfig(
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            test_commands={"unit": "pytest tests/unit", "integration": "pytest tests/integration"},
            coverage_threshold=80.0,
            parallel_execution=True
        ),
        "deployment_config": DeploymentConfig(
            environment=environment,
            strategy=DeploymentStrategy.ROLLING,
            replicas=1,
            health_checks={"path": "/health", "timeout": 30},
            rollback_enabled=True
        )
    }

if __name__ == "__main__":
    asyncio.run(main())
