"""Terraform deployment automation."""

import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

from python_terraform import Terraform, IsFlagged

from .config import Config
from .exceptions import DeploymentError


class TerraformDeployer:
    """Automate Terraform deployment for Workers and R2."""
    
    def __init__(self, config: Config, working_dir: str = "./terraform"):
        self.config = config
        self.working_dir = Path(working_dir)
        self.tf = Terraform(working_dir=str(self.working_dir))
    
    def generate_terraform_config(
        self,
        worker_script_path: Path,
    ) -> None:
        """Generate Terraform configuration files."""
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Main configuration
        main_tf = f"""
terraform {{
  required_providers {{
    cloudflare = {{
      source  = "cloudflare/cloudflare"
      version = "~> 4"
    }}
  }}
}}

provider "cloudflare" {{
  api_token = var.cloudflare_api_token
}}

variable "cloudflare_api_token" {{
  type      = string
  sensitive = true
}}

variable "cloudflare_account_id" {{
  type = string
}}

variable "cloudflare_zone_id" {{
  type = string
}}

variable "r2_bucket_name" {{
  type = string
}}

variable "worker_script_name" {{
  type = string
}}

variable "platform_domain" {{
  type = string
}}

variable "internal_api_key" {{
  type      = string
  sensitive = true
}}

# R2 Bucket
resource "cloudflare_r2_bucket" "sites" {{
  account_id = var.cloudflare_account_id
  name       = var.r2_bucket_name
  location   = "EEUR"
}}

# Worker Script
resource "cloudflare_worker_script" "site_router" {{
  account_id = var.cloudflare_account_id
  name       = var.worker_script_name
  content    = file("${{path.module}}/worker.js")

  r2_bucket_binding {{
    name        = "MY_BUCKET"
    bucket_name = cloudflare_r2_bucket.sites.name
  }}

  secret_text_binding {{
    name = "INTERNAL_API_KEY"
    text = var.internal_api_key
  }}

  plain_text_binding {{
    name = "PLATFORM_DOMAIN"
    text = var.platform_domain
  }}
}}

# Worker Route
resource "cloudflare_worker_route" "wildcard_route" {{
  zone_id     = var.cloudflare_zone_id
  pattern     = "*.{self.config.platform_domain}/*"
  script_name = cloudflare_worker_script.site_router.name
}}

# Outputs
output "r2_bucket_name" {{
  value = cloudflare_r2_bucket.sites.name
}}

output "worker_script_name" {{
  value = cloudflare_worker_script.site_router.name
}}
"""
        
        (self.working_dir / "main.tf").write_text(main_tf)
        
        # Copy worker script
        if worker_script_path.exists():
            shutil.copy(worker_script_path, self.working_dir / "worker.js")
        
        # Create tfvars
        tfvars = {
            "cloudflare_api_token": self.config.cloudflare_api_token,
            "cloudflare_account_id": self.config.cloudflare_account_id,
            "cloudflare_zone_id": self.config.cloudflare_zone_id,
            "r2_bucket_name": self.config.r2_bucket_name,
            "worker_script_name": self.config.worker_script_name,
            "platform_domain": self.config.platform_domain,
            "internal_api_key": self.config.internal_api_key or "default-key",
        }
        
        (self.working_dir / "terraform.tfvars.json").write_text(
            json.dumps(tfvars, indent=2)
        )
    
    async def deploy(
        self,
        worker_script_path: Path,
        auto_approve: bool = False,
    ) -> Dict[str, Any]:
        """Deploy infrastructure with Terraform."""
        try:
            # Generate config
            self.generate_terraform_config(worker_script_path)
            
            # Initialize
            return_code, stdout, stderr = self.tf.init(capture_output=True)
            if return_code != 0:
                raise DeploymentError(f"Terraform init failed: {stderr}")
            
            # Plan
            return_code, stdout, stderr = self.tf.plan(
                capture_output=True,
                out="tfplan",
            )
            if return_code != 0:
                raise DeploymentError(f"Terraform plan failed: {stderr}")
            
            # Apply
            if auto_approve:
                return_code, stdout, stderr = self.tf.apply(
                    "tfplan",
                    capture_output=True,
                    skip_plan=True,
                )
                if return_code != 0:
                    raise DeploymentError(f"Terraform apply failed: {stderr}")
            
            # Get outputs
            outputs = self.tf.output(json=IsFlagged)
            
            return {
                "success": True,
                "outputs": outputs,
                "stdout": stdout,
            }
        except Exception as e:
            raise DeploymentError(f"Terraform deployment failed: {e}")
    
    async def destroy(self, auto_approve: bool = False) -> Dict[str, Any]:
        """Destroy infrastructure."""
        try:
            if auto_approve:
                return_code, stdout, stderr = self.tf.destroy(
                    capture_output=True,
                    auto_approve=True,
                )
                if return_code != 0:
                    raise DeploymentError(f"Terraform destroy failed: {stderr}")
            
            return {
                "success": True,
                "stdout": stdout,
            }
        except Exception as e:
            raise DeploymentError(f"Terraform destroy failed: {e}")