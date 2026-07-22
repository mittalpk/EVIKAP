import asyncio
import httpx
import time
import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

async def benchmark_knowledge_query(client, query):
    print(f"Benchmarking Knowledge API (Layer 2) with query: {query}")
    start = time.time()
    try:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/knowledge/query",
            json={"query": query, "target_systems": ["confluence", "code_repos"]},
            timeout=120.0
        )
        duration = time.time() - start
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Duration: {duration:.2f}s")
            print(f"Execution time (server): {data.get('execution_time_ms')}ms")
            print(f"Facts found: {len(data.get('facts', []))}")
        else:
            print(f"Failed! Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

async def benchmark_agent_query(client, query):
    print(f"\nBenchmarking Agent API (Layer 3) with query: {query}")
    start = time.time()
    try:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/agent/run",
            json={"task": query, "max_iterations": 5},
            timeout=120.0
        )
        duration = time.time() - start
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Duration: {duration:.2f}s")
            print(f"Steps: {data.get('steps', 0)}")
            print(f"Answer: {data.get('answer', '')[:100]}...")
        else:
            print(f"Failed! Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    test_query = "If we change the VigilRAGUser Pydantic model in vigilrag-auth, which services in our GitHub ecosystem will be affected? Trace all dependencies"
    
    async with httpx.AsyncClient() as client:
        # 1. Warm-up / Simple query
        await benchmark_knowledge_query(client, "What is vigilrag-auth?")
        
        # 2. Complex query (Knowledge Layer)
        await benchmark_knowledge_query(client, test_query)
        
        # 3. Complex query (Agent Layer)
        await benchmark_agent_query(client, test_query)

if __name__ == "__main__":
    asyncio.run(main())
