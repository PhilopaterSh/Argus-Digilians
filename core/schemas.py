from pydantic import BaseModel, Field
from typing import List, Optional

class Finding(BaseModel):
    target: str = Field(description="The specific subdomain or IP being analyzed")
    issue: str = Field(description="The identified security issue or observation")
    severity: str = Field(description="Severity level: Low, Medium, High, Critical")
    description: str = Field(description="Detailed technical explanation of the finding")
    suggested_payload: Optional[str] = Field(description="A sample test payload or exploit methodology (e.g., from PayloadsAllTheThings)")
    remediation: str = Field(description="Step-by-step instructions to fix the issue")

class SecurityReport(BaseModel):
    summary: str = Field(description="High-level executive summary of the security posture")
    attack_surface_stats: str = Field(description="Summary of discovered subdomains and services")
    findings: List[Finding] = Field(description="List of specific technical security findings")
    overall_risk_score: int = Field(description="Overall risk score from 1 to 10", ge=1, le=10)
    next_steps: List[str] = Field(description="Recommended actions for further deep testing")
