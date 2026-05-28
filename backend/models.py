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


class DuplicatePair(BaseModel):
    resource_id_1: str
    resource_id_2: str
    similarity: float
    text_1: str
    text_2: str


class ResourceTypeDuplicates(BaseModel):
    resource_type: str
    count: int
    avg_score: float
    duplicates: list[DuplicatePair]


class DuplicateDetectionReport(BaseModel):
    overall_score: float
    by_resource_type: list[ResourceTypeDuplicates]


class FullQualityReport(BaseModel):
    completeness: CompletenessReport
    code_coverage: CodeCoverageReport
    temporal: TemporalConsistencyReport
    duplicates: DuplicateDetectionReport
    overall_weighted_score: float
    grade: str




