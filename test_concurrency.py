#!/usr/bin/env python3
"""
Load testing script to validate concurrency improvements.
Run this to test if the server can handle the target concurrent users.
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "your-test-token-here"  # Replace with actual token

async def make_request(session: aiohttp.ClientSession, endpoint: str, method: str = "GET", json_data: Dict = None) -> Dict[str, Any]:
    """Make an async HTTP request and measure response time."""
    start_time = time.time()
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"} if TEST_TOKEN != "your-test-token-here" else {}
    
    try:
        async with session.request(method, f"{BASE_URL}{endpoint}", json=json_data, headers=headers) as response:
            data = await response.json()
            elapsed = time.time() - start_time
            return {
                "success": response.status == 200,
                "status": response.status,
                "time": elapsed,
                "data": data
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "status": 0,
            "time": elapsed,
            "error": str(e)
        }

async def test_light_operations(num_concurrent: int = 100):
    """Test light operations (reads, health checks)."""
    print(f"\n📊 Testing {num_concurrent} concurrent light operations...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        endpoints = ["/healthz", "/health", "/version", "/metrics"]
        
        for i in range(num_concurrent):
            endpoint = endpoints[i % len(endpoints)]
            tasks.append(make_request(session, endpoint))
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        
        successful = sum(1 for r in results if r["success"])
        response_times = [r["time"] for r in results if r["success"]]
        
        print(f"✅ Successful: {successful}/{num_concurrent}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        if response_times:
            print(f"📈 Avg response: {statistics.mean(response_times):.3f}s")
            print(f"📊 P95 response: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
            print(f"🚀 Throughput: {successful/total_time:.1f} req/s")

async def test_heavy_operations(num_concurrent: int = 20):
    """Test heavy operations (simulated chapter generation)."""
    print(f"\n🔥 Testing {num_concurrent} concurrent heavy operations...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Simulate chapter generation requests
        for i in range(num_concurrent):
            # Using health endpoint as a placeholder - replace with actual generation endpoint
            tasks.append(make_request(session, "/readyz"))
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        
        successful = sum(1 for r in results if r["success"])
        response_times = [r["time"] for r in results if r["success"]]
        
        print(f"✅ Successful: {successful}/{num_concurrent}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        if response_times:
            print(f"📈 Avg response: {statistics.mean(response_times):.3f}s")
            print(f"🚀 Throughput: {successful/total_time:.1f} req/s")

async def test_mixed_load(light_users: int = 80, heavy_users: int = 20):
    """Test mixed load scenario."""
    print(f"\n🎯 Testing mixed load: {light_users} light + {heavy_users} heavy operations...")
    
    async with aiohttp.ClientSession() as session:
        light_tasks = []
        heavy_tasks = []
        
        # Light operations
        endpoints = ["/healthz", "/health", "/version", "/metrics"]
        for i in range(light_users):
            endpoint = endpoints[i % len(endpoints)]
            light_tasks.append(make_request(session, endpoint))
        
        # Heavy operations
        for i in range(heavy_users):
            heavy_tasks.append(make_request(session, "/readyz"))
        
        start = time.time()
        all_tasks = light_tasks + heavy_tasks
        results = await asyncio.gather(*all_tasks)
        total_time = time.time() - start
        
        light_results = results[:light_users]
        heavy_results = results[light_users:]
        
        light_successful = sum(1 for r in light_results if r["success"])
        heavy_successful = sum(1 for r in heavy_results if r["success"])
        
        print(f"✅ Light ops: {light_successful}/{light_users} successful")
        print(f"✅ Heavy ops: {heavy_successful}/{heavy_users} successful")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"🚀 Overall throughput: {(light_successful + heavy_successful)/total_time:.1f} req/s")

async def main():
    print("=" * 60)
    print("🧪 BOOKOLOGY CONCURRENCY TEST SUITE")
    print("=" * 60)
    
    # Test increasing loads
    await test_light_operations(50)
    await asyncio.sleep(2)
    
    await test_light_operations(150)
    await asyncio.sleep(2)
    
    await test_heavy_operations(10)
    await asyncio.sleep(2)
    
    await test_heavy_operations(20)
    await asyncio.sleep(2)
    
    await test_mixed_load(80, 20)
    
    print("\n" + "=" * 60)
    print("✅ CONCURRENCY TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

