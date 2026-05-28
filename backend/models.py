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
