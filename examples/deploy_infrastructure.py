"""Deploy Cloudflare infrastructure with Terraform."""

import asyncio
import sys
from pathlib import Path
from cloudflare_saas import Config
from cloudflare_saas.terraform_deployer import TerraformDeployer


async def main():
    """Deploy infrastructure."""
    print("Loading configuration...")
    config = Config.from_env()
    
    # Path to worker script
    worker_script = Path(__file__).parent.parent / "cloudflare_saas" / "worker_template.js"
    
    if not worker_script.exists():
        print(f"✗ Worker script not found at {worker_script}")
        return
    
    print("Initializing Terraform deployer...")
    deployer = TerraformDeployer(config, working_dir="./terraform_generated")
    
    print("\nGenerating Terraform configuration...")
    deployer.generate_terraform_config(worker_script)
    print("✓ Configuration generated")
    
    print("\nDeploying infrastructure...")
    print("This will:")
    print("  - Create R2 bucket")
    print("  - Deploy Worker script")
    print("  - Configure Worker routes")
    
    # Skip confirmation in non-interactive mode
    import os
    if os.environ.get('CI') or not sys.stdout.isatty():
        print("\nRunning in non-interactive mode, proceeding automatically...")
        confirm = "yes"
    else:
        confirm = input("\nProceed with deployment? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("Deployment cancelled")
        return
    
    try:
        result = await deployer.deploy(
            worker_script_path=worker_script,
            auto_approve=True,
        )
        
        if result["success"]:
            print("\n✓ Infrastructure deployed successfully!")
            print("\nOutputs:")
            for key, value in result.get("outputs", {}).items():
                print(f"  {key}: {value}")
        else:
            print("\n✗ Deployment failed")
    
    except Exception as e:
        print(f"\n✗ Deployment error: {e}")
        raise


async def destroy_infrastructure():
    """Destroy infrastructure."""
    print("Loading configuration...")
    config = Config.from_env()
    
    deployer = TerraformDeployer(config, working_dir="./terraform_generated")
    
    print("\n⚠️  WARNING: This will destroy all infrastructure!")
    print("  - R2 bucket (and all objects)")
    print("  - Worker script")
    print("  - Worker routes")
    
    confirm = input("\nType 'DESTROY' to confirm: ")
    
    if confirm != "DESTROY":
        print("Destruction cancelled")
        return
    
    try:
        result = await deployer.destroy(auto_approve=True)
        
        if result["success"]:
            print("\n✓ Infrastructure destroyed")
        else:
            print("\n✗ Destruction failed")
    
    except Exception as e:
        print(f"\n✗ Destruction error: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "destroy":
        asyncio.run(destroy_infrastructure())
    else:
        asyncio.run(main())