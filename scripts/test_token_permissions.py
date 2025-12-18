#!/usr/bin/env python3
"""
Test Cloudflare API token permissions for various services.
"""

import asyncio
import os
from typing import Dict, List

import httpx


class CloudflareTokenTester:
    """Test Cloudflare API token permissions."""

    def __init__(self, api_token: str, account_id: str, zone_id: str = None):
        self.api_token = api_token
        self.account_id = account_id
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    async def test_basic_auth(self) -> Dict:
        """Test basic authentication."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user/tokens/verify",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_account_access(self) -> Dict:
        """Test account access."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/accounts/{self.account_id}",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_zone_access(self) -> Dict:
        """Test zone access."""
        if not self.zone_id:
            return {"success": False, "error": "No zone_id provided"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/zones/{self.zone_id}",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_r2_buckets_list(self) -> Dict:
        """Test R2 buckets listing permission."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/accounts/{self.account_id}/r2/buckets",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_r2_bucket_create(self) -> Dict:
        """Test R2 bucket creation permission."""
        async with httpx.AsyncClient() as client:
            try:
                # Try to create a test bucket (will fail if bucket exists, but tests permission)
                response = await client.post(
                    f"{self.base_url}/accounts/{self.account_id}/r2/buckets",
                    headers=self.headers,
                    json={"name": "test-permission-check"}
                )
                return {
                    "success": response.status_code in [200, 409],  # 409 = bucket exists
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code in [200, 409] else None,
                    "error": response.text if response.status_code not in [200, 409] else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_workers_list(self) -> Dict:
        """Test Workers listing permission."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/accounts/{self.account_id}/workers/scripts",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_workers_routes(self) -> Dict:
        """Test Workers routes permission."""
        if not self.zone_id:
            return {"success": False, "error": "No zone_id provided"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/zones/{self.zone_id}/workers/routes",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def test_custom_hostnames(self) -> Dict:
        """Test custom hostnames permission."""
        if not self.zone_id:
            return {"success": False, "error": "No zone_id provided"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/zones/{self.zone_id}/custom_hostnames",
                    headers=self.headers
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def run_all_tests(self) -> Dict[str, Dict]:
        """Run all permission tests."""
        tests = {
            "basic_auth": await self.test_basic_auth(),
            "account_access": await self.test_account_access(),
            "zone_access": await self.test_zone_access(),
            "r2_buckets_list": await self.test_r2_buckets_list(),
            "r2_bucket_create": await self.test_r2_bucket_create(),
            "workers_list": await self.test_workers_list(),
            "workers_routes": await self.test_workers_routes(),
            "custom_hostnames": await self.test_custom_hostnames(),
        }
        return tests


async def main():
    """Main function."""
    # Load from environment
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")

    if not api_token or not account_id:
        print("❌ Missing required environment variables:")
        print("   CLOUDFLARE_API_TOKEN")
        print("   CLOUDFLARE_ACCOUNT_ID")
        return

    print("🔍 Testing Cloudflare API token permissions...")
    print(f"Account ID: {account_id}")
    print(f"Zone ID: {zone_id or 'Not provided'}")
    print()

    tester = CloudflareTokenTester(api_token, account_id, zone_id)
    results = await tester.run_all_tests()

    # Display results
    print("📊 Test Results:")
    print("=" * 50)

    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

        if not result["success"]:
            print(f"   Status: {result.get('status_code', 'N/A')}")
            if result.get("error"):
                # Truncate long error messages
                error = result["error"]
                if len(error) > 100:
                    error = error[:100] + "..."
                print(f"   Error: {error}")
        print()

    # Summary
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)

    print("=" * 50)
    print(f"📈 Summary: {passed}/{total} tests passed")

    # Specific recommendations
    print("\n💡 Recommendations:")

    if not results["basic_auth"]["success"]:
        print("   - API token is invalid or expired")
        print("   - Regenerate token in Cloudflare dashboard")

    if not results["account_access"]["success"]:
        print("   - Token lacks account access permissions")
        print("   - Add 'Account:Read' permission to token")

    if not results["r2_buckets_list"]["success"] or not results["r2_bucket_create"]["success"]:
        print("   - Token lacks R2 permissions")
        print("   - Add 'Account:Cloudflare R2:Edit' permission to token")
        print("   - Ensure R2 is enabled for your account")

    if not results["workers_list"]["success"]:
        print("   - Token lacks Workers permissions")
        print("   - Add 'Account:Cloudflare Workers:Edit' permission to token")

    if not results["workers_routes"]["success"]:
        print("   - Token lacks Workers routes permissions")
        print("   - Add 'Zone:Cloudflare Workers Routes:Edit' permission to token")

    if not results["custom_hostnames"]["success"]:
        print("   - Token lacks custom hostnames permissions")
        print("   - Add 'Zone:Custom Hostnames:Edit' permission to token")


if __name__ == "__main__":
    asyncio.run(main())