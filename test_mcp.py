#!/usr/bin/env python3
"""Test script for MCP Server"""

import asyncio
import json
import httpx

async def test_health():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8089/health")
        print(f"Health Check: {response.json()}")
        return response.status_code == 200

async def test_sse_connection():
    """Test SSE endpoint"""
    async with httpx.AsyncClient() as client:
        # Try to connect to SSE endpoint
        try:
            response = await client.get(
                "http://localhost:8089/sse",
                headers={"Accept": "text/event-stream"},
                timeout=5.0
            )
            print(f"SSE Connection Status: {response.status_code}")
            
            # Should get auth_required response
            if response.status_code == 200:
                print("SSE endpoint accessible")
                return True
        except Exception as e:
            print(f"SSE Connection Error: {e}")
    return False

async def main():
    """Run tests"""
    print("Testing MCP Server...")
    print("-" * 40)
    
    # Test health endpoint
    health_ok = await test_health()
    print(f"✓ Health endpoint: {'OK' if health_ok else 'FAILED'}")
    
    # Test SSE endpoint
    sse_ok = await test_sse_connection()
    print(f"✓ SSE endpoint: {'OK' if sse_ok else 'FAILED'}")
    
    print("-" * 40)
    if health_ok and sse_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())