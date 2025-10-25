#!/usr/bin/env python3
"""
PRISM パフォーマンステストスクリプト
"""
import asyncio
import time
import aiohttp
import json
from typing import List, Dict, Any
import statistics

class PerformanceTester:
    """パフォーマンステストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8060", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        } if api_key else {"Content-Type": "application/json"}
    
    async def test_health_endpoint(self, iterations: int = 100) -> Dict[str, Any]:
        """ヘルスチェックエンドポイントのテスト"""
        print(f"🏥 Testing health endpoint ({iterations} iterations)...")
        
        async with aiohttp.ClientSession() as session:
            times = []
            errors = 0
            
            for i in range(iterations):
                start_time = time.time()
                try:
                    async with session.get(f"{self.base_url}/healthz") as response:
                        if response.status == 200:
                            await response.text()
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in iteration {i}: {e}")
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            return {
                "endpoint": "/healthz",
                "iterations": iterations,
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "errors": errors,
                "success_rate": (iterations - errors) / iterations * 100
            }
    
    async def test_metrics_endpoint(self, iterations: int = 50) -> Dict[str, Any]:
        """メトリクスエンドポイントのテスト"""
        print(f"📊 Testing metrics endpoint ({iterations} iterations)...")
        
        async with aiohttp.ClientSession() as session:
            times = []
            errors = 0
            
            for i in range(iterations):
                start_time = time.time()
                try:
                    async with session.get(f"{self.base_url}/metrics") as response:
                        if response.status == 200:
                            await response.text()
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in iteration {i}: {e}")
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            return {
                "endpoint": "/metrics",
                "iterations": iterations,
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "errors": errors,
                "success_rate": (iterations - errors) / iterations * 100
            }
    
    async def test_async_classification(self, iterations: int = 10) -> Dict[str, Any]:
        """非同期分類エンドポイントのテスト"""
        print(f"⚡ Testing async classification endpoint ({iterations} iterations)...")
        
        # テストデータ
        test_items = [
            {
                "id": f"test_{i}",
                "title": f"Test Item {i}",
                "content": f"This is test content for item {i}"
            }
            for i in range(5)
        ]
        
        async with aiohttp.ClientSession() as session:
            times = []
            errors = 0
            
            for i in range(iterations):
                start_time = time.time()
                try:
                    payload = {
                        "items": test_items,
                        "database_id": "test_database_id",
                        "batch_size": 5
                    }
                    
                    async with session.post(
                        f"{self.base_url}/async/classify/batch",
                        json=payload,
                        headers=self.headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            # タスクの完了を待機
                            task_id = result.get("task_id")
                            if task_id:
                                await self._wait_for_task_completion(session, task_id)
                        else:
                            errors += 1
                            print(f"Error in iteration {i}: {response.status}")
                
                except Exception as e:
                    errors += 1
                    print(f"Error in iteration {i}: {e}")
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            return {
                "endpoint": "/async/classify/batch",
                "iterations": iterations,
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "errors": errors,
                "success_rate": (iterations - errors) / iterations * 100
            }
    
    async def _wait_for_task_completion(self, session: aiohttp.ClientSession, task_id: str, timeout: int = 30):
        """タスクの完了を待機"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with session.get(
                    f"{self.base_url}/async/task/{task_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get("status")
                        
                        if status in ["completed", "failed", "cancelled"]:
                            return result
                        
                        await asyncio.sleep(0.5)
                    else:
                        break
            except Exception:
                break
        
        return None
    
    async def test_concurrent_requests(self, endpoint: str, concurrent: int = 10, iterations: int = 100) -> Dict[str, Any]:
        """同時リクエストのテスト"""
        print(f"🔄 Testing concurrent requests ({concurrent} concurrent, {iterations} total)...")
        
        async def make_request(session: aiohttp.ClientSession):
            start_time = time.time()
            try:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    await response.text()
                    return time.time() - start_time, response.status == 200
            except Exception:
                return time.time() - start_time, False
        
        async with aiohttp.ClientSession() as session:
            times = []
            successes = 0
            
            # セマフォで同時リクエスト数を制限
            semaphore = asyncio.Semaphore(concurrent)
            
            async def limited_request():
                async with semaphore:
                    return await make_request(session)
            
            tasks = [limited_request() for _ in range(iterations)]
            results = await asyncio.gather(*tasks)
            
            for time_taken, success in results:
                times.append(time_taken)
                if success:
                    successes += 1
            
            return {
                "endpoint": endpoint,
                "concurrent": concurrent,
                "iterations": iterations,
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "successes": successes,
                "success_rate": successes / iterations * 100
            }
    
    def print_results(self, results: List[Dict[str, Any]]):
        """結果を表示"""
        print("\n" + "="*80)
        print("📈 PERFORMANCE TEST RESULTS")
        print("="*80)
        
        for result in results:
            print(f"\n🔍 {result['endpoint']}")
            print(f"   Iterations: {result['iterations']}")
            print(f"   Average Time: {result['avg_time']:.4f}s")
            print(f"   Min Time: {result['min_time']:.4f}s")
            print(f"   Max Time: {result['max_time']:.4f}s")
            print(f"   Median Time: {result['median_time']:.4f}s")
            
            if 'success_rate' in result:
                print(f"   Success Rate: {result['success_rate']:.1f}%")
            
            if 'errors' in result:
                print(f"   Errors: {result['errors']}")
            
            if 'concurrent' in result:
                print(f"   Concurrent Requests: {result['concurrent']}")

async def main():
    """メイン関数"""
    print("🚀 PRISM Performance Test")
    print("="*50)
    
    # APIキーを設定（必要に応じて）
    api_key = "your-api-key-here"  # 実際のAPIキーに置き換え
    
    tester = PerformanceTester(api_key=api_key)
    
    # テストを実行
    results = []
    
    # ヘルスチェックテスト
    health_results = await tester.test_health_endpoint(100)
    results.append(health_results)
    
    # メトリクステスト
    metrics_results = await tester.test_metrics_endpoint(50)
    results.append(metrics_results)
    
    # 同時リクエストテスト
    concurrent_results = await tester.test_concurrent_requests("/healthz", 10, 100)
    results.append(concurrent_results)
    
    # 結果を表示
    tester.print_results(results)
    
    print("\n✅ Performance test completed!")

if __name__ == "__main__":
    asyncio.run(main())
