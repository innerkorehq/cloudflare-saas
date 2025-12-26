#!/usr/bin/env python3
"""
Create Cloudflare API Token using Global API Key.

This script creates a User API Token with all required permissions
for the Cloudflare SaaS platform using your Global API Key.

Usage:
    python create_token_with_global_key.py \\
        --email your@email.com \\
        --global-key your_global_api_key \\
        --account-id your_account_id \\
        --zone-id your_zone_id \\
        --name "Token Name"

Example:
    python create_token_with_global_key.py \\
        --email admin@example.com \\
        --global-key c2547eb745079dac9320b638f5e225cf483cc5cfdda41 \\
        --account-id 6451353ea5a8407bab6162abc42f5338 \\
        --zone-id 2cf1f02313c4ef76af3d62eb78bb906e \\
        --name "GETAIPAGE SaaS Token"
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Optional

import httpx


class CloudflareTokenCreatorWithGlobalKey:
    """Create Cloudflare API tokens using Global API Key."""

    def __init__(self, email: str, global_key: str):
        self.email = email
        self.global_key = global_key
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": global_key,
            "Content-Type": "application/json",
        }

    async def verify_credentials(self) -> Dict:
        """Verify that the Global API Key works."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user",
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

    async def get_permission_groups(self) -> Dict:
        """Fetch available permission groups from Cloudflare."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user/tokens/permission_groups",
                    headers=self.headers
                )

                if response.status_code == 200:
                    data = response.json()
                    # Create a mapping of permission names to IDs
                    permissions = {}
                    for perm in data["result"]:
                        permissions[perm["name"]] = perm["id"]

                    return {
                        "success": True,
                        "permissions": permissions,
                        "all_permissions": data["result"]
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.json() if response.content else response.text
                    }

            except Exception as e:
                return {"success": False, "error": str(e)}

    def _build_token_policies(
        self,
        account_id: str,
        zone_id: str,
        permission_map: Dict[str, str]
    ) -> List[Dict]:
        """Build token policies with required permissions."""
        
        # Required Account-level permissions
        required_account_permissions = [
            "Account Settings Read",        # Read account info
            "Workers R2 Storage Write",     # R2 bucket management
            "Workers Scripts Read",         # List Worker scripts
            "Workers Scripts Write",        # Deploy Worker scripts
            "Workers Routes Write",         # Configure Worker routes
            "D1 Read",                      # Query D1 databases
            "D1 Write",                     # Modify D1 databases
        ]

        # Required Zone-level permissions
        required_zone_permissions = [
            "Zone Read",                    # Read zone configuration
            "SSL and Certificates Read",    # Read custom hostnames
            "SSL and Certificates Write",   # Manage custom hostnames
        ]

        policies = []
        
        print("\n🔍 Mapping permissions to IDs...")

        # Build account permissions policy
        account_perm_ids = []
        for perm_name in required_account_permissions:
            if perm_name in permission_map:
                account_perm_ids.append({"id": permission_map[perm_name]})
                print(f"   ✅ Account: {perm_name}")
            else:
                print(f"   ⚠️  Account: Permission '{perm_name}' not found")

        if account_perm_ids:
            policies.append({
                "effect": "allow",
                "resources": {
                    f"com.cloudflare.api.account.{account_id}": "*"
                },
                "permission_groups": account_perm_ids
            })

        # Build zone permissions policy
        zone_perm_ids = []
        for perm_name in required_zone_permissions:
            if perm_name in permission_map:
                zone_perm_ids.append({"id": permission_map[perm_name]})
                print(f"   ✅ Zone: {perm_name}")
            else:
                print(f"   ⚠️  Zone: Permission '{perm_name}' not found")

        if zone_perm_ids:
            policies.append({
                "effect": "allow",
                "resources": {
                    f"com.cloudflare.api.account.zone.{zone_id}": "*"
                },
                "permission_groups": zone_perm_ids
            })

        return policies

    async def create_token(
        self,
        account_id: str,
        zone_id: str,
        token_name: str,
        ttl_seconds: Optional[int] = None
    ) -> Dict:
        """Create a new API token with required permissions."""
        print("🔍 Fetching available permission groups...")
        perm_result = await self.get_permission_groups()

        if not perm_result["success"]:
            return {
                "success": False,
                "error": f"Failed to fetch permission groups: {perm_result.get('error', 'Unknown error')}"
            }

        permission_map = perm_result["permissions"]
        print(f"✅ Found {len(permission_map)} permission groups")

        # Print available permissions for debugging
        print("\n📋 Available Account Permissions:")
        for name, perm_id in sorted(permission_map.items()):
            if any(keyword in name.lower() for keyword in ['account', 'r2', 'worker', 'd1']):
                print(f"   - {name}")

        print("\n📋 Available Zone Permissions:")
        for name, perm_id in sorted(permission_map.items()):
            if any(keyword in name.lower() for keyword in ['zone', 'dns', 'ssl', 'hostname']):
                print(f"   - {name}")

        policies = self._build_token_policies(account_id, zone_id, permission_map)

        if not policies:
            return {
                "success": False,
                "error": "No valid permissions found to create token"
            }

        print(f"\n🔐 Creating token with {len(policies)} policy groups...")

        token_data = {
            "name": token_name,
            "policies": policies,
        }

        # Add TTL if specified
        if ttl_seconds:
            from datetime import datetime, timedelta
            expires_on = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            token_data["expires_on"] = expires_on.isoformat() + "Z"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/user/tokens",
                    headers=self.headers,
                    json=token_data
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "token": data["result"]["value"],
                        "id": data["result"]["id"],
                        "name": data["result"]["name"],
                        "status": data["result"]["status"],
                        "expires_on": data["result"].get("expires_on"),
                        "policies": data["result"]["policies"]
                    }
                else:
                    error_data = response.json() if response.content else response.text
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": error_data
                    }

            except Exception as e:
                return {"success": False, "error": str(e)}

    async def list_tokens(self) -> Dict:
        """List existing API tokens."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/user/tokens",
                    headers=self.headers
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "tokens": [
                            {
                                "id": token["id"],
                                "name": token["name"],
                                "status": token["status"],
                                "expires_on": token.get("expires_on"),
                                "modified_on": token["modified_on"]
                            }
                            for token in data["result"]
                        ]
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.json() if response.content else response.text
                    }

            except Exception as e:
                return {"success": False, "error": str(e)}


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create Cloudflare API token using Global API Key"
    )
    parser.add_argument(
        "--email",
        help="Cloudflare account email (can also use CLOUDFLARE_EMAIL env var)"
    )
    parser.add_argument(
        "--global-key",
        help="Cloudflare Global API Key (can also use CLOUDFLARE_GLOBAL_KEY env var)"
    )
    parser.add_argument(
        "--account-id",
        help="Cloudflare Account ID (can also use CLOUDFLARE_ACCOUNT_ID env var)"
    )
    parser.add_argument(
        "--zone-id",
        help="Cloudflare Zone ID (can also use CLOUDFLARE_ZONE_ID env var)"
    )
    parser.add_argument(
        "--name",
        default="SaaS Platform Token",
        help="Name for the API token"
    )
    parser.add_argument(
        "--ttl-days",
        type=int,
        help="Token expiration in days (optional, recommended for security)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing tokens instead of creating new one"
    )
    parser.add_argument(
        "--list-permissions",
        action="store_true",
        help="List all available permission groups"
    )

    args = parser.parse_args()

    # Get credentials from args or environment
    email = args.email or os.getenv("CLOUDFLARE_EMAIL")
    global_key = args.global_key or os.getenv("CLOUDFLARE_GLOBAL_KEY")
    account_id = args.account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
    zone_id = args.zone_id or os.getenv("CLOUDFLARE_ZONE_ID")

    if not email or not global_key:
        print("❌ Error: Email and Global API Key are required")
        print("\nProvide via arguments:")
        print("  --email your@email.com --global-key your_global_api_key")
        print("\nOr set environment variables:")
        print("  CLOUDFLARE_EMAIL=your@email.com")
        print("  CLOUDFLARE_GLOBAL_KEY=your_global_api_key")
        print("\n⚠️  Where to find Global API Key:")
        print("  https://dash.cloudflare.com/profile/api-tokens")
        print("  → View Global API Key (requires password confirmation)")
        sys.exit(1)

    creator = CloudflareTokenCreatorWithGlobalKey(email, global_key)

    # Verify credentials first
    print("🔐 Verifying Global API Key credentials...")
    verify_result = await creator.verify_credentials()
    
    if not verify_result["success"]:
        print(f"❌ Failed to verify credentials: {verify_result.get('error', 'Unknown error')}")
        print("\n💡 Troubleshooting:")
        print("1. Check that your email is correct")
        print("2. Verify your Global API Key is valid")
        print("3. Get your Global API Key from: https://dash.cloudflare.com/profile/api-tokens")
        sys.exit(1)

    user_data = verify_result["data"]["result"]
    print(f"✅ Credentials verified for: {user_data.get('email', 'N/A')}")
    print()

    if args.list_permissions:
        print("📋 Listing all available permission groups...")
        result = await creator.get_permission_groups()

        if result["success"]:
            permissions = result["all_permissions"]
            print(f"Found {len(permissions)} permission groups:")
            print()

            # Group by scope
            account_perms = [p for p in permissions if 'Account' in p['name']]
            zone_perms = [p for p in permissions if 'Zone' in p['name']]
            other_perms = [p for p in permissions if p not in account_perms and p not in zone_perms]

            print("Account Permissions:")
            for p in account_perms:
                print(f"  - {p['name']} (ID: {p['id']})")

            print("\nZone Permissions:")
            for p in zone_perms:
                print(f"  - {p['name']} (ID: {p['id']})")

            print("\nOther Permissions:")
            for p in other_perms:
                print(f"  - {p['name']} (ID: {p['id']})")
        else:
            print(f"❌ Failed to list permissions: {result.get('error', 'Unknown error')}")

    elif args.list:
        print("📋 Listing existing API tokens...")
        result = await creator.list_tokens()

        if result["success"]:
            tokens = result["tokens"]
            if not tokens:
                print("No API tokens found.")
            else:
                print(f"Found {len(tokens)} tokens:")
                for token in tokens:
                    status = "✅" if token['status'] == 'active' else "❌"
                    print(f"  {status} {token['name']}")
                    print(f"     ID: {token['id']}")
                    print(f"     Status: {token['status']}")
                    if token.get('expires_on'):
                        print(f"     Expires: {token['expires_on']}")
                    print()
        else:
            print(f"❌ Failed to list tokens: {result.get('error', 'Unknown error')}")

    else:
        # Token creation requires account and zone IDs
        if not account_id or not zone_id:
            print("❌ Error: --account-id and --zone-id are required for token creation")
            print("\nProvide via arguments:")
            print("  --account-id your_account_id --zone-id your_zone_id")
            print("\nOr set environment variables:")
            print("  CLOUDFLARE_ACCOUNT_ID=your_account_id")
            print("  CLOUDFLARE_ZONE_ID=your_zone_id")
            sys.exit(1)

        print("🔐 Creating Cloudflare API Token for SaaS Platform...")
        print(f"Account ID: {account_id}")
        print(f"Zone ID: {zone_id}")
        print(f"Token Name: {args.name}")
        print()

        ttl_seconds = args.ttl_days * 86400 if args.ttl_days else None
        
        result = await creator.create_token(
            account_id=account_id,
            zone_id=zone_id,
            token_name=args.name,
            ttl_seconds=ttl_seconds
        )

        if result["success"]:
            print("\n✅ Token created successfully!")
            print(f"Token ID: {result['id']}")
            print(f"Token Name: {result['name']}")
            print(f"Token Status: {result['status']}")
            if result.get('expires_on'):
                print(f"Expires On: {result['expires_on']}")
            print()
            print("🔑 IMPORTANT: Save this token value - it will only be shown once!")
            print("=" * 70)
            print(f"Token Value: {result['token']}")
            print("=" * 70)
            print()
            print("💡 Update your .env file:")
            print(f"CLOUDFLARE_API_TOKEN={result['token']}")
            print()
            print("🧪 Test the token:")
            print("python test_token_permissions.py")
            print()
            print("📋 Token Policies:")
            for i, policy in enumerate(result['policies'], 1):
                print(f"\nPolicy {i}:")
                print(f"  Effect: {policy['effect']}")
                print(f"  Resources: {', '.join(policy['resources'].keys())}")
                print(f"  Permissions: {len(policy['permission_groups'])} permission groups")
        else:
            print(f"\n❌ Failed to create token")
            print(f"Error: {json.dumps(result.get('error', 'Unknown error'), indent=2)}")
            print()
            print("💡 Troubleshooting:")
            print("1. Verify your account ID and zone ID are correct")
            print("2. Check that your Global API Key has not expired")
            print("3. Try running with --list-permissions to see available permissions")


if __name__ == "__main__":
    asyncio.run(main())
