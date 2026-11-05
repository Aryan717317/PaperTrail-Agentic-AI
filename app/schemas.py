from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    paper_ids: list[str] | None = None


class Source(BaseModel):
    source_id: str
    paper_id: str
    filename: str
    page: int
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    limitations: list[str]
