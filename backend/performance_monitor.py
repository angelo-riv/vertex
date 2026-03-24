"""
Performance Monitoring Utility for Real-time Processing Optimization

Tracks and reports performance metrics for the ESP32 sensor data processing pipeline
to ensure sub-200ms end-to-end latency requirements are met.
"""

import time
import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional
import statistics
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Monitors performance metrics for real-time sensor data processing.
    Tracks latency, throughput, and memory usage to ensure clinical requirements are met.
    """
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        
        # Performance metrics
        self.processing_times = deque(maxlen=max_samples)
        self.websocket_broadcast_times = deque(maxlen=max_samples)
        self.database_storage_times = deque(maxlen=max_samples)
        self.end_to_end_times = deque(maxlen=max_samples)
        
        # Throughput tracking
        self.requests_per_second = deque(maxlen=60)  # Last 60 seconds
        self.last_request_time = time.time()
        self.request_count = 0
        
        # Memory usage tracking
        self.memory_usage_samples = deque(maxlen=100)
        
        # Alert thresholds
        self.latency_threshold_ms = 200  # Clinical requirement
        self.warning_threshold_ms = 150  # Warning threshold
        
    def record_processing_time(self, processing_time_ms: float):
        """Record sensor data processing time"""
        self.processing_times.append(processing_time_ms)
        
        # Check for performance issues
        if processing_time_ms > self.latency_threshold_ms:
            logger.warning(f"Processing time exceeded threshold: {processing_time_ms:.1f}ms > {self.latency_threshold_ms}ms")
        elif processing_time_ms > self.warning_threshold_ms:
            logger.info(f"Processing time approaching threshold: {processing_time_ms:.1f}ms")
    
    def record_websocket_broadcast_time(self, broadcast_time_ms: float):
        """Record WebSocket broadcast time"""
        self.websocket_broadcast_times.append(broadcast_time_ms)
    
    def record_database_storage_time(self, storage_time_ms: float):
        """Record database storage time"""
        self.database_storage_times.append(storage_time_ms)
    
    def record_end_to_end_time(self, end_to_end_time_ms: float):
        """Record complete end-to-end processing time"""
        self.end_to_end_times.append(end_to_end_time_ms)
        
        # Critical alert for end-to-end latency
        if end_to_end_time_ms > self.latency_threshold_ms:
            logger.error(f"End-to-end latency exceeded clinical requirement: {end_to_end_time_ms:.1f}ms > {self.latency_threshold_ms}ms")
    
    def record_request(self):
        """Record incoming request for throughput calculation"""
        current_time = time.time()
        self.request_count += 1
        
        # Calculate requests per second
        if current_time - self.last_request_time >= 1.0:
            self.requests_per_second.append(self.request_count)
            self.request_count = 0
            self.last_request_time = current_time
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_times": self._calculate_stats(self.processing_times, "Processing"),
            "websocket_broadcast": self._calculate_stats(self.websocket_broadcast_times, "WebSocket Broadcast"),
            "database_storage": self._calculate_stats(self.database_storage_times, "Database Storage"),
            "end_to_end": self._calculate_stats(self.end_to_end_times, "End-to-End"),
            "throughput": {
                "current_rps": self.requests_per_second[-1] if self.requests_per_second else 0,
                "avg_rps": statistics.mean(self.requests_per_second) if self.requests_per_second else 0,
                "max_rps": max(self.requests_per_second) if self.requests_per_second else 0,
                "total_samples": len(self.processing_times)
            },
            "performance_status": self._get_performance_status()
        }
        
        return stats
    
    def _calculate_stats(self, data: deque, name: str) -> Dict:
        """Calculate statistics for a data series"""
        if not data:
            return {"name": name, "samples": 0}
        
        data_list = list(data)
        return {
            "name": name,
            "samples": len(data_list),
            "mean_ms": round(statistics.mean(data_list), 2),
            "median_ms": round(statistics.median(data_list), 2),
            "p95_ms": round(self._percentile(data_list, 95), 2),
            "p99_ms": round(self._percentile(data_list, 99), 2),
            "min_ms": round(min(data_list), 2),
            "max_ms": round(max(data_list), 2),
            "std_dev": round(statistics.stdev(data_list) if len(data_list) > 1 else 0, 2)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _get_performance_status(self) -> Dict:
        """Assess overall performance status"""
        status = {
            "overall": "excellent",
            "alerts": [],
            "recommendations": []
        }
        
        # Check end-to-end latency
        if self.end_to_end_times:
            recent_e2e = list(self.end_to_end_times)[-10:]  # Last 10 samples
            avg_e2e = statistics.mean(recent_e2e)
            
            if avg_e2e > self.latency_threshold_ms:
                status["overall"] = "critical"
                status["alerts"].append(f"End-to-end latency exceeds clinical requirement: {avg_e2e:.1f}ms")
                status["recommendations"].append("Optimize critical path processing")
            elif avg_e2e > self.warning_threshold_ms:
                status["overall"] = "warning"
                status["alerts"].append(f"End-to-end latency approaching threshold: {avg_e2e:.1f}ms")
        
        # Check processing times
        if self.processing_times:
            recent_processing = list(self.processing_times)[-10:]
            avg_processing = statistics.mean(recent_processing)
            
            if avg_processing > 100:  # Processing should be much faster than total latency
                status["recommendations"].append("Optimize sensor data processing algorithms")
        
        # Check WebSocket broadcast performance
        if self.websocket_broadcast_times:
            recent_ws = list(self.websocket_broadcast_times)[-10:]
            avg_ws = statistics.mean(recent_ws)
            
            if avg_ws > 50:  # WebSocket broadcast should be very fast
                status["recommendations"].append("Optimize WebSocket broadcasting")
        
        return status
    
    def log_performance_summary(self):
        """Log a performance summary"""
        stats = self.get_performance_stats()
        
        logger.info("=== Performance Summary ===")
        logger.info(f"Overall Status: {stats['performance_status']['overall'].upper()}")
        
        if stats['end_to_end']['samples'] > 0:
            logger.info(f"End-to-End Latency: {stats['end_to_end']['mean_ms']:.1f}ms avg, "
                       f"{stats['end_to_end']['p95_ms']:.1f}ms p95, "
                       f"{stats['end_to_end']['max_ms']:.1f}ms max")
        
        if stats['throughput']['total_samples'] > 0:
            logger.info(f"Throughput: {stats['throughput']['avg_rps']:.1f} requests/sec avg, "
                       f"{stats['throughput']['max_rps']} max")
        
        # Log alerts
        for alert in stats['performance_status']['alerts']:
            logger.warning(f"ALERT: {alert}")
        
        # Log recommendations
        for rec in stats['performance_status']['recommendations']:
            logger.info(f"RECOMMENDATION: {rec}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def track_performance(func):
    """Decorator to track function performance"""
    import functools

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        performance_monitor.record_request()
        
        try:
            result = await func(*args, **kwargs)
            processing_time = (time.time() - start_time) * 1000
            performance_monitor.record_processing_time(processing_time)
            return result
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            performance_monitor.record_processing_time(processing_time)
            raise e
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        performance_monitor.record_request()
        
        try:
            result = func(*args, **kwargs)
            processing_time = (time.time() - start_time) * 1000
            performance_monitor.record_processing_time(processing_time)
            return result
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            performance_monitor.record_processing_time(processing_time)
            raise e
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper