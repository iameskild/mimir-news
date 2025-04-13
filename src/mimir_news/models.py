from pydantic import BaseModel


class PredictionMarket(BaseModel):
    id: str
    question: str
    description: str
    categories: list[str]
    outcome_type: str
    probability: float
    creator_name: str
    embed_url: str


class ResearchDetails(BaseModel):
    research: str
    citations: list[str]
