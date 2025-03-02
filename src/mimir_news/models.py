from pydantic import BaseModel


class PredictionMarket(BaseModel):
    id: str
    question: str
    description: str
    categories: list[str]
    outcome_type: str
    probability: float


class ResearchDetails(BaseModel):
    research: str
    citations: list[str]