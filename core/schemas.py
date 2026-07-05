from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ScanMode(str, Enum):
    PASSIVE = "passive"
    AGGRESSIVE = "aggressive"


class SeverityLevel(str, Enum):
    INFO = "Info"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Finding(BaseModel):
    target: str = Field(description="The specific subdomain or IP being analyzed")
    issue: str = Field(description="The identified security issue or observation")
    severity: str = Field(description="Severity level: Info, Low, Medium, High, Critical")
    description: str = Field(description="Detailed technical explanation of the finding")
    suggested_payload: Optional[str] = Field(default=None, description="A sample test payload or exploit methodology")
    remediation: str = Field(description="Step-by-step instructions to fix the issue")
    tool_source: Optional[str] = Field(default=None, description="The tool that detected this finding")


class SecurityReport(BaseModel):
    summary: str = Field(description="High-level executive summary of the security posture")
    attack_surface_stats: str = Field(description="Summary of discovered subdomains and services")
    findings: List[Finding] = Field(description="List of specific technical security findings")
    overall_risk_score: int = Field(description="Overall risk score from 1 to 10", ge=1, le=10)
    next_steps: List[str] = Field(description="Recommended actions for further deep testing")
    scan_mode: Optional[str] = Field(default="passive", description="The scan mode used")
    scan_target: Optional[str] = Field(default=None, description="The primary target of the scan")


class PluginResult(BaseModel):
    plugin_name: str
    target: str
    success: bool
    output: str
    error: Optional[str] = None
    findings_count: int = 0
