# ModuLink Testing Cookbook - Advanced Guide

## Overview

This cookbook covers advanced testing patterns for complex ModuLink workflows, including enterprise-scale systems, multi-environment deployments, state management, and comprehensive test strategies. Based on real-world examples from DevOps CI/CD pipelines and financial trading systems.

## Table of Contents

1. [Complex Workflow Testing Strategies](#complex-workflow-testing-strategies)
2. [State Management and Prerequisites](#state-management-and-prerequisites)
3. [Multi-Environment Testing](#multi-environment-testing)
4. [Testing Complex Dependencies](#testing-complex-dependencies)
5. [Performance and Load Testing](#performance-and-load-testing)
6. [Enterprise Testing Patterns](#enterprise-testing-patterns)
7. [Testing Real-World Examples](#testing-real-world-examples)
8. [Comprehensive Test Architecture](#comprehensive-test-architecture)

## Complex Workflow Testing Strategies

Learn to test enterprise-level workflows with multiple stages, complex dependencies, and various failure modes.

### Testing Multi-Stage Pipelines

Based on our DevOps CI/CD pipeline example, here's how to test complex multi-stage workflows:

```python
# Example: DevOps CI/CD Pipeline Testing
class TestComplexPipeline:
    """Test suite for complex multi-stage DevOps workflows."""
    
    def setup_method(self):
        """Reset pipeline state before each test."""
        # Clear any shared state
        self.pipeline_state = {}
        self.mock_services = self.setup_mock_services()
    
    def setup_mock_services(self):
        """Create comprehensive mock services for testing."""
        return {
            'version_control': MockVersionControl({
                'web-app': {'branch': 'main', 'commit': 'abc123'},
                'api-service': {'branch': 'develop', 'commit': 'def456'}
            }),
            'build_system': MockBuildSystem(),
            'test_runner': MockTestRunner(),
            'security_scanner': MockSecurityScanner(),
            'container_registry': MockContainerRegistry(),
            'cluster_manager': MockClusterManager()
        }
    
    @pytest.mark.asyncio
    async def test_complete_ci_cd_pipeline_success(self):
        """Test successful execution of complete CI/CD pipeline."""
        # Create the complete pipeline
        pipeline = chain([
            checkout_source_code,
            build_application,
            run_test_suite,
            analyze_code_quality,
            perform_security_scan,
            containerize_application,
            deploy_to_environment,
            validate_deployment,
            setup_monitoring_and_alerts
        ])
        
        # Comprehensive initial context
        context = {
            'repository': {
                'name': 'web-app',
                'branch': 'main',
                'owner': 'company'
            },
            'environment': Environment.PRODUCTION,
            'deployment_strategy': DeploymentStrategy.BLUE_GREEN,
            'build_config': {
                'dockerfile_path': './Dockerfile',
                'build_args': {'ENV': 'production'}
            },
            'test_config': {
                'test_types': [TestType.UNIT, TestType.INTEGRATION, TestType.E2E],
                'coverage_threshold': 0.8,
                'parallel_execution': True
            },
            'security_config': {
                'vulnerability_threshold': 'medium',
                'compliance_checks': ['OWASP', 'GDPR']
            },
            'deployment_config': {
                'replicas': 3,
                'health_check_path': '/health',
                'rollback_on_failure': True
            }
        }
        
        # Execute the pipeline
        result = await pipeline(context)
        
        # Comprehensive assertions
        assert result['checkout_successful'] is True
        assert result['build_successful'] is True
        assert result['tests_passed'] is True
        assert result['quality_analysis_passed'] is True
        assert result['security_scan_passed'] is True
        assert result['container_built'] is True
        assert result['deployment_successful'] is True
        assert result['validation_successful'] is True
        assert result['monitoring_configured'] is True
        
        # Verify deployment details
        assert result['replicas_running'] >= 3
        assert 'deployment_url' in result
        assert 'monitoring_dashboard_url' in result
    
    @pytest.mark.asyncio
    async def test_pipeline_failure_at_each_stage(self):
        """Test pipeline failure handling at different stages."""
        stages_and_failures = [
            ('checkout', {'repository': {'name': 'non-existent-repo'}}),
            ('build', {'build_config': {'dockerfile_path': '/invalid/path'}}),
            ('test', {'test_config': {'coverage_threshold': 1.0}}),  # Impossible threshold
            ('security', {'security_config': {'vulnerability_threshold': 'none'}}),
            ('deploy', {'deployment_config': {'replicas': 0}})  # Invalid replica count
        ]
        
        for stage_name, failing_context in stages_and_failures:
            with pytest.raises(Exception) as exc_info:
                pipeline = self.create_pipeline_up_to_stage(stage_name)
                await pipeline(failing_context)
            
            # Verify appropriate error type and message
            assert stage_name.lower() in str(exc_info.value).lower()
    
    def create_pipeline_up_to_stage(self, stage_name: str) -> chain:
        """Create pipeline that includes stages up to the specified stage."""
        stage_functions = {
            'checkout': [checkout_source_code],
            'build': [checkout_source_code, build_application],
            'test': [checkout_source_code, build_application, run_test_suite],
            'security': [checkout_source_code, build_application, run_test_suite, 
                        analyze_code_quality, perform_security_scan],
            'deploy': [checkout_source_code, build_application, run_test_suite,
                      analyze_code_quality, perform_security_scan, 
                      containerize_application, deploy_to_environment]
        }
        
        return chain(stage_functions.get(stage_name, []))
```

### Testing Conditional Workflows

```python
class TestConditionalWorkflows:
    """Test workflows that branch based on conditions."""
    
    @pytest.mark.asyncio
    async def test_environment_specific_deployment(self):
        """Test that deployments behave differently per environment."""
        environments_and_expectations = [
            (Environment.DEVELOPMENT, {'replicas_running': 1, 'monitoring_level': 'basic'}),
            (Environment.STAGING, {'replicas_running': 2, 'monitoring_level': 'standard'}),
            (Environment.PRODUCTION, {'replicas_running': 3, 'monitoring_level': 'comprehensive'})
        ]
        
        for env, expected in environments_and_expectations:
            context = self.create_base_context()
            context['environment'] = env
            
            deployment_workflow = chain([
                containerize_application,
                deploy_to_environment,
                setup_monitoring_and_alerts
            ])
            
            result = await deployment_workflow(context)
            
            assert result['replicas_running'] == expected['replicas_running']
            assert result['monitoring_level'] == expected['monitoring_level']
    
    @pytest.mark.asyncio
    async def test_deployment_strategy_variations(self):
        """Test different deployment strategies."""
        strategies_and_behavior = [
            (DeploymentStrategy.ROLLING_UPDATE, {'downtime_expected': False}),
            (DeploymentStrategy.BLUE_GREEN, {'old_version_preserved': True}),
            (DeploymentStrategy.CANARY, {'traffic_split': True})
        ]
        
        for strategy, expected_behavior in strategies_and_behavior:
            context = self.create_base_context()
            context['deployment_strategy'] = strategy
            
            result = await deploy_to_environment(context)
            
            for key, expected_value in expected_behavior.items():
                assert result[key] == expected_value
```

## State Management and Prerequisites

Complex workflows often have intricate state dependencies. Here's how to test them effectively.

### Testing Prerequisite Chains

```python
class TestPrerequisiteChains:
    """Test workflows with complex prerequisite dependencies."""
    
    def create_context_with_prerequisites(self, completed_stages: List[str]) -> Dict[str, Any]:
        """Create context with specified prerequisites completed."""
        context = self.create_base_context()
        
        # Map of prerequisite flags
        prerequisite_map = {
            'checkout': 'checkout_successful',
            'build': 'build_successful',
            'test': 'tests_passed',
            'quality': 'quality_analysis_passed',
            'security': 'security_scan_passed',
            'container': 'container_built',
            'deploy': 'deployment_successful'
        }
        
        # Set prerequisites based on completed stages
        for stage in completed_stages:
            if stage in prerequisite_map:
                context[prerequisite_map[stage]] = True
        
        return context
    
    @pytest.mark.asyncio
    async def test_deployment_prerequisites(self):
        """Test that deployment requires all prerequisites."""
        # Test with missing prerequisites
        incomplete_contexts = [
            (['checkout', 'build'], "Cannot deploy without container image"),
            (['checkout', 'build', 'test'], "Cannot deploy without container image"),
            (['checkout', 'build', 'test', 'quality'], "Cannot deploy without container image")
        ]
        
        for completed_stages, expected_error in incomplete_contexts:
            context = self.create_context_with_prerequisites(completed_stages)
            
            with pytest.raises(Exception, match=expected_error):
                await deploy_to_environment(context)
    
    @pytest.mark.asyncio
    async def test_security_scan_prerequisites(self):
        """Test that security scan requires quality analysis."""
        # Should fail without quality analysis
        context = self.create_context_with_prerequisites(['checkout', 'build', 'test'])
        
        with pytest.raises(Exception, match="Cannot proceed with security scan after quality failures"):
            await perform_security_scan(context)
        
        # Should succeed with quality analysis
        context = self.create_context_with_prerequisites(['checkout', 'build', 'test', 'quality'])
        
        result = await perform_security_scan(context)
        assert result['security_scan_passed'] is True
    
    @pytest.mark.asyncio
    async def test_quality_analysis_prerequisites(self):
        """Test that quality analysis requires tests to pass."""
        # Should fail without passing tests
        context = self.create_context_with_prerequisites(['checkout', 'build'])
        
        with pytest.raises(Exception, match="Cannot proceed with quality analysis after test failures"):
            await analyze_code_quality(context)
        
        # Should succeed with passing tests
        context = self.create_context_with_prerequisites(['checkout', 'build', 'test'])
        
        result = await analyze_code_quality(context)
        assert result['quality_analysis_passed'] is True
```

### Testing State Transitions

```python
class TestStateTransitions:
    """Test how workflow state changes through execution."""
    
    @pytest.mark.asyncio
    async def test_state_accumulation_through_pipeline(self):
        """Test that state accumulates correctly through pipeline stages."""
        pipeline = chain([
            checkout_source_code,
            build_application,
            run_test_suite,
            analyze_code_quality
        ])
        
        initial_context = self.create_base_context()
        
        # Track state at each stage
        stage_results = []
        
        # Create pipeline with state tracking
        async def track_state(stage_func):
            async def wrapper(ctx):
                result = await stage_func(ctx)
                stage_results.append(result.copy())
                return result
            return wrapper
        
        tracked_pipeline = chain([
            track_state(checkout_source_code),
            track_state(build_application),
            track_state(run_test_suite),
            track_state(analyze_code_quality)
        ])
        
        final_result = await tracked_pipeline(initial_context)
        
        # Verify state accumulation
        assert len(stage_results) == 4
        
        # After checkout
        assert stage_results[0]['checkout_successful'] is True
        assert 'build_successful' not in stage_results[0]
        
        # After build
        assert stage_results[1]['checkout_successful'] is True
        assert stage_results[1]['build_successful'] is True
        assert 'tests_passed' not in stage_results[1]
        
        # After tests
        assert stage_results[2]['tests_passed'] is True
        assert 'quality_analysis_passed' not in stage_results[2]
        
        # After quality analysis
        assert stage_results[3]['quality_analysis_passed'] is True
        
        # Final result should have all state
        assert final_result['checkout_successful'] is True
        assert final_result['build_successful'] is True
        assert final_result['tests_passed'] is True
        assert final_result['quality_analysis_passed'] is True
```

## Multi-Environment Testing

Test workflows that behave differently across environments.

### Environment-Specific Behavior Testing

```python
class TestMultiEnvironmentWorkflows:
    """Test workflows across different environments."""
    
    @pytest.mark.parametrize("environment,expected_config", [
        (Environment.DEVELOPMENT, {
            'replicas': 1,
            'monitoring_level': 'basic',
            'security_level': 'standard',
            'resource_limits': {'cpu': '100m', 'memory': '128Mi'}
        }),
        (Environment.STAGING, {
            'replicas': 2,
            'monitoring_level': 'standard',
            'security_level': 'enhanced',
            'resource_limits': {'cpu': '200m', 'memory': '256Mi'}
        }),
        (Environment.PRODUCTION, {
            'replicas': 3,
            'monitoring_level': 'comprehensive',
            'security_level': 'maximum',
            'resource_limits': {'cpu': '500m', 'memory': '512Mi'}
        })
    ])
    @pytest.mark.asyncio
    async def test_environment_specific_deployment(self, environment, expected_config):
        """Test that deployments are configured correctly per environment."""
        context = self.create_base_context()
        context['environment'] = environment
        
        # Add all prerequisites
        context.update({
            'checkout_successful': True,
            'build_successful': True,
            'tests_passed': True,
            'quality_analysis_passed': True,
            'security_scan_passed': True,
            'container_built': True
        })
        
        result = await deploy_to_environment(context)
        
        assert result['deployment_successful'] is True
        assert result['replicas_running'] == expected_config['replicas']
        assert result['monitoring_level'] == expected_config['monitoring_level']
        assert result['security_configuration'] == expected_config['security_level']
        assert result['resource_configuration'] == expected_config['resource_limits']
    
    @pytest.mark.asyncio
    async def test_cross_environment_promotion_workflow(self):
        """Test promoting deployments across environments."""
        # Simulate a complete promotion workflow
        environments = [Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION]
        
        promotion_context = self.create_base_context()
        
        for env in environments:
            promotion_context['environment'] = env
            
            # Complete deployment for this environment
            env_pipeline = self.create_environment_pipeline(env)
            result = await env_pipeline(promotion_context)
            
            # Verify deployment succeeded
            assert result['deployment_successful'] is True
            
            # Promote successful deployment info to next environment
            promotion_context['previous_deployment'] = {
                'environment': env,
                'deployment_id': result['deployment_id'],
                'artifacts': result.get('artifacts', {})
            }
    
    def create_environment_pipeline(self, environment: Environment) -> chain:
        """Create environment-specific deployment pipeline."""
        base_stages = [
            containerize_application,
            deploy_to_environment,
            validate_deployment
        ]
        
        if environment == Environment.PRODUCTION:
            # Production includes additional monitoring and security
            base_stages.extend([
                setup_monitoring_and_alerts,
                configure_backup_and_recovery,
                enable_security_monitoring
            ])
        
        return chain(base_stages)
```

## Testing Complex Dependencies

Handle workflows with intricate dependency relationships.

### Testing Service Dependencies

```python
class TestServiceDependencies:
    """Test workflows with complex service dependencies."""
    
    @pytest.mark.asyncio
    async def test_service_dependency_resolution(self):
        """Test that service dependencies are resolved correctly."""
        # Mock multiple interdependent services
        services = {
            'database': MockDatabaseService(),
            'cache': MockCacheService(),
            'message_queue': MockMessageQueueService(),
            'file_storage': MockFileStorageService()
        }
        
        # Create workflow that depends on all services
        complex_workflow = chain([
            initialize_database_connection,
            setup_cache_layer,
            configure_message_processing,
            initialize_file_storage,
            validate_all_services
        ])
        
        context = {
            'services': services,
            'service_config': {
                'database_url': 'postgresql://localhost:5432/testdb',
                'cache_url': 'redis://localhost:6379',
                'queue_url': 'amqp://localhost:5672',
                'storage_path': '/tmp/test_storage'
            }
        }
        
        result = await complex_workflow(context)
        
        # Verify all services are initialized
        assert result['database_connected'] is True
        assert result['cache_initialized'] is True
        assert result['message_queue_connected'] is True
        assert result['file_storage_ready'] is True
        assert result['all_services_validated'] is True
    
    @pytest.mark.asyncio
    async def test_service_failure_cascading(self):
        """Test how service failures cascade through dependencies."""
        # Test database failure affects dependent services
        failing_services = {
            'database': MockDatabaseService(should_fail=True),
            'cache': MockCacheService(),
            'message_queue': MockMessageQueueService(),
            'file_storage': MockFileStorageService()
        }
        
        workflow_with_error_handling = chain([
            initialize_database_connection,
            setup_cache_layer,
            configure_message_processing
        ]).catch_errors({
            DatabaseConnectionError: handle_database_failure,
            Exception: handle_general_service_failure
        })
        
        context = {'services': failing_services}
        
        result = await workflow_with_error_handling(context)
        
        # Verify error handling
        assert result['database_connected'] is False
        assert result['error_handled'] is True
        assert result['fallback_activated'] is True
```

## Performance and Load Testing

Test how workflows perform under various load conditions.

### Testing Pipeline Performance

```python
class TestPipelinePerformance:
    """Test performance characteristics of complex workflows."""
    
    @pytest.mark.asyncio
    async def test_pipeline_execution_time(self):
        """Test that pipeline executes within acceptable time limits."""
        pipeline = create_development_pipeline()
        context = self.create_optimized_context()
        
        start_time = time.time()
        result = await pipeline(context)
        execution_time = time.time() - start_time
        
        # Pipeline should complete within 30 seconds
        assert execution_time < 30.0, f"Pipeline took {execution_time}s, expected < 30s"
        assert result['deployment_successful'] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution(self):
        """Test multiple pipelines running concurrently."""
        pipeline = create_development_pipeline()
        
        # Create multiple contexts for parallel execution
        contexts = [
            self.create_context_for_repo(f'repo-{i}')
            for i in range(5)
        ]
        
        start_time = time.time()
        
        # Execute pipelines concurrently
        results = await asyncio.gather(
            *[pipeline(ctx) for ctx in contexts],
            return_exceptions=True
        )
        
        execution_time = time.time() - start_time
        
        # Should complete concurrent executions efficiently
        assert execution_time < 60.0, f"5 concurrent pipelines took {execution_time}s"
        
        # Verify all succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 5
    
    @pytest.mark.asyncio
    async def test_pipeline_resource_usage(self):
        """Test pipeline resource consumption."""
        import psutil
        import os
        
        # Get initial resource usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        initial_cpu_percent = process.cpu_percent()
        
        # Execute resource-intensive pipeline
        heavy_pipeline = create_production_pipeline()
        context = self.create_large_context()
        
        result = await heavy_pipeline(context)
        
        # Check resource usage after execution
        final_memory = process.memory_info().rss
        final_cpu_percent = process.cpu_percent()
        
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"
        
        # CPU usage should be manageable
        assert final_cpu_percent < 80.0, f"CPU usage: {final_cpu_percent}%"
        
        assert result['deployment_successful'] is True
```

### Load Testing Patterns

```python
class TestLoadScenarios:
    """Test workflows under various load conditions."""
    
    @pytest.mark.asyncio
    async def test_high_throughput_processing(self):
        """Test workflow handling high throughput."""
        # Create batch processing workflow
        batch_workflow = chain([
            load_batch_items,
            validate_batch_items,
            process_batch_items,
            store_batch_results
        ])
        
        # Large batch context
        context = {
            'batch_size': 1000,
            'items': [{'id': i, 'data': f'item_{i}'} for i in range(1000)]
        }
        
        start_time = time.time()
        result = await batch_workflow(context)
        processing_time = time.time() - start_time
        
        # Should process 1000 items efficiently
        throughput = len(context['items']) / processing_time
        assert throughput > 50, f"Throughput: {throughput:.2f} items/sec, expected > 50"
        
        assert result['batch_processed'] is True
        assert len(result['processed_items']) == 1000
    
    @pytest.mark.asyncio
    async def test_stress_testing_with_failures(self):
        """Test workflow behavior under stress with intermittent failures."""
        # Create workflow with simulated failures
        unreliable_workflow = chain([
            checkout_source_code,
            build_with_random_failures,  # Fails 20% of the time
            run_tests_with_flaky_behavior,  # Has intermittent issues
            deploy_with_retry_logic
        ]).catch_errors({
            Exception: retry_with_backoff
        })
        
        contexts = [self.create_base_context() for _ in range(20)]
        
        # Execute with some expected failures
        results = await asyncio.gather(
            *[unreliable_workflow(ctx) for ctx in contexts],
            return_exceptions=True
        )
        
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        # Should have reasonable success rate even with failures
        success_rate = len(successful_results) / len(results)
        assert success_rate > 0.7, f"Success rate: {success_rate:.2%}, expected > 70%"
        
        # Failed results should be handled gracefully
        for failure in failed_results:
            assert hasattr(failure, 'retry_attempted')
```

## Enterprise Testing Patterns

Patterns for testing large-scale, enterprise workflows.

### Testing Compliance and Governance

```python
class TestComplianceAndGovernance:
    """Test workflows for compliance and governance requirements."""
    
    @pytest.mark.asyncio
    async def test_security_compliance_workflow(self):
        """Test that workflows meet security compliance requirements."""
        compliance_pipeline = chain([
            validate_security_credentials,
            scan_for_vulnerabilities,
            check_compliance_policies,
            generate_security_report,
            store_audit_trail
        ])
        
        context = {
            'security_config': {
                'compliance_standards': ['SOC2', 'ISO27001', 'GDPR'],
                'vulnerability_threshold': 'high',
                'audit_required': True
            },
            'credentials': self.get_test_credentials()
        }
        
        result = await compliance_pipeline(context)
        
        # Verify compliance checks
        assert result['security_scan_passed'] is True
        assert result['compliance_verified'] is True
        assert result['audit_trail_created'] is True
        assert 'security_report_url' in result
        
        # Verify specific compliance requirements
        compliance_results = result['compliance_results']
        assert compliance_results['SOC2']['status'] == 'passed'
        assert compliance_results['ISO27001']['status'] == 'passed'
        assert compliance_results['GDPR']['status'] == 'passed'
    
    @pytest.mark.asyncio
    async def test_data_governance_workflow(self):
        """Test data governance and privacy requirements."""
        data_pipeline = chain([
            classify_data_sensitivity,
            apply_data_protection,
            validate_data_retention_policies,
            ensure_data_lineage,
            generate_privacy_report
        ])
        
        context = {
            'data_classification': 'PII',
            'retention_period': '7_years',
            'privacy_regulations': ['GDPR', 'CCPA'],
            'data_sources': ['customer_db', 'transaction_logs']
        }
        
        result = await data_pipeline(context)
        
        assert result['data_classified'] is True
        assert result['protection_applied'] is True
        assert result['retention_policy_valid'] is True
        assert result['lineage_documented'] is True
        assert result['privacy_compliant'] is True
```

### Testing Disaster Recovery

```python
class TestDisasterRecovery:
    """Test disaster recovery and business continuity workflows."""
    
    @pytest.mark.asyncio
    async def test_backup_and_recovery_workflow(self):
        """Test backup and recovery procedures."""
        backup_workflow = chain([
            create_application_backup,
            create_database_backup,
            store_backup_remotely,
            verify_backup_integrity,
            test_recovery_procedure
        ])
        
        context = {
            'backup_config': {
                'retention_days': 30,
                'compression': True,
                'encryption': True,
                'remote_storage': 's3://backup-bucket/'
            }
        }
        
        result = await backup_workflow(context)
        
        assert result['application_backup_created'] is True
        assert result['database_backup_created'] is True
        assert result['backup_stored_remotely'] is True
        assert result['backup_integrity_verified'] is True
        assert result['recovery_test_passed'] is True
    
    @pytest.mark.asyncio
    async def test_failover_workflow(self):
        """Test failover to secondary systems."""
        failover_workflow = chain([
            detect_primary_system_failure,
            initiate_failover_procedure,
            switch_traffic_to_secondary,
            validate_secondary_system,
            notify_operations_team
        ])
        
        # Simulate primary system failure
        context = {
            'primary_system': {'status': 'failed', 'last_response': '2024-01-01T10:00:00Z'},
            'secondary_system': {'status': 'ready', 'capacity': '100%'},
            'failover_config': {'auto_failover': True, 'max_downtime': '5_minutes'}
        }
        
        result = await failover_workflow(context)
        
        assert result['failure_detected'] is True
        assert result['failover_initiated'] is True
        assert result['traffic_switched'] is True
        assert result['secondary_validated'] is True
        assert result['team_notified'] is True
        assert result['downtime_duration'] < 300  # Less than 5 minutes
```

## Testing Real-World Examples

Comprehensive examples based on our DevOps and Financial systems.

### DevOps Pipeline Testing Example

```python
class TestRealWorldDevOpsPipeline:
    """Complete test suite for production DevOps pipeline."""
    
    @pytest.fixture
    def pipeline_context(self):
        """Fixture providing realistic pipeline context."""
        return {
            'repository': {
                'name': 'web-application',
                'branch': 'main',
                'owner': 'company-org'
            },
            'environment': Environment.PRODUCTION,
            'deployment_strategy': DeploymentStrategy.BLUE_GREEN,
            'build_config': {
                'dockerfile_path': './Dockerfile',
                'build_args': {'NODE_ENV': 'production', 'API_VERSION': 'v2'},
                'target_platforms': ['linux/amd64', 'linux/arm64']
            },
            'test_config': {
                'test_types': [TestType.UNIT, TestType.INTEGRATION, TestType.E2E, TestType.PERFORMANCE],
                'coverage_threshold': 0.85,
                'parallel_execution': True,
                'test_timeout': 1800  # 30 minutes
            },
            'quality_config': {
                'quality_gates': ['code_coverage', 'complexity', 'duplication', 'security'],
                'sonarqube_project': 'company-web-app',
                'quality_threshold': 'A'
            },
            'security_config': {
                'vulnerability_threshold': 'medium',
                'compliance_checks': ['OWASP_TOP_10', 'SANS_25'],
                'security_tools': ['snyk', 'trivy', 'clair']
            },
            'deployment_config': {
                'replicas': 5,
                'resource_requests': {'cpu': '500m', 'memory': '1Gi'},
                'resource_limits': {'cpu': '1000m', 'memory': '2Gi'},
                'health_check_path': '/api/health',
                'readiness_probe_delay': 30,
                'liveness_probe_delay': 60,
                'rollback_on_failure': True,
                'max_surge': 2,
                'max_unavailable': 1
            },
            'monitoring_config': {
                'metrics_collection': True,
                'log_aggregation': True,
                'alerting_enabled': True,
                'dashboard_creation': True,
                'notification_channels': ['slack', 'email', 'pagerduty']
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_production_deployment(self, pipeline_context):
        """Test complete production deployment workflow."""
        production_pipeline = create_production_pipeline()
        
        result = await production_pipeline(pipeline_context)
        
        # Verify all stages completed successfully
        self.verify_complete_pipeline_success(result)
        
        # Verify production-specific configurations
        assert result['replicas_running'] == 5
        assert result['blue_green_deployment'] is True
        assert result['zero_downtime_deployment'] is True
        assert result['monitoring_comprehensive'] is True
    
    @pytest.mark.asyncio
    async def test_rollback_on_deployment_failure(self, pipeline_context):
        """Test rollback procedure when deployment fails."""
        # Inject deployment failure
        pipeline_context['deployment_config']['simulate_failure'] = True
        
        production_pipeline = create_production_pipeline_with_rollback()
        
        result = await production_pipeline(pipeline_context)
        
        # Verify rollback occurred
        assert result['deployment_failed'] is True
        assert result['rollback_initiated'] is True
        assert result['rollback_successful'] is True
        assert result['previous_version_restored'] is True
    
    def verify_complete_pipeline_success(self, result: Dict[str, Any]):
        """Verify all pipeline stages completed successfully."""
        required_stages = [
            'checkout_successful',
            'build_successful',
            'tests_passed',
            'quality_analysis_passed',
            'security_scan_passed',
            'container_built',
            'deployment_successful',
            'validation_successful',
            'monitoring_configured'
        ]
        
        for stage in required_stages:
            assert result.get(stage) is True, f"Stage {stage} did not complete successfully"
```

### Financial Trading System Testing Example

```python
class TestRealWorldTradingSystem:
    """Complete test suite for financial trading system."""
    
    @pytest.fixture
    def trading_context(self):
        """Fixture providing realistic trading context."""
        return {
            'market_data': {
                'symbol': 'AAPL',
                'current_price': 150.00,
                'volume': 1000000,
                'bid': 149.95,
                'ask': 150.05,
                'timestamp': datetime.now().isoformat()
            },
            'trading_strategy': {
                'name': 'momentum_strategy',
                'parameters': {
                    'short_window': 10,
                    'long_window': 30,
                    'threshold': 0.02
                }
            },
            'risk_parameters': {
                'max_position_size': 10000,
                'stop_loss_percentage': 0.05,
                'max_daily_loss': 50000,
                'position_limits': {'AAPL': 5000}
            },
            'compliance_rules': {
                'enabled': True,
                'rules': ['position_limits', 'concentration_risk', 'regulatory_checks'],
                'jurisdiction': 'US'
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_trading_workflow(self, trading_context):
        """Test complete trading workflow from signal to execution."""
        trading_pipeline = chain([
            fetch_market_data,
            calculate_trading_signals,
            evaluate_risk_parameters,
            check_compliance_rules,
            generate_trading_orders,
            execute_trades,
            update_portfolio_positions,
            log_trading_activity
        ])
        
        result = await trading_pipeline(trading_context)
        
        # Verify trading workflow completed
        assert result['market_data_updated'] is True
        assert result['signals_calculated'] is True
        assert result['risk_evaluated'] is True
        assert result['compliance_checked'] is True
        assert result['orders_generated'] is True
        assert result['trades_executed'] is True
        assert result['portfolio_updated'] is True
        assert result['activity_logged'] is True
    
    @pytest.mark.asyncio
    async def test_risk_management_prevents_dangerous_trades(self, trading_context):
        """Test that risk management prevents dangerous trading scenarios."""
        # Set up dangerous trading scenario
        dangerous_context = trading_context.copy()
        dangerous_context['proposed_trade'] = {
            'symbol': 'AAPL',
            'quantity': 20000,  # Exceeds max position size
            'side': 'buy',
            'price': 150.00
        }
        
        risk_aware_pipeline = chain([
            calculate_trading_signals,
            evaluate_risk_parameters,
            check_compliance_rules
        ])
        
        with pytest.raises(Exception, match="Position size exceeds limit"):
            await risk_aware_pipeline(dangerous_context)
    
    @pytest.mark.asyncio
    async def test_compliance_violations_block_trades(self, trading_context):
        """Test that compliance violations prevent trade execution."""
        # Set up compliance violation scenario
        violation_context = trading_context.copy()
        violation_context['portfolio_concentration'] = {
            'AAPL': 0.35  # 35% concentration exceeds typical limits
        }
        
        compliance_pipeline = chain([
            check_portfolio_concentration,
            evaluate_regulatory_requirements,
            validate_trading_permissions
        ])
        
        with pytest.raises(Exception, match="Portfolio concentration risk"):
            await compliance_pipeline(violation_context)
```

## Comprehensive Test Architecture

Structure your test suites for maximum maintainability and coverage.

### Test Suite Organization

```python
# tests/conftest.py
"""Shared test configuration and fixtures."""

@pytest.fixture(scope="session")
def test_environment():
    """Session-scoped test environment setup."""
    # Set up test databases, services, etc.
    pass

@pytest.fixture
def mock_services():
    """Provide comprehensive mock services."""
    return {
        'version_control': MockVersionControl(),
        'build_system': MockBuildSystem(),
        'test_runner': MockTestRunner(),
        'security_scanner': MockSecurityScanner(),
        'notification_service': MockNotificationService()
    }

# tests/unit/test_individual_functions.py
"""Unit tests for individual workflow functions."""

# tests/integration/test_workflow_chains.py
"""Integration tests for workflow chains."""

# tests/e2e/test_complete_workflows.py
"""End-to-end tests for complete workflows."""

# tests/performance/test_load_and_performance.py
"""Performance and load testing."""

# tests/compliance/test_security_and_governance.py
"""Compliance and governance testing."""
```

### Test Data Management

```python
class TestDataFactory:
    """Factory for creating consistent test data."""
    
    @staticmethod
    def create_repository_data(name: str = "test-repo") -> Dict[str, Any]:
        """Create repository test data."""
        return {
            'name': name,
            'branch': 'main',
            'owner': 'test-org',
            'commit_hash': 'abc123def456',
            'last_modified': datetime.now().isoformat()
        }
    
    @staticmethod
    def create_build_config(environment: Environment = Environment.DEVELOPMENT) -> Dict[str, Any]:
        """Create build configuration test data."""
        configs = {
            Environment.DEVELOPMENT: {
                'dockerfile_path': './Dockerfile.dev',
                'build_args': {'NODE_ENV': 'development'},
                'cache_enabled': True
            },
            Environment.PRODUCTION: {
                'dockerfile_path': './Dockerfile',
                'build_args': {'NODE_ENV': 'production'},
                'cache_enabled': False,
                'multi_stage': True
            }
        }
        return configs.get(environment, configs[Environment.DEVELOPMENT])
    
    @staticmethod
    def create_complete_context(environment: Environment = Environment.DEVELOPMENT) -> Dict[str, Any]:
        """Create complete workflow context."""
        return {
            'repository': TestDataFactory.create_repository_data(),
            'environment': environment,
            'build_config': TestDataFactory.create_build_config(environment),
            'test_config': TestDataFactory.create_test_config(),
            'deployment_config': TestDataFactory.create_deployment_config(environment)
        }
```

## Key Takeaways

1. **Test Complex Prerequisites** - Ensure prerequisite chains work correctly
2. **Mock External Dependencies** - Isolate workflow logic from external services
3. **Test Multiple Environments** - Verify behavior across different deployment targets
4. **Performance Testing** - Ensure workflows perform acceptably under load
5. **Compliance Testing** - Verify regulatory and security requirements
6. **Disaster Recovery** - Test backup, recovery, and failover procedures
7. **Comprehensive Organization** - Structure tests for maintainability and coverage

These advanced patterns enable you to test enterprise-scale ModuLink workflows with confidence, ensuring they work correctly in production environments with complex requirements and constraints.

## Next Steps

- Apply these patterns to your own complex workflows
- Adapt the examples to your specific domain requirements
- Build comprehensive test suites that provide confidence in production deployments
- Consider automating these tests as part of your CI/CD pipeline

Remember: Comprehensive testing of complex workflows is an investment in system reliability and team confidence!
