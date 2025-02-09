"""
This module should ultimate be folded into a task that an agent can perform.
However, I kept running into issues trying to use the Perplexity LLM
with the crewAI framework.

See this issue for more details: https://github.com/crewAIInc/crewAI/issues/1908
"""

import requests
import os
from enum import Enum
import datetime
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from pymanifold import Session


TOP_N_MARKETS = 1


class TimePeriod(Enum):
    WEEK = "week"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"


class PredictionMarket(BaseModel):
    id: str
    question: str
    description: str
    categories: list[str]
    outcome_type: str
    probability: float
    time_period: TimePeriod


def get_market_details(market_id: str) -> PredictionMarket:
    """
    Get the details of a prediction market.
    """
    try:
        market = Session("/market/[marketId]")
        response = market.execute(url_params={"marketId": market_id})
    except Exception as e:
        raise Exception(f"An error occurred while getting the market details: {e}")

    return PredictionMarket(
        id=market_id,
        question=response["question"],
        description=response["textDescription"],
        categories=response["groupSlugs"],
        outcome_type=response["outcomeType"],
        probability=response["probability"],
        time_period=TimePeriod.MONTH,
    )


def get_prediction_market_inputs() -> list[PredictionMarket]:
    """
    Preprocess the prediction markets data.
    """
    try:
        search_markets = Session("/search-markets")
        params = {
            "sort": "24-hour-vol",
            "token": "MANA",
            "filter": "closing-month",
        }
        response = search_markets.execute(params=params)
    except Exception as e:
        raise Exception(
            f"An error occurred while searching for prediction markets: {e}"
        )

    df = pd.DataFrame(response)

    # filter to binary outcomes (for now)
    df = df[df.outcomeType == "BINARY"]

    # handle datetimes outside the acceptable range
    df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms", errors="coerce")

    df["createdTime"] = pd.to_datetime(df["createdTime"], unit="ms").dt.strftime(
        "%Y-%m-%d-%H:%M"
    )
    df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms").dt.strftime(
        "%Y-%m-%d-%H:%M"
    )

    # get the top markets by volume in the last 24 hours
    top_markets = df.sort_values(by="volume24Hours", ascending=False).head(
        TOP_N_MARKETS
    )

    return [get_market_details(market_id) for market_id in top_markets["id"]]


def call_perplexity_api(input: PredictionMarket) -> str:
    """
    Call the perplexity API.
    """
    url = "https://api.perplexity.ai/chat/completions"
    model = "sonar-reasoning-pro"
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise Exception("PERPLEXITY_API_KEY is not set")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    role = """
    You're a seasoned prediction markets researcher with a knack for uncovering the latest developments and trends in high-volume markets. 
    Known for your ability to find the most relevant information and present it in a clear and concise manner, 
    you excel at identifying key insights that can inform trading strategies and market predictions.
    """

    prompt = f"""
    Conduct thorough research on a particular prediction market question.
    The question is `{input.question}` and falls into the following categories: `{input.categories}`.
    And the description is: `{input.description}`
    """

    payload = {
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": prompt},
        ],
        "model": model,
        "frequency_penalty": 1,
        "max_tokens": None,
        "presence_penalty": 0,  # incompatible with `frequency_penalty`
        "response_format": None,
        "return_images": False,
        "return_related_questions": False,
        "search_domain_filter": None,
        "search_recency_filter": input.time_period.value,
        "stream": False,
        "temperature": 0.2,
        "top_p": 0.5,  # use either top_k or top_p, not both
        "top_k": None,  # use either top_k or top_p, not both
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(
                f"An error occurred while calling the perplexity API: {response.json()}"
            )
        return response.json()
    except Exception as e:
        raise Exception(f"An error occurred while calling the perplexity API: {e}")


def save_response(response: dict, input: PredictionMarket):
    """
    Save the response to a file in markdown format.
    """
    # Extract message content and citations
    message = response['choices'][0]['message']['content']
    citations = response.get('citations', [])
    
    # Format markdown content
    markdown_content = f"""# Research: {input.question}

{message}

## Sources
"""
    # Add numbered citations
    for i, citation in enumerate(citations, 1):
        markdown_content += f"{i}. {citation}\n"

    # Create directory and save file
    path = (
        Path("responses")
        / datetime.datetime.now().strftime("%Y-%m-%d")
        / f"{input.id}.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding='utf-8') as f:
        f.write(markdown_content)


# if __name__ == "__main__":
#     inputs = get_prediction_market_inputs()
#     for input in inputs:
#         response = call_perplexity_api(input)
#         save_response(response, input)