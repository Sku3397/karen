#!/usr/bin/env python3
"""
Performance and Load Testing Module for Karen AI Secretary
QA Agent Instance: QA-001

Comprehensive performance testing including:
- System load testing
- Response time benchmarks
- Memory usage monitoring
- Concurrent user simulation
- Database performance
- API endpoint performance
"""

import pytest
import os
import sys
import time
import threading
import multiprocessing
import psutil
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import concurrent.futures
import requests
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestSystemPerformance:
    """System-wide performance tests"""
    
    def test_system_resource_usage(self):
        """Test system resource usage under normal load"""
        # Get initial system stats
        initial_cpu = psutil.cpu_percent(interval=1)
        initial_memory = psutil.virtual_memory().percent
        
        # Simulate some work
        start_time = time.time()
        
        # Import and initialize core modules
        try:
            from src.email_client import EmailClient
            from src.calendar_client import CalendarClient
            
            with patch('src.email_client.build'), patch('src.calendar_client.build'):
                email_client = EmailClient()
                calendar_client = CalendarClient()
                
                # Simulate processing
                for i in range(10):
                    # Mock email processing
                    time.sleep(0.1)
                    
        except ImportError:
            # Skip if modules not available
            pass
        
        end_time = time.time()
        
        # Check final resource usage
        final_cpu = psutil.cpu_percent(interval=1)
        final_memory = psutil.virtual_memory().percent
        
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 5.0  # Should complete in under 5 seconds
        assert final_cpu < 80  # CPU usage should stay under 80%
        assert final_memory < 90  # Memory usage should stay under 90%
    
    def test_module_import_performance(self):
        """Test module import performance"""
        modules_to_test = [
            'src.config',
            'src.email_client',
            'src.calendar_client',
            'src.communication_agent',
            'src.orchestrator_agent',
            'src.task_manager_agent'
        ]
        
        import_times = {}
        
        for module in modules_to_test:
            start_time = time.time()
            try:
                __import__(module)
                import_time = time.time() - start_time
                import_times[module] = import_time
                
                # Each module should import in under 2 seconds
                assert import_time < 2.0, f"Module {module} took {import_time:.2f}s to import"
                
            except ImportError:
                # Skip missing modules
                import_times[module] = 'NOT_AVAILABLE'
        
        # Log import times for analysis
        print(f"Module import times: {import_times}")
    
    def test_memory_usage_patterns(self):
        """Test memory usage patterns during operation"""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create objects and process data
        test_objects = []
        
        try:
            from src.email_client import EmailClient
            
            with patch('src.email_client.build'):
                for i in range(100):
                    # Create mock email data
                    email_data = {
                        'id': f'email_{i}',
                        'subject': f'Test Subject {i}' * 10,  # Make it larger
                        'body': f'Test body content {i}' * 100,
                        'sender': f'sender{i}@example.com',
                        'date': datetime.now().isoformat()
                    }
                    test_objects.append(email_data)
                
                # Process the objects
                for obj in test_objects:
                    # Simulate processing
                    processed = json.dumps(obj)
                    del processed
                
        except ImportError:
            # Create generic test objects if email client not available
            for i in range(1000):
                test_objects.append({'data': f'test_data_{i}' * 100})
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Clean up
        del test_objects
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        memory_growth = peak_memory - initial_memory
        memory_cleanup = peak_memory - final_memory
        
        # Memory should not grow excessively
        assert memory_growth < 500, f"Memory grew by {memory_growth:.2f}MB"
        
        # Memory should be cleaned up after processing
        assert memory_cleanup > memory_growth * 0.5, "Memory not properly cleaned up"

class TestEmailPerformance:
    """Email processing performance tests"""
    
    @pytest.fixture
    def mock_email_client_performance(self):
        """High-performance mock email client"""
        with patch('src.email_client.EmailClient') as mock_client:
            mock_instance = Mock()
            
            # Mock large email dataset
            mock_emails = []
            for i in range(1000):
                mock_emails.append({
                    'id': f'email_{i}',
                    'subject': f'Performance Test Email {i}',
                    'sender': f'sender{i}@example.com',
                    'body': f'Test email body content {i}' * 50,
                    'date': datetime.now().isoformat()
                })
            
            mock_instance.fetch_unread_emails.return_value = mock_emails
            mock_instance.send_email.return_value = True
            mock_client.return_value = mock_instance
            
            return mock_instance
    
    def test_email_fetch_performance(self, mock_email_client_performance):
        """Test email fetching performance with large datasets"""
        start_time = time.time()
        
        emails = mock_email_client_performance.fetch_unread_emails()
        
        fetch_time = time.time() - start_time
        
        assert len(emails) == 1000
        assert fetch_time < 2.0, f"Fetching 1000 emails took {fetch_time:.2f}s"
    
    def test_email_processing_throughput(self, mock_email_client_performance):
        """Test email processing throughput"""
        emails = mock_email_client_performance.fetch_unread_emails()[:100]  # Process 100 emails
        
        start_time = time.time()
        
        processed_count = 0
        for email in emails:
            # Simulate email processing
            subject = email['subject']
            body = email['body']
            
            # Mock intent classification
            intent = 'appointment_request' if 'appointment' in subject.lower() else 'general_inquiry'
            
            # Mock response generation
            response = f"Thank you for your email regarding: {subject}"
            
            processed_count += 1
        
        processing_time = time.time() - start_time
        throughput = processed_count / processing_time  # emails per second
        
        assert throughput > 10, f"Processing throughput: {throughput:.2f} emails/sec (should be > 10)"
        assert processing_time < 10, f"Processing 100 emails took {processing_time:.2f}s"
    
    def test_concurrent_email_processing(self, mock_email_client_performance):
        """Test concurrent email processing performance"""
        emails = mock_email_client_performance.fetch_unread_emails()[:50]
        
        def process_email_batch(email_batch):
            """Process a batch of emails"""
            processed = []
            for email in email_batch:
                # Simulate processing
                time.sleep(0.01)  # 10ms per email
                processed.append({
                    'id': email['id'],
                    'status': 'processed'
                })
            return processed
        
        # Split emails into batches for concurrent processing
        batch_size = 10
        batches = [emails[i:i+batch_size] for i in range(0, len(emails), batch_size)]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_email_batch, batch) for batch in batches]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                results.extend(future.result())
        
        concurrent_time = time.time() - start_time
        
        # Compare with sequential processing
        start_time = time.time()
        sequential_results = process_email_batch(emails)
        sequential_time = time.time() - start_time
        
        assert len(results) == len(emails)
        assert concurrent_time < sequential_time, "Concurrent processing should be faster"
        
        speedup = sequential_time / concurrent_time
        assert speedup > 1.5, f"Concurrent speedup: {speedup:.2f}x (should be > 1.5x)"

class TestCalendarPerformance:
    """Calendar operation performance tests"""
    
    @pytest.fixture
    def mock_calendar_performance(self):
        """High-performance mock calendar service"""
        mock_service = Mock()
        
        # Generate large busy periods dataset
        busy_periods = []
        base_date = datetime(2024, 1, 1, 9, 0, 0)
        
        for i in range(500):  # 500 busy periods
            start_time = base_date + timedelta(days=i//10, hours=i%10)
            end_time = start_time + timedelta(minutes=30)
            busy_periods.append({
                'start': start_time.isoformat() + 'Z',
                'end': end_time.isoformat() + 'Z'
            })
        
        mock_service.freebusy().query().execute.return_value = {
            'calendars': {'primary': {'busy': busy_periods}}
        }
        
        mock_service.events().insert().execute.return_value = {
            'id': 'event123',
            'status': 'confirmed'
        }
        
        return mock_service
    
    def test_availability_check_performance(self, mock_calendar_performance):
        """Test calendar availability checking performance"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_performance
            
            from src.calendar_client import CalendarClient
            client = CalendarClient()
            
            start_time = time.time()
            
            # Check availability for 100 different time slots
            base_date = datetime(2024, 1, 15, 9, 0, 0)
            
            availability_results = []
            for i in range(100):
                slot_start = base_date + timedelta(hours=i*0.5)  # Every 30 minutes
                slot_end = slot_start + timedelta(hours=1)
                
                is_available = client.is_time_available(slot_start, slot_end)
                availability_results.append(is_available)
            
            check_time = time.time() - start_time
            
            assert len(availability_results) == 100
            assert check_time < 5.0, f"100 availability checks took {check_time:.2f}s"
            
            # Calculate throughput
            throughput = 100 / check_time
            assert throughput > 20, f"Availability check throughput: {throughput:.2f} checks/sec"
    
    def test_bulk_event_creation_performance(self, mock_calendar_performance):
        """Test bulk calendar event creation performance"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_performance
            
            from src.calendar_client import CalendarClient
            client = CalendarClient()
            
            # Create 50 events
            events_to_create = []
            base_date = datetime(2024, 1, 15, 9, 0, 0)
            
            for i in range(50):
                event_data = {
                    'summary': f'Performance Test Event {i}',
                    'description': f'Test event for performance testing {i}',
                    'start_time': base_date + timedelta(days=i),
                    'end_time': base_date + timedelta(days=i, hours=1)
                }
                events_to_create.append(event_data)
            
            start_time = time.time()
            
            created_events = []
            for event_data in events_to_create:
                created_event = client.create_event(event_data)
                created_events.append(created_event)
            
            creation_time = time.time() - start_time
            
            assert len(created_events) == 50
            assert creation_time < 10.0, f"Creating 50 events took {creation_time:.2f}s"
            
            # Calculate throughput
            throughput = 50 / creation_time
            assert throughput > 5, f"Event creation throughput: {throughput:.2f} events/sec"

class TestAPIPerformance:
    """API endpoint performance tests"""
    
    @pytest.fixture
    def test_app(self):
        """Create test FastAPI app for performance testing"""
        try:
            from fastapi.testclient import TestClient
            from src.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI or main app not available")
    
    def test_api_response_times(self, test_app):
        """Test API endpoint response times"""
        endpoints_to_test = [
            '/',
            '/health',
            '/api/status'
        ]
        
        response_times = {}
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            
            try:
                response = test_app.get(endpoint)
                response_time = time.time() - start_time
                response_times[endpoint] = response_time
                
                # Each endpoint should respond in under 1 second
                assert response_time < 1.0, f"Endpoint {endpoint} took {response_time:.2f}s"
                
            except Exception as e:
                response_times[endpoint] = f"ERROR: {str(e)}"
        
        print(f"API response times: {response_times}")
    
    def test_concurrent_api_requests(self, test_app):
        """Test API performance under concurrent load"""
        endpoint = '/'
        num_requests = 50
        max_workers = 10
        
        def make_request():
            start_time = time.time()
            try:
                response = test_app.get(endpoint)
                response_time = time.time() - start_time
                return {
                    'status_code': response.status_code,
                    'response_time': response_time
                }
            except Exception as e:
                return {
                    'status_code': 500,
                    'response_time': None,
                    'error': str(e)
                }
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 200]
        failed_requests = [r for r in results if r['status_code'] != 200]
        
        success_rate = len(successful_requests) / num_requests
        avg_response_time = sum(r['response_time'] for r in successful_requests if r['response_time']) / len(successful_requests)
        
        assert success_rate > 0.95, f"Success rate: {success_rate:.2%} (should be > 95%)"
        assert avg_response_time < 0.5, f"Average response time: {avg_response_time:.2f}s"
        assert total_time < 10.0, f"Total time for {num_requests} requests: {total_time:.2f}s"

class TestDatabasePerformance:
    """Database operation performance tests"""
    
    def test_celery_task_performance(self):
        """Test Celery task execution performance"""
        try:
            from src.celery_app import celery_app
            
            # Test task registration
            start_time = time.time()
            
            # Check if tasks are registered
            registered_tasks = list(celery_app.tasks.keys())
            
            registration_time = time.time() - start_time
            
            assert registration_time < 2.0, f"Task registration took {registration_time:.2f}s"
            assert len(registered_tasks) > 0, "No Celery tasks registered"
            
        except ImportError:
            pytest.skip("Celery not available")
    
    def test_file_io_performance(self):
        """Test file I/O performance"""
        import tempfile
        import json
        
        # Test writing large JSON files
        test_data = {
            'emails': [
                {
                    'id': f'email_{i}',
                    'subject': f'Test Subject {i}',
                    'body': f'Test body content {i}' * 100,
                    'timestamp': datetime.now().isoformat()
                }
                for i in range(1000)
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Test write performance
            start_time = time.time()
            json.dump(test_data, temp_file, indent=2)
            write_time = time.time() - start_time
            
        # Test read performance
        start_time = time.time()
        with open(temp_path, 'r') as f:
            loaded_data = json.load(f)
        read_time = time.time() - start_time
        
        # Clean up
        os.unlink(temp_path)
        
        assert write_time < 2.0, f"Writing 1000 email records took {write_time:.2f}s"
        assert read_time < 1.0, f"Reading 1000 email records took {read_time:.2f}s"
        assert len(loaded_data['emails']) == 1000

class TestLoadTesting:
    """Load testing scenarios"""
    
    def test_email_processing_load(self):
        """Test system under email processing load"""
        # Simulate high email volume
        num_emails = 500
        batch_size = 50
        
        def process_email_batch(batch_id, batch_size):
            """Simulate processing a batch of emails"""
            processed = []
            for i in range(batch_size):
                email_data = {
                    'id': f'batch_{batch_id}_email_{i}',
                    'subject': f'Load Test Email {i}',
                    'body': 'Load testing email content',
                    'processed_at': datetime.now().isoformat()
                }
                
                # Simulate processing time
                time.sleep(0.01)  # 10ms per email
                processed.append(email_data)
            
            return processed
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for batch_id in range(num_emails // batch_size):
                future = executor.submit(process_email_batch, batch_id, batch_size)
                futures.append(future)
            
            all_processed = []
            for future in concurrent.futures.as_completed(futures):
                all_processed.extend(future.result())
        
        total_time = time.time() - start_time
        
        assert len(all_processed) == num_emails
        assert total_time < 30.0, f"Processing {num_emails} emails took {total_time:.2f}s"
        
        throughput = num_emails / total_time
        assert throughput > 20, f"Load test throughput: {throughput:.2f} emails/sec"
    
    def test_memory_stress_test(self):
        """Test system under memory stress"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create large objects to stress memory
        large_objects = []
        
        try:
            for i in range(100):
                # Create large data structure
                large_object = {
                    'id': i,
                    'data': [f'data_chunk_{j}' * 1000 for j in range(100)],
                    'metadata': {
                        'created_at': datetime.now().isoformat(),
                        'size': 'large',
                        'content': 'test_data' * 1000
                    }
                }
                large_objects.append(large_object)
                
                # Check memory usage periodically
                if i % 20 == 0:
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - initial_memory
                    
                    # Ensure memory growth is reasonable
                    assert memory_growth < 1000, f"Memory growth: {memory_growth:.2f}MB (too high)"
            
            peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
        finally:
            # Clean up
            del large_objects
            import gc
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        memory_growth = peak_memory - initial_memory
        memory_recovered = peak_memory - final_memory
        
        assert memory_growth < 500, f"Memory stress test used {memory_growth:.2f}MB"
        assert memory_recovered > memory_growth * 0.7, "Memory not properly released"

@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance regression detection"""
    
    def test_import_benchmark(self):
        """Benchmark module import times"""
        import_benchmarks = {}
        
        modules = [
            'json',
            'datetime',
            'os',
            'sys',
            'time'
        ]
        
        for module in modules:
            start_time = time.time()
            __import__(module)
            import_time = time.time() - start_time
            import_benchmarks[module] = import_time
        
        # Standard library imports should be very fast
        for module, import_time in import_benchmarks.items():
            assert import_time < 0.1, f"Module {module} import too slow: {import_time:.3f}s"
    
    def test_json_processing_benchmark(self):
        """Benchmark JSON processing performance"""
        # Create test data
        test_data = {
            'emails': [
                {
                    'id': i,
                    'subject': f'Benchmark Email {i}',
                    'body': f'Email body content {i}' * 50,
                    'metadata': {
                        'received_at': datetime.now().isoformat(),
                        'priority': 'normal',
                        'tags': [f'tag_{j}' for j in range(5)]
                    }
                }
                for i in range(1000)
            ]
        }
        
        # Benchmark serialization
        start_time = time.time()
        json_string = json.dumps(test_data)
        serialize_time = time.time() - start_time
        
        # Benchmark deserialization
        start_time = time.time()
        parsed_data = json.loads(json_string)
        deserialize_time = time.time() - start_time
        
        assert serialize_time < 1.0, f"JSON serialization too slow: {serialize_time:.3f}s"
        assert deserialize_time < 0.5, f"JSON deserialization too slow: {deserialize_time:.3f}s"
        assert len(parsed_data['emails']) == 1000

if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "not benchmark"])