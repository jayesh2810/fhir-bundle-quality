from pydantic import BaseModel
 
 
class ResourceInstanceScore(BaseModel):
    resource_id: str
    score: float           # 0.0–1.0
    missing_fields: list[str]
 
 
class ResourceTypeCompleteness(BaseModel):
    resource_type: str
    count: int
    avg_score: float
    instances: list[ResourceInstanceScore]
 
 
class CompletenessReport(BaseModel):
    overall_score: float
    by_resource_type: list[ResourceTypeCompleteness]
 
 
class CodeCoverageInstanceScore(BaseModel):
    resource_id: str
    score: float           # 0.0 or 1.0
 
 
class ResourceTypeCoverage(BaseModel):
    resource_type: str
    count: int
    avg_score: float
    instances: list[CodeCoverageInstanceScore]
 
 
class CodeCoverageReport(BaseModel):
    overall_score: float
    by_resource_type: list[ResourceTypeCoverage]


class TemporalViolation(BaseModel):
    resource_id: str
    violation_type: str
    conflicting_dates: dict[str, str]


class TemporalInstanceScore(BaseModel):
    resource_id: str
    score: float           # 0.0 or 1.0
    violations: list[TemporalViolation]


class ResourceTypeTemporal(BaseModel):
    resource_type: str
    count: int
    avg_score: float
    instances: list[TemporalInstanceScore]


class TemporalConsistencyReport(BaseModel):
    overall_score: float
    by_resource_type: list[ResourceTypeTemporal]


