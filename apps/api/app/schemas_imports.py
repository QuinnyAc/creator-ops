from pydantic import BaseModel


class MetricImportResult(BaseModel):
    imported: int
    updated: int
    skipped: int
    errors: list[str]
