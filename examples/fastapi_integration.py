"""FastAPI integration example."""

from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from cloudflare_saas import (
    CloudflareSaaSPlatform,
    Config,
    DomainStatus,
    VerificationMethod,
)


# Initialize platform
config = Config.from_env()
platform = CloudflareSaaSPlatform(config)

app = FastAPI(title="Cloudflare SaaS Platform API")


# Request/Response models
class CreateTenantRequest(BaseModel):
    name: str
    slug: str
    owner_id: Optional[str] = None


class CreateTenantResponse(BaseModel):
    tenant_id: str
    subdomain: str
    name: str


class AddDomainRequest(BaseModel):
    domain: str
    verification_method: VerificationMethod = VerificationMethod.HTTP


class DomainStatusResponse(BaseModel):
    domain: str
    status: DomainStatus
    cname_target: Optional[str]
    ssl_status: Optional[str]
    error_message: Optional[str]


# Endpoints
@app.post("/v1/tenants", response_model=CreateTenantResponse)
async def create_tenant(req: CreateTenantRequest):
    """Create a new tenant."""
    try:
        tenant = await platform.create_tenant(
            name=req.name,
            slug=req.slug,
            owner_id=req.owner_id,
        )
        return CreateTenantResponse(
            tenant_id=tenant.tenant_id,
            subdomain=tenant.subdomain,
            name=tenant.name,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get tenant details."""
    try:
        tenant = await platform.get_tenant(tenant_id)
        return tenant.dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/v1/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Delete tenant and all resources."""
    try:
        await platform.delete_tenant(tenant_id)
        return {"message": "Tenant deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/tenants/{tenant_id}/domains")
async def add_custom_domain(
    tenant_id: str,
    req: AddDomainRequest,
    background_tasks: BackgroundTasks,
):
    """Add custom domain to tenant."""
    try:
        instructions = await platform.add_custom_domain(
            tenant_id,
            req.domain,
            req.verification_method,
        )
        return instructions.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/domains/{domain}", response_model=DomainStatusResponse)
async def get_domain_status(domain: str):
    """Get custom domain status."""
    try:
        domain_obj = await platform.get_domain_status(domain)
        return DomainStatusResponse(
            domain=domain_obj.domain,
            status=domain_obj.status,
            cname_target=domain_obj.cname_target,
            ssl_status=domain_obj.ssl_status,
            error_message=domain_obj.error_message,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/v1/domains/{domain}")
async def remove_domain(domain: str):
    """Remove custom domain."""
    try:
        await platform.remove_custom_domain(domain)
        return {"message": "Domain removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/tenants/{tenant_id}/domains")
async def list_tenant_domains(tenant_id: str):
    """List all domains for tenant."""
    try:
        domains = await platform.list_tenant_domains(tenant_id)
        return [d.dict() for d in domains]
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/v1/tenants/{tenant_id}/deployment-status")
async def get_deployment_status(tenant_id: str):
    """Get deployment status."""
    try:
        status = await platform.get_deployment_status(tenant_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/internal/resolve")
async def resolve_tenant(host: str):
    """
    Internal endpoint for Worker to resolve tenant from hostname.
    Should be protected with API key in production.
    """
    tenant_id = await platform.resolve_tenant_from_host(host)
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"tenant_id": tenant_id}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)